from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.26D"
LEGACY_FIRST_OPENED_TIME_S = 510.0
LEGACY_FIRST_SINK_DELAY_S = 30.0


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


def _first_non_empty(rows: list[dict[str, str]], fields: list[str]) -> str:
    for field in fields:
        for row in rows:
            value = row.get(field, "").strip()
            if value:
                return value
    return ""


def _legacy_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "opened")
    sink = _first_flag_row(rows, "sink_positive")
    opening_time = (
        _float(opening.get("time_s"))
        if opening is not None
        else LEGACY_FIRST_OPENED_TIME_S
    )
    sink_time = _float(sink.get("time_s")) if sink is not None else None
    if sink_time is None and opening_time is not None:
        sink_time = opening_time + LEGACY_FIRST_SINK_DELAY_S
    return {
        "opening_time_s": opening_time,
        "sink_time_s": sink_time,
        "max_pressure_Pa": _max(rows, "pw_Pa"),
    }


def _modern_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "fracture_started_this_step")
    if opening is None:
        opening = _first_flag_row(rows, "fracture_initiated")
    sink = _first_positive_sink_row(rows)
    opening_time = None if opening is None else _float(opening.get("time_s"))
    sink_time = None if sink is None else _float(sink.get("time_s"))
    consumption_status = _first_non_empty(
        rows,
        [
            "apbsalt1d_consumption_status",
            "sigma_theta_sampling_consumption_status",
            "apbsalt1d_geometry_status",
            "sigma_theta_mapping_status",
        ],
    )
    mapping_status = _first_non_empty(
        rows,
        [
            "sigma_theta_mapping_status",
            "sigma_theta_sampling_mapping_status",
            "apbsalt1d_sampling_mapping_status",
        ],
    )
    sample_radius_values = _values(
        rows, "sigma_theta_sample_radius_m"
    ) or _values(rows, "wall_stress_r_m")
    return {
        "opening_time_s": opening_time,
        "sink_time_s": sink_time,
        "sink_delay_s": (
            None if opening_time is None or sink_time is None else sink_time - opening_time
        ),
        "max_pressure_Pa": _max(rows, "wellbore_pressure_Pa"),
        "apbsalt1d_consumption_status": consumption_status or "UNKNOWN",
        "sampling_mapping_status": mapping_status or "UNKNOWN",
        "sigma_theta_sample_radius_m": (
            sample_radius_values[0] if sample_radius_values else None
        ),
        "has_spatial_sampling_fields": any(
            field in rows[0]
            for field in {
                "sigma_theta_sample_radius_m",
                "sigma_theta_sample_index",
                "wall_stress_r_m",
                "wall_stress_gp_id",
            }
        ),
    }


def classify(metrics: dict[str, Any]) -> str:
    status = str(metrics.get("apbsalt1d_consumption_status", ""))
    mapping = str(metrics.get("sampling_mapping_status", ""))
    if "BLOCKED" in status or "BLOCKED" in mapping:
        return "APBSALT1D_SAMPLING_BRIDGE_BLOCKED"
    if (
        status in {"APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED", "UNKNOWN", ""}
        or mapping == "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
        or not metrics.get("has_spatial_sampling_fields", False)
    ):
        return "APBSALT1D_SAMPLING_BRIDGE_METADATA_ONLY"
    if (
        metrics.get("modern_opening_time_s") is None
        or metrics.get("opening_time_error_s") is None
        or metrics.get("relative_error_max_pressure") is None
    ):
        return "APBSALT1D_SAMPLING_BRIDGE_INCONCLUSIVE"
    opening_error = abs(float(metrics["opening_time_error_s"]))
    if opening_error <= 60.0:
        return "APBSALT1D_SAMPLING_BRIDGE_EFFECTIVE"
    if opening_error < 150.0:
        return "APBSALT1D_SAMPLING_BRIDGE_PARTIAL"
    return "APBSALT1D_SAMPLING_BRIDGE_NO_CHANGE"


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
        "legacy_sink_delay_s": legacy_sink_delay,
        "modern_sink_delay_s": modern["sink_delay_s"],
        "max_pressure_legacy_Pa": legacy["max_pressure_Pa"],
        "max_pressure_modern_Pa": modern["max_pressure_Pa"],
        "relative_error_max_pressure": _relative_error(
            legacy["max_pressure_Pa"], modern["max_pressure_Pa"]
        ),
        "apbsalt1d_consumption_status": modern["apbsalt1d_consumption_status"],
        "sampling_mapping_status": modern["sampling_mapping_status"],
        "sigma_theta_sample_radius_m": modern["sigma_theta_sample_radius_m"],
        "has_spatial_sampling_fields": modern["has_spatial_sampling_fields"],
    }
    classification = classify(metrics)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_row = {"phase": PHASE, "classification": classification, **metrics}
    with (output_dir / "phase10_26d_summary.csv").open(
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
        "sampling_bridge": {
            "mode": "legacy_elem0_sig_2_0",
            "metadata_consumed": classification
            not in {
                "APBSALT1D_SAMPLING_BRIDGE_METADATA_ONLY",
                "APBSALT1D_SAMPLING_BRIDGE_BLOCKED",
            },
            "has_spatial_sampling_fields": modern["has_spatial_sampling_fields"],
            "mapping_status": modern["sampling_mapping_status"],
            "sample_radius_m": modern["sigma_theta_sample_radius_m"],
        },
        "metrics": metrics,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "Time-series sigmaTheta has no spatial samples for legacy elem0/sig(2,0) resampling.",
            "Metadata-only must not be interpreted as APBSalt1D-equivalent stress calculation.",
            "Default LOT/PKN behavior remains unchanged.",
        ],
    }
    (output_dir / "phase10_26d_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Phase 10.26D BUZ67D APBSalt1D sigma-theta sampling bridge diagnostic."
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
