from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.24B"
LEGACY_FIRST_OPENED_TIME_S = 510.0
LEGACY_FIRST_SINK_POSITIVE_TIME_S = 540.0
LEGACY_PRESSURE_AT_OPENING_PA = 66769500.0


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


def _flag(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() in {"1", "true", "yes"}


def _values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [value for row in rows if (value := _float(row.get(field))) is not None]


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _last_value(rows: list[dict[str, str]], field: str) -> float | None:
    for row in reversed(rows):
        value = _float(row.get(field))
        if value is not None:
            return value
    return None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


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


def _legacy_first_opened(rows: list[dict[str, str]]) -> dict[str, str] | None:
    return _first_flag_row(rows, "opened")


def _legacy_first_sink(rows: list[dict[str, str]]) -> dict[str, str] | None:
    return _first_flag_row(rows, "sink_positive")


def _modern_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "fracture_started_this_step")
    if opening is None:
        opening = _first_flag_row(rows, "fracture_initiated")
    sink = _first_positive_sink_row(rows)
    opening_time = None if opening is None else _float(opening.get("time_s"))
    sink_time = None if sink is None else _float(sink.get("time_s"))
    opening_pressure = None
    if opening is not None:
        opening_pressure = _float(opening.get("fracture_initiation_pressure_Pa"))
        if opening_pressure is None or opening_pressure == 0.0:
            opening_pressure = _float(opening.get("wellbore_pressure_Pa"))
    return {
        "fracture_initiation_time_s": opening_time,
        "first_sink_positive_time_s": sink_time,
        "sink_delay_s": None
        if opening_time is None or sink_time is None
        else sink_time - opening_time,
        "pressure_at_opening_Pa": opening_pressure,
        "max_pressure_Pa": _max(rows, "wellbore_pressure_Pa"),
        "final_pressure_Pa": _last_value(rows, "wellbore_pressure_Pa"),
    }


def _legacy_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _legacy_first_opened(rows)
    sink = _legacy_first_sink(rows)
    opening_time = None if opening is None else _float(opening.get("time_s"))
    sink_time = None if sink is None else _float(sink.get("time_s"))
    opening_pressure = None if opening is None else _float(opening.get("pw_Pa"))
    return {
        "first_opened_time_s": opening_time or LEGACY_FIRST_OPENED_TIME_S,
        "first_sink_positive_time_s": sink_time or LEGACY_FIRST_SINK_POSITIVE_TIME_S,
        "pressure_at_opening_Pa": opening_pressure or LEGACY_PRESSURE_AT_OPENING_PA,
        "max_pressure_Pa": _max(rows, "pw_Pa"),
        "final_pressure_Pa": _last_value(rows, "pw_Pa"),
    }


def _classify(metrics: dict[str, Any]) -> str:
    rel = metrics["relative_error_max_pressure"]
    opening_time = metrics["modern_fracture_initiation_time_s"]
    sink_delay = metrics["modern_sink_delay_s"]
    pressure_ok = rel is not None and abs(rel) <= 0.10
    opening_ok = (
        opening_time is not None
        and abs(opening_time - LEGACY_FIRST_OPENED_TIME_S) <= 60.0
    )
    sink_ok = sink_delay is not None and abs(sink_delay - 30.0) <= 1.0e-9
    if pressure_ok and opening_ok and sink_ok:
        return "SIGMA_THETA_TIMESERIES_EFFECTIVE"
    if pressure_ok and not opening_ok:
        return "SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED"
    if opening_ok and not pressure_ok:
        return "SIGMA_THETA_TIMESERIES_OPENING_OK_PRESSURE_SHIFTED"
    if rel is None or opening_time is None or sink_delay is None:
        return "SIGMA_THETA_TIMESERIES_INCONCLUSIVE"
    return "SIGMA_THETA_TIMESERIES_NO_IMPROVEMENT"


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    legacy = _legacy_metrics(legacy_rows)
    modern = _modern_metrics(modern_rows)
    metrics: dict[str, Any] = {
        "legacy_first_opened_time_s": legacy["first_opened_time_s"],
        "legacy_first_sink_positive_time_s": legacy["first_sink_positive_time_s"],
        "modern_fracture_initiation_time_s": modern["fracture_initiation_time_s"],
        "modern_first_sink_positive_time_s": modern["first_sink_positive_time_s"],
        "modern_sink_delay_s": modern["sink_delay_s"],
        "max_pressure_legacy_Pa": legacy["max_pressure_Pa"],
        "max_pressure_modern_Pa": modern["max_pressure_Pa"],
        "relative_error_max_pressure": _relative_error(
            legacy["max_pressure_Pa"], modern["max_pressure_Pa"]
        ),
        "pressure_at_opening_legacy_Pa": legacy["pressure_at_opening_Pa"],
        "pressure_at_opening_modern_Pa": modern["pressure_at_opening_Pa"],
        "final_pressure_legacy_Pa": legacy["final_pressure_Pa"],
        "final_pressure_modern_Pa": modern["final_pressure_Pa"],
    }
    classification = _classify(metrics)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_row = {"phase": PHASE, "classification": classification, **metrics}
    with (output_dir / "phase10_24b_summary.csv").open(
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
        "configuration": {
            "criterion": "sigma_theta_time_series",
            "interpolation": "linear",
            "out_of_range": "clamp",
            "pressure_source": "wellbore_pressure_trial_Pa",
        },
        "metrics": metrics,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "sigma_theta_time_series is an opt-in LOT diagnostic provider.",
            "The Phase 10.24B diagnostic case uses a minimal legacy-derived series, not full salt runtime stress.",
            "pkn_direct and default runtime behavior remain unchanged.",
        ],
    }
    (output_dir / "phase10_24b_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.24B BUZ67D sigma-theta time-series diagnostic."
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
