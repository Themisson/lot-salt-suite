#!/usr/bin/env python3
"""Verify the Phase 10.30B versioned BUZ-67D sensitivity matrix run."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


REQUIRED_SCENARIOS = {
    "cgeom_060_next_step",
    "cgeom_065_next_step",
    "cgeom_070_next_step",
    "cgeom_075_next_step",
    "cgeom_080_next_step",
    "cgeom_085_next_step",
    "cgeom_090_next_step",
    "cgeom_100_next_step",
    "cgeom_125_next_step",
    "cgeom_100_same_step",
}

ESSENTIAL_COLUMNS = {
    "scenario_id",
    "case",
    "timeseries_csv",
    "max_pressure_Pa",
    "fracture_initiation_time_s",
    "first_sink_positive_time_s",
    "sink_delay_s",
    "final_pressure_Pa",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = set(reader.fieldnames or [])
    missing = ESSENTIAL_COLUMNS - fieldnames
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
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


def has_failed_action(metadata: dict) -> bool:
    for action in metadata.get("actions", []):
        status = str(action.get("status", "")).lower()
        if status in {"failed", "error"}:
            return True
    return False


def verify(summary_path: Path, metadata_path: Path) -> dict:
    rows = read_csv(summary_path)
    metadata = read_metadata(metadata_path)
    scenario_ids = {row["scenario_id"] for row in rows}
    missing_scenarios = sorted(REQUIRED_SCENARIOS - scenario_ids)
    extra_scenarios = sorted(scenario_ids - REQUIRED_SCENARIOS)
    row_count_matches_metadata = len(rows) == int(metadata.get("scenario_count", -1))
    required_present = not missing_scenarios
    baseline_present = "cgeom_100_next_step" in scenario_ids
    cgeom_075_present = "cgeom_075_next_step" in scenario_ids
    same_step_present = "cgeom_100_same_step" in scenario_ids
    failed_action = has_failed_action(metadata)

    if failed_action:
        classification = "VERSIONED_SENSITIVITY_RUN_FAILED"
    elif required_present and row_count_matches_metadata and baseline_present and cgeom_075_present and same_step_present:
        classification = "VERSIONED_SENSITIVITY_RUN_OK"
    elif scenario_ids:
        classification = "VERSIONED_SENSITIVITY_RUN_PARTIAL"
    else:
        classification = "VERSIONED_SENSITIVITY_RUN_INCONCLUSIVE"

    return {
        "classification": classification,
        "matrix_id": metadata["matrix_id"],
        "scenario_count_metadata": metadata.get("scenario_count"),
        "scenario_count_summary": len(rows),
        "required_scenarios_present": required_present,
        "baseline_present": baseline_present,
        "cgeom_075_present": cgeom_075_present,
        "same_step_present": same_step_present,
        "missing_scenarios": missing_scenarios,
        "extra_scenarios": extra_scenarios,
        "row_count_matches_metadata": row_count_matches_metadata,
        "failed_action": failed_action,
    }


def write_markdown(path: Path, result: dict) -> None:
    lines = [
        "# Phase 10.30B sensitivity run verification",
        "",
        f"- classification: `{result['classification']}`",
        f"- matrix_id: `{result['matrix_id']}`",
        f"- scenario_count_metadata: `{result['scenario_count_metadata']}`",
        f"- scenario_count_summary: `{result['scenario_count_summary']}`",
        f"- required_scenarios_present: `{str(result['required_scenarios_present']).lower()}`",
        f"- baseline_present: `{str(result['baseline_present']).lower()}`",
        f"- cgeom_075_present: `{str(result['cgeom_075_present']).lower()}`",
        f"- same_step_present: `{str(result['same_step_present']).lower()}`",
        f"- row_count_matches_metadata: `{str(result['row_count_matches_metadata']).lower()}`",
        f"- failed_action: `{str(result['failed_action']).lower()}`",
    ]
    if result["missing_scenarios"]:
        lines.append(f"- missing_scenarios: `{', '.join(result['missing_scenarios'])}`")
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
    result = verify(args.summary, args.metadata)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, result)
    print(f"MATRIX_ID={result['matrix_id']}")
    print(f"CLASSIFICATION={result['classification']}")
    print(f"SCENARIO_COUNT={result['scenario_count_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
