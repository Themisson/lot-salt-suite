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


def _float(row: dict[str, str], field: str) -> float | None:
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


def _next_after(rows: list[dict[str, str]], time_s: float, predicate) -> dict[str, str] | None:
    for row in rows:
        row_time = _float(row, "time_s")
        if row_time is not None and row_time > time_s and predicate(row):
            return row
    return None


def _classify_sink(first_open: dict[str, str] | None,
                   first_positive_sink: dict[str, str] | None) -> str:
    if first_open is None:
        return "LEGACY_SINK_UNKNOWN"
    if first_positive_sink is None:
        return "LEGACY_SINK_UNKNOWN"
    open_time = _float(first_open, "time_s")
    sink_time = _float(first_positive_sink, "time_s")
    if open_time is None or sink_time is None:
        return "LEGACY_SINK_UNKNOWN"
    if math.isclose(open_time, sink_time, abs_tol=1.0e-9):
        return "LEGACY_SINK_SAME_STEP"
    if sink_time > open_time:
        return "LEGACY_SINK_NEXT_STEP"
    return "LEGACY_SINK_GRADUAL"


def analyze_trace(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    if not rows:
        return {
            "phase": "10.18F",
            "status": "BLOCKED_EMPTY_LEGACY_TRACE",
            "legacy_sink_classification": "LEGACY_SINK_UNKNOWN",
            "caveats": ["legacy trace has no rows"],
        }

    first_open = _first(rows, lambda row: _truthy(row, "opened"))
    first_transition = _first(
        rows,
        lambda row: _truthy(row, "opened")
        and not _truthy(row, "opened_before_step"),
    )
    if first_transition is None:
        first_transition = first_open

    first_positive_sink = _first(
        rows,
        lambda row: (_float(row, "fracture_volume_increment_m3") or 0.0) > 0.0,
    )

    first_after_open_sink = None
    if first_open is not None and _float(first_open, "time_s") is not None:
        first_after_open_sink = _next_after(
            rows,
            _float(first_open, "time_s") or 0.0,
            lambda row: (_float(row, "fracture_volume_increment_m3") or 0.0) > 0.0,
        )

    sink_row = first_after_open_sink or first_positive_sink
    classification = _classify_sink(first_open, sink_row)

    def compact(row: dict[str, str] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        fields = [
            "step",
            "time_min",
            "time_s",
            "pw_Pa",
            "sigmaTheta_Pa",
            "margin_Pa",
            "opened",
            "opened_before_step",
            "opened_after_step",
            "fracture_volume_m3",
            "fracture_volume_increment_m3",
            "leakoff_volume_m3",
            "leakoff_volume_increment_m3",
            "dV_effective_m3",
            "dP_step_Pa",
            "layer",
            "annular_index",
        ]
        result: dict[str, Any] = {}
        for field in fields:
            parsed = _float(row, field)
            result[field] = parsed if parsed is not None else row.get(field)
        return result

    first_open_time = _float(first_open, "time_s") if first_open is not None else None
    surrounding = []
    if first_open_time is not None:
        for row in rows:
            time_s = _float(row, "time_s")
            if time_s is not None and abs(time_s - first_open_time) <= 30.0:
                if row.get("layer") in {first_open.get("layer"), "16"}:
                    surrounding.append(compact(row))
            if len(surrounding) >= 20:
                break

    return {
        "phase": "10.18F",
        "status": "LEGACY_FRACTURE_TRACE_ANALYZED",
        "source_trace": str(path),
        "n_rows": len(rows),
        "first_open": compact(first_open),
        "first_open_transition": compact(first_transition),
        "first_positive_sink": compact(first_positive_sink),
        "first_positive_sink_after_open": compact(first_after_open_sink),
        "legacy_sink_classification": classification,
        "fracture_volume_zero_before_opening": all(
            (_float(row, "fracture_volume_m3") or 0.0) == 0.0
            for row in rows
            if first_open_time is not None
            and (_float(row, "time_s") or math.inf) < first_open_time
        ),
        "sink_enters_same_step": classification == "LEGACY_SINK_SAME_STEP",
        "sink_enters_next_step": classification == "LEGACY_SINK_NEXT_STEP",
        "surrounding_open_rows": surrounding,
        "caveats": [
            "Trace is instrumented diagnostic output, not committable legacy code.",
            "Rows include nonlinear iteration samples, not only accepted time-step states.",
            "fracture_volume_m3 records the legacy dV_leakoff field used as fracture/leakoff sink proxy.",
        ],
    }


def _write_summary_csv(path: Path, summary: dict[str, Any]) -> None:
    fields = [
        "phase",
        "status",
        "legacy_sink_classification",
        "first_open_time_s",
        "first_open_pw_Pa",
        "first_open_sigmaTheta_Pa",
        "first_positive_sink_time_s",
        "first_positive_sink_increment_m3",
    ]
    first_open = summary.get("first_open") or {}
    first_sink = summary.get("first_positive_sink_after_open") or summary.get(
        "first_positive_sink"
    ) or {}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "phase": summary.get("phase"),
                "status": summary.get("status"),
                "legacy_sink_classification": summary.get("legacy_sink_classification"),
                "first_open_time_s": first_open.get("time_s"),
                "first_open_pw_Pa": first_open.get("pw_Pa"),
                "first_open_sigmaTheta_Pa": first_open.get("sigmaTheta_Pa"),
                "first_positive_sink_time_s": first_sink.get("time_s"),
                "first_positive_sink_increment_m3": first_sink.get(
                    "fracture_volume_increment_m3"
                ),
            }
        )


def run(args: argparse.Namespace) -> dict[str, Any]:
    summary = analyze_trace(Path(args.legacy_trace))
    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_summary_csv(output_csv, summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Phase 10.18F instrumented legacy fracture trace."
    )
    parser.add_argument("--legacy-trace", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser


def main() -> int:
    summary = run(build_parser().parse_args())
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("status") != "BLOCKED_EMPTY_LEGACY_TRACE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
