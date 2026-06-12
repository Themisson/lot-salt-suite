#!/usr/bin/env python3
"""Decide the Phase 11.10X runtime integration gate for fracture wiring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10X"
STATUS = "RUNTIME_INTEGRATION_GATE_SPECIFIED"
SELECTED_OPTION = "DIAGNOSTIC_PRE_RUNNER_OPT_IN"
NEXT_PHASE = "PHASE11_10Y_IMPLEMENT_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE"


def build_decision() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "integration_gate_status": STATUS,
        "selected_integration_option": SELECTED_OPTION,
        "implementation_allowed_next": True,
        "runtime_physical_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "requires_feature_flag": True,
        "requires_diagnostic_output_isolation": True,
        "recommended_next_phase": NEXT_PHASE,
        "runtime_audit": {
            "current_lot_pkn_entrypoint": "apps/lot-sim.cpp::run_case",
            "current_runner_call": "lss::lot::run_pkn_case(data)",
            "pkn_runner_result": "lss::lot::PknRun",
            "case_data_fracture_model_storage": "lss::core::CaseData::lot.fracture_model",
            "safe_integration_point": "after parse/validate and before run_pkn_case",
            "physical_result_change_allowed": False,
        },
        "options": [
            {
                "id": "A",
                "name": "DIAGNOSTIC_PRE_RUNNER_OPT_IN",
                "risk": "LOW",
                "recommended": True,
                "notes": "Evaluates wiring after parse and before PknRunner, writing isolated diagnostics only.",
            },
            {
                "id": "B",
                "name": "INSIDE_PKN_RUNNER",
                "risk": "HIGH",
                "recommended": False,
                "notes": "Could alter time-series behavior and fracture initiation chronology.",
            },
            {
                "id": "C",
                "name": "EXTERNAL_DIAGNOSTIC_TOOL_ONLY",
                "risk": "LOW",
                "recommended": False,
                "notes": "Safe fallback, but does not test runtime adjacency.",
            },
            {
                "id": "D",
                "name": "FULL_RUNTIME_DISPATCH",
                "risk": "BLOCKED",
                "recommended": False,
                "notes": "Physical dispatch remains out of scope.",
            },
        ],
        "required_gates": [
            "explicit feature flag enabled",
            "diagnostic mode only",
            "PKN remains default",
            "PENNY_SHAPED remains diagnostic_only",
            "runtime physical dispatch remains disabled",
            "BUZ29-PENNY remains blocked",
            "PKN regressions pass",
            "diagnostic outputs isolated from physical outputs",
        ],
        "classifications": [
            "PHASE11_10X_RUNTIME_INTEGRATION_GATE_SPECIFIED",
            STATUS,
            "DIAGNOSTIC_PRE_RUNNER_OPT_IN_SELECTED",
            "RUNTIME_PHYSICAL_DISPATCH_NOT_ALLOWED",
            "BUZ29_EXECUTION_BLOCKED",
            "PKN_BEHAVIOR_CHANGE_NOT_ALLOWED",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 11.10X runtime integration gate",
        "",
        f"- phase: `{payload['phase']}`",
        f"- integration_gate_status: `{payload['integration_gate_status']}`",
        f"- selected_integration_option: `{payload['selected_integration_option']}`",
        f"- implementation_allowed_next: `{str(payload['implementation_allowed_next']).lower()}`",
        f"- runtime_physical_dispatch_allowed_next: `{str(payload['runtime_physical_dispatch_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(payload['buz29_execution_allowed_next']).lower()}`",
        f"- pkn_behavior_change_allowed: `{str(payload['pkn_behavior_change_allowed']).lower()}`",
        f"- requires_feature_flag: `{str(payload['requires_feature_flag']).lower()}`",
        f"- requires_diagnostic_output_isolation: `{str(payload['requires_diagnostic_output_isolation']).lower()}`",
        f"- recommended_next_phase: `{payload['recommended_next_phase']}`",
        "",
        "## Required gates",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["required_gates"])
    lines.extend(["", "## Classifications", ""])
    lines.extend(f"- `{item}`" for item in payload["classifications"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.10X runtime integration gate for fracture wiring."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_decision()
    if args.output_json:
        write_json(args.output_json, payload)
    if args.output_md:
        write_markdown(args.output_md, payload)

    print(f"PHASE={payload['phase']}")
    print(f"INTEGRATION_GATE_STATUS={payload['integration_gate_status']}")
    print(f"SELECTED_INTEGRATION_OPTION={payload['selected_integration_option']}")
    print(f"IMPLEMENTATION_ALLOWED_NEXT={str(payload['implementation_allowed_next']).lower()}")
    print(
        "RUNTIME_PHYSICAL_DISPATCH_ALLOWED_NEXT="
        f"{str(payload['runtime_physical_dispatch_allowed_next']).lower()}"
    )
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(payload['buz29_execution_allowed_next']).lower()}")
    print(f"PKN_BEHAVIOR_CHANGE_ALLOWED={str(payload['pkn_behavior_change_allowed']).lower()}")
    print(f"REQUIRES_FEATURE_FLAG={str(payload['requires_feature_flag']).lower()}")
    print(
        "REQUIRES_DIAGNOSTIC_OUTPUT_ISOLATION="
        f"{str(payload['requires_diagnostic_output_isolation']).lower()}"
    )
    print(f"RECOMMENDED_NEXT_PHASE={payload['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
