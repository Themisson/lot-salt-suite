#!/usr/bin/env python3
"""Analyze Phase 11.5A extended BUZ-67D C_geom sensitivity results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Iterable


CLASS_OK = "CGEOM_EXTENDED_SENSITIVITY_ANALYZED"
CLASS_PARTIAL = "CGEOM_EXTENDED_SENSITIVITY_PARTIAL"
CLASS_INCONCLUSIVE = "CGEOM_EXTENDED_SENSITIVITY_INCONCLUSIVE"


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
    missing = []
    for column in ["fracture_volume_max_m3", "leakoff_volume_max_m3"]:
        if column not in row:
            missing.append(column)
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


def abs_error(value: float | None, target: float | None) -> float:
    if value is None or target is None:
        return math.inf
    return abs(value - target)


def normalized_error(value: float | None, target: float | None) -> float:
    if value is None or target is None:
        return math.inf
    return abs(value - target) / max(abs(target), 1.0)


def select_best(scenarios: list[dict], key: str) -> dict | None:
    candidates = [item for item in scenarios if item.get(key) is not None and math.isfinite(item[key])]
    return min(candidates, key=lambda item: item[key]) if candidates else None


def analyze(summary_path: Path, metadata_path: Path) -> dict:
    rows = read_summary(summary_path)
    metadata = read_metadata(metadata_path)
    caveats = [
        "best_by_* is diagnostic ranking only; not calibration.",
        "C_geom factors are diagnostic variations of the modern-refined baseline.",
    ]
    scenarios = [scenario_from_row(row, caveats) for row in rows]
    target_opening_s = 510.0
    target_max_pressure_Pa = 69035836.1743195
    for scenario in scenarios:
        scenario["opening_time_error_s"] = (
            None
            if math.isinf(abs_error(scenario["opening_time_s"], target_opening_s))
            else abs_error(scenario["opening_time_s"], target_opening_s)
        )
        scenario["max_pressure_error_Pa"] = (
            None
            if math.isinf(abs_error(scenario["max_pressure_Pa"], target_max_pressure_Pa))
            else abs_error(scenario["max_pressure_Pa"], target_max_pressure_Pa)
        )
        score = normalized_error(scenario["opening_time_s"], target_opening_s) + normalized_error(
            scenario["max_pressure_Pa"], target_max_pressure_Pa
        )
        scenario["combined_score"] = None if math.isinf(score) else score

    best_opening = select_best(scenarios, "opening_time_error_s")
    best_pressure = select_best(scenarios, "max_pressure_error_Pa")
    best_combined = select_best(scenarios, "combined_score")
    classification = CLASS_OK if len(scenarios) >= 2 else CLASS_PARTIAL
    if not scenarios:
        classification = CLASS_INCONCLUSIVE
    return {
        "classification": classification,
        "matrix_id": metadata.get("matrix_id"),
        "scenario_count": len(scenarios),
        "target_opening_time_s": target_opening_s,
        "target_max_pressure_Pa": target_max_pressure_Pa,
        "best_by_opening_time": best_opening["scenario_id"] if best_opening else None,
        "best_by_max_pressure": best_pressure["scenario_id"] if best_pressure else None,
        "best_by_combined_score": best_combined["scenario_id"] if best_combined else None,
        "scenarios": scenarios,
        "caveats": sorted(set(caveats)),
    }


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Phase 11.5A C_geom extended sensitivity analysis",
        "",
        f"- classification: `{report['classification']}`",
        f"- matrix_id: `{report['matrix_id']}`",
        f"- scenario_count: `{report['scenario_count']}`",
        f"- best_by_opening_time: `{report['best_by_opening_time']}`",
        f"- best_by_max_pressure: `{report['best_by_max_pressure']}`",
        f"- best_by_combined_score: `{report['best_by_combined_score']}`",
        "",
        "| Scenario | C_geom | Opening (s) | Sink delay (s) | Max pressure (Pa) | Score |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for scenario in report["scenarios"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{scenario['scenario_id']}`",
                    str(scenario["cgeom_factor"]),
                    str(scenario["opening_time_s"]),
                    str(scenario["sink_delay_s"]),
                    str(scenario["max_pressure_Pa"]),
                    str(scenario["combined_score"]),
                ]
            )
            + " |"
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
    print(f"BEST_BY_COMBINED_SCORE={report['best_by_combined_score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
