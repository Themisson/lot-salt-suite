#!/usr/bin/env python3
"""Verify Phase 11.3A BUZ-67D parametric matrix v2 sensitivity execution."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable


EXPECTED_DOCUMENTED = {
    "cgeom_075_next_step": {"opening": 510.0, "sink_delay": 30.0},
    "cgeom_100_next_step": {"opening": 660.0, "sink_delay": 30.0},
    "cgeom_125_next_step": {"opening": None, "sink_delay": None},
    "cgeom_100_same_step": {"opening": 660.0, "sink_delay": 0.0},
}


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def read_summary(path: Path) -> list[dict]:
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


def close_enough(value: float | None, expected: float | None, tolerance: float = 1.0) -> bool:
    if expected is None:
        return value is None
    return value is not None and abs(value - expected) <= tolerance


def scenario_map(rows: list[dict]) -> dict[str, dict]:
    return {row["scenario_id"]: row for row in rows if row.get("scenario_id")}


def action_failed(action: dict) -> bool:
    status = str(action.get("status", "")).lower()
    return status in {"failed", "error"} or bool(action.get("failed"))


def verify(summary_path: Path, metadata_path: Path) -> dict:
    rows = read_summary(summary_path)
    metadata = read_metadata(metadata_path)
    by_id = scenario_map(rows)
    issues: list[str] = []

    matrix_id = metadata.get("matrix_id")
    schema_version = metadata.get("schema_version")
    actions = metadata.get("actions") or []
    failed_actions = [action.get("scenario_id", "<unknown>") for action in actions if action_failed(action)]
    materialized_paths = [row.get("materialized_case_path") for row in rows if row.get("materialized_case_path")]
    action_materialized_paths = [action.get("materialized_case_path") for action in actions if action.get("materialized_case_path")]

    if not matrix_id:
        issues.append("missing matrix_id")
    if schema_version != 2:
        issues.append("schema_version is not 2")
    if failed_actions:
        issues.append(f"failed scenarios: {failed_actions}")
    if not materialized_paths and not action_materialized_paths:
        issues.append("missing materialized_case_path")
    for required in ["cgeom_075_next_step", "cgeom_100_next_step"]:
        if required not in by_id:
            issues.append(f"missing required scenario: {required}")
    if "cgeom_100_same_step" not in by_id:
        issues.append("missing same_step scenario")

    comparisons = []
    compatible_count = 0
    checked_count = 0
    for scenario_id, expected in EXPECTED_DOCUMENTED.items():
        if scenario_id not in by_id:
            continue
        row = by_id[scenario_id]
        opening = as_float(row.get("fracture_initiation_time_s"))
        sink_delay = as_float(row.get("sink_delay_s"))
        opening_ok = close_enough(opening, expected["opening"])
        sink_ok = close_enough(sink_delay, expected["sink_delay"])
        checked_count += 1
        if opening_ok and sink_ok:
            compatible_count += 1
        comparisons.append(
            {
                "scenario_id": scenario_id,
                "opening_time_s": opening,
                "expected_opening_time_s": expected["opening"],
                "opening_compatible": opening_ok,
                "sink_delay_s": sink_delay,
                "expected_sink_delay_s": expected["sink_delay"],
                "sink_delay_compatible": sink_ok,
                "source": "DOCUMENTED_PHASE_SUMMARY",
            }
        )

    if issues:
        classification = "PHASE11_3A_V2_SENSITIVITY_RUN_FAILED" if failed_actions else "PHASE11_3A_V2_SENSITIVITY_RUN_PARTIAL"
        v1_v2 = "V2_PARTIALLY_REPRODUCES_V1"
    elif checked_count and compatible_count == checked_count:
        classification = "PHASE11_3A_V2_SENSITIVITY_RUN_OK"
        v1_v2 = "V2_REPRODUCES_V1_DIAGNOSTICS"
    elif compatible_count > 0:
        classification = "PHASE11_3A_V2_SENSITIVITY_RUN_PARTIAL"
        v1_v2 = "V2_PARTIALLY_REPRODUCES_V1"
    else:
        classification = "PHASE11_3A_V2_SENSITIVITY_RUN_INCONCLUSIVE"
        v1_v2 = "V2_V1_COMPARISON_INCONCLUSIVE"

    return {
        "phase": "11.3A",
        "classification": classification,
        "v1_v2_classification": v1_v2,
        "matrix_id": matrix_id,
        "schema_version": schema_version,
        "scenario_count": len(rows),
        "materialized_case_paths_present": bool(materialized_paths or action_materialized_paths),
        "required_scenarios_present": all(item in by_id for item in ["cgeom_075_next_step", "cgeom_100_next_step"]),
        "same_step_present": "cgeom_100_same_step" in by_id,
        "failed_actions": failed_actions,
        "issues": issues,
        "comparisons": comparisons,
        "comparison_source": "DOCUMENTED_PHASE_SUMMARY",
        "caveats": [
            "Diagnostic execution only; not automatic calibration.",
            "Matrix v2 materialized cases are local artifacts in results/ and must not be versioned.",
            "V1 comparison uses documented phase summary when local v1 results are not supplied.",
        ],
    }


def write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# Phase 11.3A v2 sensitivity run verification",
        "",
        f"- classification: `{payload['classification']}`",
        f"- v1_v2_classification: `{payload['v1_v2_classification']}`",
        f"- matrix_id: `{payload['matrix_id']}`",
        f"- schema_version: `{payload['schema_version']}`",
        f"- scenario_count: `{payload['scenario_count']}`",
        f"- materialized_case_paths_present: `{payload['materialized_case_paths_present']}`",
        "",
        "## V1 vs V2 comparison",
        "",
        "| Scenario | Opening v2 (s) | Opening expected (s) | Sink delay v2 (s) | Sink expected (s) | Compatible |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in payload["comparisons"]:
        compatible = item["opening_compatible"] and item["sink_delay_compatible"]
        lines.append(
            f"| `{item['scenario_id']}` | {item['opening_time_s']} | {item['expected_opening_time_s']} | "
            f"{item['sink_delay_s']} | {item['expected_sink_delay_s']} | `{compatible}` |"
        )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in payload["caveats"])
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- {item}" for item in payload["issues"])
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
    payload = verify(args.summary, args.metadata)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, payload)
    print(f"MATRIX_ID={payload['matrix_id']}")
    print(f"CLASSIFICATION={payload['classification']}")
    print(f"V1_V2_CLASSIFICATION={payload['v1_v2_classification']}")
    return 0 if payload["classification"] != "PHASE11_3A_V2_SENSITIVITY_RUN_FAILED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
