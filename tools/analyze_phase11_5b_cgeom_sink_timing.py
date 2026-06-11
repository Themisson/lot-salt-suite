#!/usr/bin/env python3
"""Analyze Phase 11.5B BUZ-67D C_geom x sink_timing sensitivity results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable


CLASS_OK = "CGEOM_SINK_TIMING_MATRIX_ANALYZED"
CLASS_PARTIAL = "CGEOM_SINK_TIMING_MATRIX_PARTIAL"
CLASS_INCONCLUSIVE = "CGEOM_SINK_TIMING_MATRIX_INCONCLUSIVE"


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def cgeom_factor(scenario_id: str) -> float | None:
    match = re.search(r"cgeom_(\d{3})", scenario_id)
    if not match:
        return None
    return int(match.group(1)) / 100.0


def sink_timing(scenario_id: str) -> str | None:
    if scenario_id.endswith("_next_step"):
        return "next_step"
    if scenario_id.endswith("_same_step"):
        return "same_step"
    return None


def read_summary(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no rows")
    return rows


def read_metadata(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_from_row(row: dict[str, str], caveats: list[str]) -> dict:
    scenario_id = row.get("scenario_id", "")
    missing = [column for column in ["fracture_volume_max_m3", "leakoff_volume_max_m3"] if column not in row]
    if missing:
        caveats.append(f"{scenario_id}: optional columns missing: {', '.join(missing)}")
    return {
        "scenario_id": scenario_id,
        "cgeom_factor": cgeom_factor(scenario_id),
        "sink_timing": sink_timing(scenario_id),
        "opening_time_s": as_float(row.get("fracture_initiation_time_s")),
        "sink_delay_s": as_float(row.get("sink_delay_s")),
        "max_pressure_Pa": as_float(row.get("max_pressure_Pa")),
        "final_pressure_Pa": as_float(row.get("final_pressure_Pa")),
        "fracture_volume_max_m3": as_float(row.get("fracture_volume_max_m3")),
        "leakoff_volume_max_m3": as_float(row.get("leakoff_volume_max_m3")),
        "status": "completed" if row.get("timeseries_csv") else "unknown",
    }


def delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def compare_same_cgeom(scenarios: list[dict]) -> list[dict]:
    grouped: dict[float, dict[str, dict]] = defaultdict(dict)
    for scenario in scenarios:
        factor = scenario.get("cgeom_factor")
        timing = scenario.get("sink_timing")
        if factor is not None and timing:
            grouped[factor][timing] = scenario
    comparisons = []
    for factor, by_timing in sorted(grouped.items()):
        same = by_timing.get("same_step")
        nxt = by_timing.get("next_step")
        if not same or not nxt:
            continue
        comparisons.append(
            {
                "cgeom_factor": factor,
                "opening_time_delta_next_minus_same_s": delta(nxt["opening_time_s"], same["opening_time_s"]),
                "sink_delay_delta_next_minus_same_s": delta(nxt["sink_delay_s"], same["sink_delay_s"]),
                "max_pressure_delta_next_minus_same_Pa": delta(nxt["max_pressure_Pa"], same["max_pressure_Pa"]),
                "final_pressure_delta_next_minus_same_Pa": delta(nxt["final_pressure_Pa"], same["final_pressure_Pa"]),
            }
        )
    return comparisons


def compare_same_sink_timing(scenarios: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for scenario in scenarios:
        timing = scenario.get("sink_timing")
        if timing:
            grouped[timing].append(scenario)
    comparisons = []
    for timing, items in sorted(grouped.items()):
        ordered = sorted(
            [item for item in items if item.get("cgeom_factor") is not None],
            key=lambda item: item["cgeom_factor"],
        )
        for previous, current in zip(ordered, ordered[1:]):
            comparisons.append(
                {
                    "sink_timing": timing,
                    "from_cgeom_factor": previous["cgeom_factor"],
                    "to_cgeom_factor": current["cgeom_factor"],
                    "opening_time_delta_s": delta(current["opening_time_s"], previous["opening_time_s"]),
                    "max_pressure_delta_Pa": delta(current["max_pressure_Pa"], previous["max_pressure_Pa"]),
                    "final_pressure_delta_Pa": delta(current["final_pressure_Pa"], previous["final_pressure_Pa"]),
                }
            )
    return comparisons


def finite_values(rows: list[dict], key: str) -> list[float]:
    return [row[key] for row in rows if row.get(key) is not None and math.isfinite(row[key])]


def analyze(summary_path: Path, metadata_path: Path) -> dict:
    rows = read_summary(summary_path)
    metadata = read_metadata(metadata_path)
    caveats = [
        "All rankings and effects are diagnostic only; not physical calibration.",
        "The matrix separates C_geom and sink_timing effects without changing solver behavior.",
    ]
    scenarios = [scenario_from_row(row, caveats) for row in rows]
    by_cgeom = compare_same_cgeom(scenarios)
    by_sink = compare_same_sink_timing(scenarios)
    sink_delay_deltas = finite_values(by_cgeom, "sink_delay_delta_next_minus_same_s")
    opening_deltas = finite_values(by_cgeom, "opening_time_delta_next_minus_same_s")
    max_pressure_deltas = finite_values(by_cgeom, "max_pressure_delta_next_minus_same_Pa")
    classification = CLASS_OK if by_cgeom and by_sink else CLASS_PARTIAL
    if not scenarios:
        classification = CLASS_INCONCLUSIVE
    expected_next_step_delay_s = 30.0
    sink_delay_reproduced = any(abs(value - expected_next_step_delay_s) < 1.0e-9 for value in sink_delay_deltas)
    return {
        "classification": classification,
        "matrix_id": metadata.get("matrix_id"),
        "scenario_count": len(scenarios),
        "same_cgeom_comparisons": by_cgeom,
        "same_sink_timing_comparisons": by_sink,
        "mean_opening_delta_next_minus_same_s": mean(opening_deltas),
        "mean_max_pressure_delta_next_minus_same_Pa": mean(max_pressure_deltas),
        "mean_sink_delay_delta_next_minus_same_s": mean(sink_delay_deltas),
        "sink_delay_reproduced_where_expected": sink_delay_reproduced,
        "interaction_observation": (
            "C_geom and sink_timing effects are both represented in the matrix."
            if by_cgeom and by_sink
            else "Insufficient paired scenarios to assess interaction."
        ),
        "scenarios": scenarios,
        "caveats": sorted(set(caveats)),
    }


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Phase 11.5B C_geom x sink_timing sensitivity analysis",
        "",
        f"- classification: `{report['classification']}`",
        f"- matrix_id: `{report['matrix_id']}`",
        f"- scenario_count: `{report['scenario_count']}`",
        f"- mean_opening_delta_next_minus_same_s: `{report['mean_opening_delta_next_minus_same_s']}`",
        f"- mean_max_pressure_delta_next_minus_same_Pa: `{report['mean_max_pressure_delta_next_minus_same_Pa']}`",
        f"- mean_sink_delay_delta_next_minus_same_s: `{report['mean_sink_delay_delta_next_minus_same_s']}`",
        f"- sink_delay_reproduced_where_expected: `{report['sink_delay_reproduced_where_expected']}`",
        "",
        "## Same C_geom, Varying Sink Timing",
        "",
        "| C_geom | Opening delta next-same (s) | Sink delay delta (s) | Max pressure delta (Pa) |",
        "|---:|---:|---:|---:|",
    ]
    for item in report["same_cgeom_comparisons"]:
        lines.append(
            f"| {item['cgeom_factor']} | {item['opening_time_delta_next_minus_same_s']} | "
            f"{item['sink_delay_delta_next_minus_same_s']} | {item['max_pressure_delta_next_minus_same_Pa']} |"
        )
    lines.extend(
        [
            "",
            "## Same Sink Timing, Varying C_geom",
            "",
            "| Sink timing | From C_geom | To C_geom | Opening delta (s) | Max pressure delta (Pa) |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for item in report["same_sink_timing_comparisons"]:
        lines.append(
            f"| `{item['sink_timing']}` | {item['from_cgeom_factor']} | {item['to_cgeom_factor']} | "
            f"{item['opening_time_delta_s']} | {item['max_pressure_delta_Pa']} |"
        )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in report["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = analyze(args.summary, args.metadata)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, report)
    print(f"CLASSIFICATION={report['classification']}")
    print(f"SCENARIO_COUNT={report['scenario_count']}")
    print(f"MEAN_SINK_DELAY_DELTA={report['mean_sink_delay_delta_next_minus_same_s']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
