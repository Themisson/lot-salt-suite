from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.23A"
LEGACY_FIRST_OPENED_TIME_S = 510.0
LEGACY_FIRST_SINK_POSITIVE_TIME_S = 540.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [value for row in rows if (value := _float(row.get(field))) is not None]


def _flag(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() in {"1", "true", "yes"}


def _first_flag_time(rows: list[dict[str, str]], field: str) -> float | None:
    for row in rows:
        if _flag(row, field):
            return _float(row.get("time_s"))
    return None


def _first_positive_sink_time(rows: list[dict[str, str]]) -> float | None:
    for row in rows:
        fracture = _float(row.get("fracture_sink_applied_m3"))
        leakoff = _float(row.get("leakoff_sink_applied_m3"))
        if fracture is None:
            fracture = _float(row.get("balance_fracture_volume_increment_m3"))
        if leakoff is None:
            leakoff = _float(row.get("balance_leakoff_volume_increment_m3"))
        if (fracture or 0.0) + (leakoff or 0.0) > 0.0:
            return _float(row.get("time_s"))
    return None


def _first_opened_time_from_legacy(rows: list[dict[str, str]]) -> float | None:
    for row in rows:
        opened = row.get("opened", "").strip().lower()
        if opened in {"1", "true", "yes"}:
            return _float(row.get("time_s"))
    sigma_values = _values(rows, "sigmaTheta_Pa")
    if not sigma_values:
        return None
    for row in rows:
        pressure = _float(row.get("pw_Pa"))
        sigma = _float(row.get("sigmaTheta_Pa"))
        if pressure is not None and sigma is not None and pressure > sigma:
            return _float(row.get("time_s"))
    return None


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


def _route_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opened_time = _first_flag_time(rows, "fracture_started_this_step")
    if opened_time is None:
        opened_time = _first_flag_time(rows, "fracture_initiated")
    sink_time = _first_positive_sink_time(rows)
    return {
        "fracture_initiation_time_s": opened_time,
        "first_sink_positive_time_s": sink_time,
        "sink_delay_s": None
        if opened_time is None or sink_time is None
        else sink_time - opened_time,
        "max_pressure_Pa": _max(rows, "wellbore_pressure_Pa"),
    }


def _classify(metrics: dict[str, Any]) -> str:
    same_delay = metrics["same_step"]["sink_delay_s"]
    next_delay = metrics["next_step"]["sink_delay_s"]
    if next_delay == 30.0 and same_delay == 0.0:
        return "NEXT_STEP_SINK_EFFECTIVE"
    if next_delay is not None and same_delay is not None and next_delay > same_delay:
        return "NEXT_STEP_SINK_PARTIAL"
    return "NEXT_STEP_SINK_NOT_EFFECTIVE"


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    same_rows = _read_csv(Path(args.modern_same_step_csv))
    next_rows = _read_csv(Path(args.modern_next_step_csv))

    legacy_opened = _first_opened_time_from_legacy(legacy_rows)
    caveats = [
        "Diagnostic only; not physical validation.",
        "Legacy LOT_Tese output does not export fracture/leakoff sink flags directly.",
        "Next-step timing is opt-in and does not change pkn_direct or same_step defaults.",
    ]
    if legacy_opened is None:
        legacy_opened = LEGACY_FIRST_OPENED_TIME_S
        caveats.append("Legacy opening time uses audited Phase 10.22C value.")
    legacy_sink = LEGACY_FIRST_SINK_POSITIVE_TIME_S
    if "sink_positive" not in (legacy_rows[0].keys() if legacy_rows else set()):
        caveats.append("Legacy first positive sink time uses audited Phase 10.22C value.")

    legacy_max = _max(legacy_rows, "pw_Pa")
    metrics: dict[str, Any] = {
        "legacy": {
            "first_opened_time_s": legacy_opened,
            "first_sink_positive_time_s": legacy_sink,
            "sink_delay_s": None
            if legacy_opened is None or legacy_sink is None
            else legacy_sink - legacy_opened,
            "max_pressure_Pa": legacy_max,
        },
        "same_step": _route_metrics(same_rows),
        "next_step": _route_metrics(next_rows),
    }
    metrics["same_step"]["relative_error_max_pressure_vs_legacy"] = _relative_error(
        legacy_max, metrics["same_step"]["max_pressure_Pa"]
    )
    metrics["next_step"]["relative_error_max_pressure_vs_legacy"] = _relative_error(
        legacy_max, metrics["next_step"]["max_pressure_Pa"]
    )
    classification = _classify(metrics)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_row = {
        "phase": PHASE,
        "classification": classification,
        "legacy_first_opened_time_s": metrics["legacy"]["first_opened_time_s"],
        "legacy_first_sink_positive_time_s": metrics["legacy"][
            "first_sink_positive_time_s"
        ],
        "legacy_sink_delay_s": metrics["legacy"]["sink_delay_s"],
        "same_step_initiation_time_s": metrics["same_step"][
            "fracture_initiation_time_s"
        ],
        "same_step_first_sink_positive_time_s": metrics["same_step"][
            "first_sink_positive_time_s"
        ],
        "same_step_sink_delay_s": metrics["same_step"]["sink_delay_s"],
        "next_step_initiation_time_s": metrics["next_step"][
            "fracture_initiation_time_s"
        ],
        "next_step_first_sink_positive_time_s": metrics["next_step"][
            "first_sink_positive_time_s"
        ],
        "next_step_sink_delay_s": metrics["next_step"]["sink_delay_s"],
        "legacy_max_pressure_Pa": metrics["legacy"]["max_pressure_Pa"],
        "same_step_max_pressure_Pa": metrics["same_step"]["max_pressure_Pa"],
        "next_step_max_pressure_Pa": metrics["next_step"]["max_pressure_Pa"],
        "same_step_relative_error_max_pressure_vs_legacy": metrics["same_step"][
            "relative_error_max_pressure_vs_legacy"
        ],
        "next_step_relative_error_max_pressure_vs_legacy": metrics["next_step"][
            "relative_error_max_pressure_vs_legacy"
        ],
    }
    with (output_dir / "phase10_23a_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_row))
        writer.writeheader()
        writer.writerow(summary_row)

    metadata = {
        "phase": PHASE,
        "classification": classification,
        "physical_validation": False,
        "runtime_default_changed": False,
        "metrics": metrics,
        "caveats": caveats,
    }
    (output_dir / "phase10_23a_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.23A same-step vs next-step sink timing diagnostics."
    )
    parser.add_argument("--legacy-csv", required=True, type=Path)
    parser.add_argument("--modern-same-step-csv", required=True, type=Path)
    parser.add_argument("--modern-next-step-csv", required=True, type=Path)
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
