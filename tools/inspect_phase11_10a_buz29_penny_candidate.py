#!/usr/bin/env python3
"""Inspect the Phase 11.10A BUZ29 PennyShaped diagnostic candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PHASE = "11.10A"
CASE_ID = "buz29_penny_candidate"
CLASSIFICATION_STARTED = "BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED"
CLASSIFICATION_BLOCKED = "BUZ29_PENNY_DIAGNOSTIC_ROUTE_BLOCKED"
EXPECTED_GATE = "BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A"
NEXT_PHASE = "PHASE11_10B_INSPECT_BUZ29_PENNY_ADAPTER_READY_INPUTS"

AXISYMMETRIC_CAVEAT = "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED"
FUTURE_OUTPUT_REQUIREMENT = "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED"

REQUIRED_CAVEAT_TEXT = [
    "Diagnostic candidate only",
    "Not physically validated",
    "Not legacy equivalent",
]


def load_candidate(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"candidate YAML not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("candidate YAML root must be a mapping")
    return data


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def _is_false(value: Any) -> bool:
    return value is False


def inspect_candidate(path: Path) -> dict[str, Any]:
    data = load_candidate(path)
    case = _section(data, "case")
    source = _section(data, "source")
    track = _section(data, "track")
    evidence = _section(data, "diagnostic_evidence")
    axisymmetric = _section(data, "axisymmetric_interpretation")
    diagnostics = _section(data, "diagnostics")
    adapter = _section(data, "adapter_status")

    blocking_gaps: list[str] = []

    if case.get("status") not in {"diagnostic_candidate", "partial_candidate"}:
        blocking_gaps.append("case.status")
    if case.get("active") is True:
        blocking_gaps.append("case.active")
    caveat = str(case.get("caveat", ""))
    for marker in REQUIRED_CAVEAT_TEXT:
        if marker not in caveat:
            blocking_gaps.append("case.caveat")
            break

    if not source.get("legacy_trace"):
        blocking_gaps.append("source.legacy_trace")
    if track.get("gate") != EXPECTED_GATE:
        blocking_gaps.append("track.gate")

    if evidence.get("pressure_history_status") != "PRESSURE_HISTORY_FOUND_CONSUMABLE":
        blocking_gaps.append("diagnostic_evidence.pressure_history_status")
    if evidence.get("opening_time_status") != "OPENING_TIME_FOUND_CONSUMABLE":
        blocking_gaps.append("diagnostic_evidence.opening_time_status")

    if axisymmetric.get("caveat") != AXISYMMETRIC_CAVEAT:
        blocking_gaps.append("axisymmetric_interpretation.caveat")
    if axisymmetric.get("future_output_requirement") != FUTURE_OUTPUT_REQUIREMENT:
        blocking_gaps.append("axisymmetric_interpretation.future_output_requirement")

    if not _is_false(diagnostics.get("physically_validated")):
        blocking_gaps.append("diagnostics.physically_validated")
    if not _is_false(diagnostics.get("legacy_equivalent")):
        blocking_gaps.append("diagnostics.legacy_equivalent")
    if not _is_false(diagnostics.get("active_simulation_case")):
        blocking_gaps.append("diagnostics.active_simulation_case")

    route_started = not blocking_gaps
    classification = CLASSIFICATION_STARTED if route_started else CLASSIFICATION_BLOCKED

    caveats = [
        "NOT_PHYSICALLY_VALIDATED",
        "NOT_LEGACY_EQUIVALENT",
        "NOT_ACTIVE_SIMULATION_CASE",
        AXISYMMETRIC_CAVEAT,
        FUTURE_OUTPUT_REQUIREMENT,
        "sigmaTheta/pw/margin/opened are not directly exported by the legacy output.",
    ]

    return {
        "phase": PHASE,
        "case": CASE_ID,
        "case_file": str(path),
        "classification": classification,
        "route_started": route_started,
        "physically_validated": False,
        "legacy_equivalent": False,
        "active_simulation_case": False,
        "gate": track.get("gate"),
        "axisymmetric_interpretation": axisymmetric.get("caveat"),
        "future_output_requirement": axisymmetric.get("future_output_requirement"),
        "available_fields": {
            "pressure_history_status": evidence.get("pressure_history_status"),
            "opening_time_status": evidence.get("opening_time_status"),
            "time_points": evidence.get("time_points"),
            "time_min_min": evidence.get("time_min_min"),
            "time_max_min": evidence.get("time_max_min"),
            "opening_time_min": evidence.get("opening_time_min"),
            "available_blocks": evidence.get("available_blocks", []),
        },
        "deferred_items": adapter.get("missing_or_deferred", []),
        "blocking_gaps": blocking_gaps,
        "caveats": caveats,
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10A BUZ29 PennyShaped Candidate Inspection",
        "",
        f"- classification: `{result['classification']}`",
        f"- route_started: `{str(result['route_started']).lower()}`",
        "- physically_validated: `false`",
        "- legacy_equivalent: `false`",
        "- active_simulation_case: `false`",
        f"- gate: `{result['gate']}`",
        "",
        "## Axisymmetric Caveat",
        "",
        f"- `{result['axisymmetric_interpretation']}`",
        f"- `{result['future_output_requirement']}`",
        "",
        "## Available Fields",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in result["available_fields"].items())
    lines.extend(["", "## Deferred Items", ""])
    lines.extend(f"- {item}" for item in result["deferred_items"])
    lines.extend(["", "## Blocking Gaps", ""])
    lines.extend(f"- `{item}`" for item in result["blocking_gaps"] or ["none"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- `{item}`" for item in result["caveats"])
    lines.extend(
        [
            "",
            "## Recommended Next Phase",
            "",
            f"```text\n{result['recommended_next_phase']}\n```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect the Phase 11.10A BUZ29 PennyShaped diagnostic candidate."
    )
    parser.add_argument("--case", required=True, type=Path, help="Candidate YAML path.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = inspect_candidate(args.case)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"CLASSIFICATION={result['classification']}")
    print(f"ROUTE_STARTED={str(result['route_started']).lower()}")
    print("PHYSICALLY_VALIDATED=false")
    print("LEGACY_EQUIVALENT=false")
    print("ACTIVE_SIMULATION_CASE=false")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0 if result["route_started"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
