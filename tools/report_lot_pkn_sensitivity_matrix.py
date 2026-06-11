#!/usr/bin/env python3
"""Generate a reproducible LOT/PKN sensitivity matrix report."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = {
    "scenario_id",
    "case",
    "max_pressure_Pa",
    "fracture_initiation_time_s",
    "first_sink_positive_time_s",
    "sink_delay_s",
    "final_pressure_Pa",
}


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


def read_summary(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            raise ValueError(f"{path} missing required columns: {sorted(missing)}")
        rows = []
        for row in reader:
            rows.append(
                {
                    "scenario_id": row["scenario_id"],
                    "case": row["case"],
                    "cgeom_factor": cgeom_factor(row["scenario_id"]),
                    "max_pressure_Pa": as_float(row.get("max_pressure_Pa")),
                    "fracture_initiation_time_s": as_float(row.get("fracture_initiation_time_s")),
                    "first_sink_positive_time_s": as_float(row.get("first_sink_positive_time_s")),
                    "sink_delay_s": as_float(row.get("sink_delay_s")),
                    "final_pressure_Pa": as_float(row.get("final_pressure_Pa")),
                }
            )
    if not rows:
        raise ValueError(f"{path} has no rows")
    return rows


def read_metadata(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if not metadata.get("matrix_id"):
        raise ValueError("metadata matrix_id is required")
    return metadata


def find_baseline(rows: list[dict], preferred: str = "cgeom_100_next_step") -> dict:
    for row in rows:
        if row["scenario_id"] == preferred:
            return row
    for row in rows:
        if row["cgeom_factor"] == 1.0 and "same_step" not in row["scenario_id"]:
            return row
    return rows[0]


def finite_or_inf(value: float | None) -> float:
    return value if value is not None and math.isfinite(value) else math.inf


def abs_error(value: float | None, target: float | None) -> float:
    if value is None or target is None:
        return math.inf
    return abs(value - target)


def normalized_abs_error(value: float | None, target: float | None) -> float:
    if value is None or target is None:
        return math.inf
    scale = max(abs(target), 1.0)
    return abs(value - target) / scale


def ranked_rows(rows: list[dict], target_opening: float | None, target_pressure: float | None) -> list[dict]:
    ranked = []
    for row in rows:
        opening_error = abs_error(row["fracture_initiation_time_s"], target_opening)
        pressure_error = abs_error(row["max_pressure_Pa"], target_pressure)
        combined_score = normalized_abs_error(row["fracture_initiation_time_s"], target_opening) + normalized_abs_error(
            row["max_pressure_Pa"], target_pressure
        )
        ranked.append(
            {
                **row,
                "opening_time_error_s": None if math.isinf(opening_error) else opening_error,
                "max_pressure_error_Pa": None if math.isinf(pressure_error) else pressure_error,
                "combined_score": None if math.isinf(combined_score) else combined_score,
            }
        )
    return sorted(ranked, key=lambda row: finite_or_inf(row["combined_score"]))


def select_best(rows: list[dict], key: str) -> dict | None:
    candidates = [row for row in rows if row.get(key) is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda row: row[key])


def summarize(
    summary_path: Path,
    metadata_path: Path,
    legacy_opening_time_s: float | None = None,
    legacy_max_pressure_Pa: float | None = None,
) -> dict:
    rows = read_summary(summary_path)
    metadata = read_metadata(metadata_path)
    baseline = find_baseline(rows)
    target_opening = legacy_opening_time_s if legacy_opening_time_s is not None else baseline["fracture_initiation_time_s"]
    target_pressure = legacy_max_pressure_Pa if legacy_max_pressure_Pa is not None else baseline["max_pressure_Pa"]
    source = "LEGACY_TARGETS" if legacy_opening_time_s is not None or legacy_max_pressure_Pa is not None else "BASELINE_RELATIVE"
    ranking = ranked_rows(rows, target_opening, target_pressure)
    best_opening = select_best(ranking, "opening_time_error_s")
    best_pressure = select_best(ranking, "max_pressure_error_Pa")
    best_combined = select_best(ranking, "combined_score")
    return {
        "classification": "SENSITIVITY_REPORT_GENERATED",
        "matrix_id": metadata["matrix_id"],
        "source": source,
        "scenario_count": len(rows),
        "baseline_scenario": baseline["scenario_id"],
        "target_opening_time_s": target_opening,
        "target_max_pressure_Pa": target_pressure,
        "best_factor_by_opening_time": best_opening["cgeom_factor"] if best_opening else None,
        "best_scenario_by_opening_time": best_opening["scenario_id"] if best_opening else None,
        "best_factor_by_max_pressure": best_pressure["cgeom_factor"] if best_pressure else None,
        "best_scenario_by_max_pressure": best_pressure["scenario_id"] if best_pressure else None,
        "best_factor_by_combined_score": best_combined["cgeom_factor"] if best_combined else None,
        "best_scenario_by_combined_score": best_combined["scenario_id"] if best_combined else None,
        "ranking": ranking,
        "caveats": [
            "Diagnostic sensitivity report only; not automatic calibration.",
            "Modern-refined mode is not strict LOT_Tese legacy-equivalence.",
            "Best factors require independent physical criteria before use as calibrated parameters.",
            "results/ outputs are reproducible local artifacts and must not be versioned.",
        ],
    }


def format_number(value: object) -> str:
    if value is None:
        return "not available"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# LOT/PKN sensitivity matrix report",
        "",
        f"- classification: `{report['classification']}`",
        f"- matrix_id: `{report['matrix_id']}`",
        f"- source: `{report['source']}`",
        f"- scenario_count: `{report['scenario_count']}`",
        f"- baseline_scenario: `{report['baseline_scenario']}`",
        f"- best_factor_by_opening_time: `{format_number(report['best_factor_by_opening_time'])}`",
        f"- best_factor_by_max_pressure: `{format_number(report['best_factor_by_max_pressure'])}`",
        f"- best_factor_by_combined_score: `{format_number(report['best_factor_by_combined_score'])}`",
        "",
        "## Ranking",
        "",
        "| Scenario | C_geom factor | Opening time (s) | Max pressure (Pa) | Combined score |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in report["ranking"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['scenario_id']}`",
                    format_number(row["cgeom_factor"]),
                    format_number(row["fracture_initiation_time_s"]),
                    format_number(row["max_pressure_Pa"]),
                    format_number(row["combined_score"]),
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
    parser.add_argument("--legacy-opening-time-s", type=float)
    parser.add_argument("--legacy-max-pressure-Pa", type=float)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = summarize(args.summary, args.metadata, args.legacy_opening_time_s, args.legacy_max_pressure_Pa)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, report)
    print(f"MATRIX_ID={report['matrix_id']}")
    print(f"CLASSIFICATION={report['classification']}")
    print(f"BEST_FACTOR_BY_COMBINED_SCORE={format_number(report['best_factor_by_combined_score'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
