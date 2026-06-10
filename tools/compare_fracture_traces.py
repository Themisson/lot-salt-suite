from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(row: dict[str, str] | None, field: str) -> float | None:
    if row is None:
        return None
    value = row.get(field)
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _truthy(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() in {"1", "true", "yes", "opened"}


def _first(rows: list[dict[str, str]], predicate) -> dict[str, str] | None:
    for row in rows:
        if predicate(row):
            return row
    return None


def _first_positive(rows: list[dict[str, str]], field: str) -> dict[str, str] | None:
    return _first(rows, lambda row: (_float(row, field) or 0.0) > 0.0)


def _nearest(rows: list[dict[str, str]], time_s: float) -> dict[str, str] | None:
    candidates = [(abs((_float(row, "time_s") or 0.0) - time_s), row) for row in rows]
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


def _classify_root(legacy_open: dict[str, str] | None,
                   modern_open: dict[str, str] | None,
                   legacy_sink: dict[str, str] | None,
                   modern_sink: dict[str, str] | None) -> tuple[str, str]:
    legacy_time = _float(legacy_open, "time_s")
    modern_time = _float(modern_open, "time_s")
    legacy_sink_time = _float(legacy_sink, "time_s")
    modern_sink_time = _float(modern_sink, "time_s")
    if legacy_time is None or modern_time is None:
        return "TRACE_INCONCLUSIVE", "missing first-open event in one trace"
    if modern_time < legacy_time:
        detail = (
            "modern static threshold opens before the legacy sigma-theta criterion; "
            "this is a criterion mismatch, not a confirmed local C++ sink bug"
        )
        return "OTHER", detail
    if legacy_sink_time is not None and modern_sink_time is not None:
        if legacy_sink_time > legacy_time and math.isclose(modern_sink_time, modern_time):
            return (
                "LEGACY_NEXT_STEP_SINK_BUT_MODERN_SAME_STEP_SINK",
                "legacy first positive sink is delayed, while modern sink is same-step",
            )
    return "TRACE_INCONCLUSIVE", "no local root cause matched the trace evidence"


def compare_traces(legacy_trace: Path, modern_trace: Path) -> dict[str, Any]:
    legacy_rows = _read_csv(legacy_trace)
    modern_rows = _read_csv(modern_trace)
    legacy_open = _first(legacy_rows, lambda row: _truthy(row, "opened"))
    modern_open = _first(
        modern_rows,
        lambda row: row.get("fracture_initiated_after", "").lower() == "true"
        or row.get("fracture_initiated_after") == "1",
    )
    legacy_sink = _first_positive(legacy_rows, "fracture_volume_increment_m3")
    modern_sink = _first_positive(modern_rows, "fracture_volume_increment_m3")
    root, detail = _classify_root(legacy_open, modern_open, legacy_sink, modern_sink)
    legacy_time = _float(legacy_open, "time_s")
    modern_near_legacy = _nearest(modern_rows, legacy_time) if legacy_time is not None else None
    first_divergent_time = None
    if legacy_time is not None and _float(modern_open, "time_s") is not None:
        first_divergent_time = min(legacy_time, _float(modern_open, "time_s") or legacy_time)

    return {
        "phase": "10.18F",
        "status": "TRACE_COMPARISON_COMPLETE",
        "physical_validation": False,
        "root_cause_classification": root,
        "root_cause_detail": detail,
        "correction_allowed": root not in {"TRACE_INCONCLUSIVE", "OTHER"},
        "legacy_first_open": {
            "time_s": legacy_time,
            "pw_Pa": _float(legacy_open, "pw_Pa"),
            "sigmaTheta_Pa": _float(legacy_open, "sigmaTheta_Pa"),
            "margin_Pa": _float(legacy_open, "margin_Pa"),
            "fracture_increment_m3": _float(legacy_open, "fracture_volume_increment_m3"),
        },
        "modern_first_open": {
            "time_s": _float(modern_open, "time_s"),
            "criterion_pressure_Pa": _float(modern_open, "criterion_pressure_Pa"),
            "threshold_Pa": _float(modern_open, "breakdown_threshold_Pa"),
            "fracture_increment_m3": _float(modern_open, "fracture_volume_increment_m3"),
            "wellbore_pressure_after_Pa": _float(modern_open, "wellbore_pressure_after_Pa"),
        },
        "legacy_first_positive_sink": {
            "time_s": _float(legacy_sink, "time_s"),
            "fracture_increment_m3": _float(legacy_sink, "fracture_volume_increment_m3"),
        },
        "modern_first_positive_sink": {
            "time_s": _float(modern_sink, "time_s"),
            "fracture_increment_m3": _float(modern_sink, "fracture_volume_increment_m3"),
        },
        "modern_at_legacy_open_time": {
            "time_s": _float(modern_near_legacy, "time_s"),
            "criterion_pressure_Pa": _float(modern_near_legacy, "criterion_pressure_Pa"),
            "wellbore_pressure_after_Pa": _float(
                modern_near_legacy, "wellbore_pressure_after_Pa"
            ),
            "fracture_volume_m3": _float(modern_near_legacy, "fracture_volume_m3"),
        },
        "first_divergent_time_s": first_divergent_time,
        "caveats": [
            "Legacy trace rows include nonlinear iteration samples.",
            "Modern trace is reconstructed from ResultWriter CSV, not a runtime debug hook.",
            "No sigma-theta runtime criterion was implemented in this phase.",
        ],
    }


def _write_outputs(output_dir: Path, metadata: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "trace_comparison_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    fields = [
        "metric",
        "legacy",
        "modern",
        "note",
    ]
    rows = [
        {
            "metric": "first_open_time_s",
            "legacy": metadata["legacy_first_open"]["time_s"],
            "modern": metadata["modern_first_open"]["time_s"],
            "note": metadata["root_cause_classification"],
        },
        {
            "metric": "first_sink_time_s",
            "legacy": metadata["legacy_first_positive_sink"]["time_s"],
            "modern": metadata["modern_first_positive_sink"]["time_s"],
            "note": metadata["root_cause_detail"],
        },
        {
            "metric": "first_open_fracture_increment_m3",
            "legacy": metadata["legacy_first_open"]["fracture_increment_m3"],
            "modern": metadata["modern_first_open"]["fracture_increment_m3"],
            "note": "diagnostic only",
        },
    ]
    with (output_dir / "trace_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> dict[str, Any]:
    metadata = compare_traces(Path(args.legacy_trace), Path(args.modern_trace))
    _write_outputs(Path(args.output_dir), metadata)
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.18F legacy and modern fracture traces."
    )
    parser.add_argument("--legacy-trace", required=True)
    parser.add_argument("--modern-trace", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> int:
    metadata = run(build_parser().parse_args())
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
