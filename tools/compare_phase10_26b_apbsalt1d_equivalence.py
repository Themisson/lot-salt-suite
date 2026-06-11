from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.26B"
LEGACY_FIRST_OPENED_TIME_S = 510.0
LEGACY_FIRST_SINK_POSITIVE_TIME_S = 540.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    if not rows:
        raise ValueError(f"CSV sem linhas de dados: {path}")
    return rows


def _require_columns(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    available = set(rows[0])
    missing = sorted(required - available)
    if missing:
        raise ValueError(
            f"{label} CSV sem colunas obrigatorias: {', '.join(missing)}"
        )


def _float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _flag(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() in {"1", "true", "yes"}


def _values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [value for row in rows if (value := _float(row.get(field))) is not None]


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _first_flag_row(rows: list[dict[str, str]], field: str) -> dict[str, str] | None:
    for row in rows:
        if _flag(row, field):
            return row
    return None


def _first_positive_sink_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        fracture = _float(row.get("fracture_sink_applied_m3"))
        leakoff = _float(row.get("leakoff_sink_applied_m3"))
        if fracture is None:
            fracture = _float(row.get("balance_fracture_volume_increment_m3"))
        if leakoff is None:
            leakoff = _float(row.get("balance_leakoff_volume_increment_m3"))
        if (fracture or 0.0) + (leakoff or 0.0) > 0.0:
            return row
    return None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


def _legacy_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "opened")
    sink = _first_flag_row(rows, "sink_positive")
    return {
        "opening_time_s": (
            _float(opening.get("time_s"))
            if opening is not None
            else LEGACY_FIRST_OPENED_TIME_S
        ),
        "sink_time_s": (
            _float(sink.get("time_s"))
            if sink is not None
            else LEGACY_FIRST_SINK_POSITIVE_TIME_S
        ),
        "max_pressure_Pa": _max(rows, "pw_Pa"),
    }


def _modern_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "fracture_started_this_step")
    if opening is None:
        opening = _first_flag_row(rows, "fracture_initiated")
    sink = _first_positive_sink_row(rows)
    opening_time = None if opening is None else _float(opening.get("time_s"))
    sink_time = None if sink is None else _float(sink.get("time_s"))
    statuses = {
        row.get("sigma_theta_mapping_status", "").strip()
        for row in rows
        if row.get("sigma_theta_mapping_status", "").strip()
    }
    return {
        "opening_time_s": opening_time,
        "sink_time_s": sink_time,
        "sink_delay_s": (
            None if opening_time is None or sink_time is None else sink_time - opening_time
        ),
        "max_pressure_Pa": _max(rows, "wellbore_pressure_Pa"),
        "sigmaTheta_source_status": (
            "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
            if "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED" in statuses
            else (";".join(sorted(statuses)) if statuses else "UNKNOWN")
        ),
        "apbsalt1d_geometry_status": (
            "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
            if "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED" in statuses
            else "APBSALT1D_GEOMETRY_STATUS_NOT_REPORTED"
        ),
    }


def classify(metrics: dict[str, Any]) -> str:
    if (
        metrics["sigmaTheta_source_status"]
        == "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
        or metrics["apbsalt1d_geometry_status"]
        == "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
    ):
        return "APBSALT1D_EQUIVALENCE_METADATA_ONLY"
    if (
        metrics["modern_opening_time_s"] is None
        or metrics["modern_sink_time_s"] is None
        or metrics["relative_error_max_pressure"] is None
    ):
        return "APBSALT1D_EQUIVALENCE_INCONCLUSIVE"
    opening_error = metrics["opening_time_error_s"]
    if opening_error is None:
        return "APBSALT1D_EQUIVALENCE_INCONCLUSIVE"
    if abs(opening_error) <= 60.0:
        return "APBSALT1D_EQUIVALENCE_EFFECTIVE"
    if abs(opening_error) < 150.0:
        return "APBSALT1D_EQUIVALENCE_PARTIAL"
    return "APBSALT1D_EQUIVALENCE_NO_CHANGE"


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    _require_columns(legacy_rows, {"time_s", "pw_Pa"}, "legacy")
    _require_columns(modern_rows, {"time_s", "wellbore_pressure_Pa"}, "modern")
    legacy = _legacy_metrics(legacy_rows)
    modern = _modern_metrics(modern_rows)
    legacy_sink_delay = (
        None
        if legacy["opening_time_s"] is None or legacy["sink_time_s"] is None
        else legacy["sink_time_s"] - legacy["opening_time_s"]
    )
    metrics: dict[str, Any] = {
        "legacy_opening_time_s": legacy["opening_time_s"],
        "modern_opening_time_s": modern["opening_time_s"],
        "opening_time_error_s": (
            None
            if legacy["opening_time_s"] is None or modern["opening_time_s"] is None
            else modern["opening_time_s"] - legacy["opening_time_s"]
        ),
        "legacy_sink_time_s": legacy["sink_time_s"],
        "modern_sink_time_s": modern["sink_time_s"],
        "legacy_sink_delay_s": legacy_sink_delay,
        "modern_sink_delay_s": modern["sink_delay_s"],
        "sink_delay_s": modern["sink_delay_s"],
        "max_pressure_legacy_Pa": legacy["max_pressure_Pa"],
        "max_pressure_modern_Pa": modern["max_pressure_Pa"],
        "relative_error_max_pressure": _relative_error(
            legacy["max_pressure_Pa"], modern["max_pressure_Pa"]
        ),
        "sigmaTheta_source_status": modern["sigmaTheta_source_status"],
        "apbsalt1d_geometry_status": modern["apbsalt1d_geometry_status"],
    }
    classification = classify(metrics)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_row = {"phase": PHASE, "classification": classification, **metrics}
    with (output_dir / "phase10_26b_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_row))
        writer.writeheader()
        writer.writerow(summary_row)

    metadata = {
        "phase": PHASE,
        "classification": classification,
        "runtime_default_changed": False,
        "physical_validation": False,
        "configuration": {
            "mode": "apbsalt1d_legacy_equivalent",
            "outer_radius_m": 8.0,
            "radial_elements": 15,
            "ratio": 10.0,
            "integration_order": 3,
            "sampling": "legacy_elem0_sig_2_0",
            "consumption_status": metrics["apbsalt1d_geometry_status"],
        },
        "metrics": metrics,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "APBSalt1D geometry is declared as opt-in metadata in this phase.",
            "No runtime salt wall-stress provider consumes the geometry yet.",
            "Default LOT/PKN behavior remains unchanged.",
        ],
    }
    (output_dir / "phase10_26b_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Phase 10.26B BUZ67D APBSalt1D sigma-theta equivalence diagnostic."
        )
    )
    parser.add_argument("--legacy-csv", required=True, type=Path)
    parser.add_argument("--modern-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    metadata = run_comparison(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": metadata["phase"],
                "classification": metadata["classification"],
                "metrics": metadata["metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
