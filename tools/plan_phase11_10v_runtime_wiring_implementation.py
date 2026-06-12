#!/usr/bin/env python3
"""Plan Phase 11.10V fracture gate runtime wiring implementation.

This tool is intentionally documentary.  It does not execute runtime wiring,
does not call LOT/PKN solvers, and does not authorize BUZ29-PENNY execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10V"
PLAN_STATUS = "RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED"
NEXT_PHASE = "PHASE11_10W_IMPLEMENT_FRACTURE_GATE_RUNTIME_WIRING"

REQUIRED_SCENARIOS = [
    "missing_model_defaults_pkn_not_reached",
    "explicit_pkn_initiated_dispatch_eligible",
    "explicit_penny_initiated_diagnostic_eligible",
    "sigmatheta_guard_blocks_dispatch",
    "pressure_sigmatheta_criterion_blocks_dispatch",
    "unsupported_kgd_model_blocked",
    "explicit_empty_model_blocked",
]

PROPOSED_FILES = [
    "include/lot/FractureGateRuntimeWiring.hpp",
    "src/lot/FractureGateRuntimeWiring.cpp",
    "tests/cpp/test_fracture_gate_runtime_wiring.cpp",
]

PROTECTED_COMPONENTS = [
    "PknModel",
    "PknRunner",
    "CaseParser",
    "ResultWriter",
    "CLI",
    "volumetric_balance",
    "pkn_direct",
    "legacy/",
    "legance/",
    "external/saltcreep/",
]


def build_plan() -> dict[str, Any]:
    """Return the deterministic Phase 11.10V implementation plan."""

    fixture_to_cpp_test_mapping = [
        {
            "fixture_id": "missing_model_defaults_pkn_not_reached",
            "future_cpp_test": "defaults missing model to PKN and does not dispatch when criterion not reached",
            "expected_gate_status": "FRACTURE_GATE_READY_NOT_REACHED",
            "expected_dispatch_status": "FRACTURE_DISPATCH_NOT_EXECUTED",
        },
        {
            "fixture_id": "explicit_pkn_initiated_dispatch_eligible",
            "future_cpp_test": "marks explicit PKN as dispatch eligible when fracture gate is reached",
            "expected_gate_status": "FRACTURE_GATE_REACHED",
            "expected_dispatch_status": "FRACTURE_DISPATCH_PKN_ELIGIBLE",
        },
        {
            "fixture_id": "explicit_penny_initiated_diagnostic_eligible",
            "future_cpp_test": "marks explicit PENNY_SHAPED as diagnostic eligible only when gate is reached",
            "expected_gate_status": "FRACTURE_GATE_REACHED",
            "expected_dispatch_status": "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE",
        },
        {
            "fixture_id": "sigmatheta_guard_blocks_dispatch",
            "future_cpp_test": "blocks dispatch when SigmaThetaInitialStateGuard is not ready",
            "expected_gate_status": "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE",
            "expected_dispatch_status": "FRACTURE_DISPATCH_NOT_ALLOWED",
        },
        {
            "fixture_id": "pressure_sigmatheta_criterion_blocks_dispatch",
            "future_cpp_test": "blocks dispatch when PressureSigmaThetaFractureCriterionGuard is not ready",
            "expected_gate_status": "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION",
            "expected_dispatch_status": "FRACTURE_DISPATCH_NOT_ALLOWED",
        },
        {
            "fixture_id": "unsupported_kgd_model_blocked",
            "future_cpp_test": "does not evaluate gate when fracture model selector rejects KGD",
            "expected_gate_status": "FRACTURE_GATE_NOT_EVALUATED",
            "expected_dispatch_status": "FRACTURE_DISPATCH_NOT_ALLOWED",
        },
        {
            "fixture_id": "explicit_empty_model_blocked",
            "future_cpp_test": "does not evaluate gate when fracture model selector rejects explicit empty model",
            "expected_gate_status": "FRACTURE_GATE_NOT_EVALUATED",
            "expected_dispatch_status": "FRACTURE_DISPATCH_NOT_ALLOWED",
        },
    ]

    return {
        "phase": PHASE,
        "source": "DOCUMENTED_PHASE_SUMMARY_AND_11_10U_FIXTURES",
        "plan_status": PLAN_STATUS,
        "implementation_allowed_next": True,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "runtime_wiring_implemented": False,
        "runtime_dispatch_executed": False,
        "available_components": [
            "FractureModelSelector",
            "SigmaThetaInitialStateGuard",
            "PressureSigmaThetaFractureCriterionGuard",
            "PennyShapedDiagnosticAdapter",
            "PennyShapedDiagnosticWriter",
        ],
        "proposed_files": PROPOSED_FILES,
        "future_api": {
            "namespace": "lss::lot",
            "enums": [
                "FractureGateStatus",
                "FractureDispatchStatus",
            ],
            "structs": [
                "FractureGateRuntimeInput",
                "FractureGateRuntimeResult",
            ],
            "function": "evaluate_fracture_gate_runtime(const FractureGateRuntimeInput& input)",
        },
        "implementation_rules": [
            "Run FractureModelSelector first.",
            "If selection fails, do not evaluate the fracture gate.",
            "Run SigmaThetaInitialStateGuard before pressure x sigma_theta criterion.",
            "If sigmaTheta guard fails, return BlockedSigmaThetaInitialState and NotAllowed.",
            "Run PressureSigmaThetaFractureCriterionGuard after the initial state guard.",
            "If criterion guard blocks, return BlockedPressureSigmaThetaCriterion and NotAllowed.",
            "If criterion is ready but fracture is not reached, return ReadyNotReached and NotExecuted.",
            "If criterion is reached, dispatch status depends on selected model.",
            "PKN may become PknEligible but the implementation must not change existing lot-pkn behavior.",
            "PENNY_SHAPED may become PennyDiagnosticEligible but BUZ29-PENNY execution remains blocked.",
            "Do not call PknModel or PennyShapedDiagnosticAdapter in the first wiring without a later gate.",
        ],
        "required_test_scenarios": REQUIRED_SCENARIOS,
        "fixture_to_cpp_test_mapping": fixture_to_cpp_test_mapping,
        "protected_components": PROTECTED_COMPONENTS,
        "classifications": [
            "PHASE11_10V_RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED",
            PLAN_STATUS,
            "RUNTIME_WIRING_IMPLEMENTATION_ALLOWED_NEXT",
            "RUNTIME_EXECUTION_STILL_BLOCKED",
            "BUZ29_EXECUTION_STILL_BLOCKED",
            "PKN_BEHAVIOR_CHANGE_NOT_ALLOWED",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 11.10V runtime wiring implementation plan",
        "",
        "## Decision",
        "",
        f"- phase: `{payload['phase']}`",
        f"- plan_status: `{payload['plan_status']}`",
        f"- recommended_next_phase: `{payload['recommended_next_phase']}`",
        f"- implementation_allowed_next: `{str(payload['implementation_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(payload['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(payload['buz29_execution_allowed_next']).lower()}`",
        f"- pkn_behavior_change_allowed: `{str(payload['pkn_behavior_change_allowed']).lower()}`",
        "",
        "## Proposed future files",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["proposed_files"])
    lines.extend(["", "## Required test scenarios", ""])
    lines.extend(f"- `{item}`" for item in payload["required_test_scenarios"])
    lines.extend(["", "## Implementation rules", ""])
    lines.extend(f"- {item}" for item in payload["implementation_rules"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the Phase 11.10V fracture gate runtime wiring implementation plan."
    )
    parser.add_argument("--output-json", type=Path, help="Optional JSON output path.")
    parser.add_argument("--output-md", type=Path, help="Optional Markdown output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_plan()

    if args.output_json:
        write_json(args.output_json, payload)
    if args.output_md:
        write_markdown(args.output_md, payload)

    print(f"PHASE={payload['phase']}")
    print(f"PLAN_STATUS={payload['plan_status']}")
    print(f"IMPLEMENTATION_ALLOWED_NEXT={str(payload['implementation_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(payload['runtime_execution_allowed_next']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(payload['buz29_execution_allowed_next']).lower()}")
    print(f"PKN_BEHAVIOR_CHANGE_ALLOWED={str(payload['pkn_behavior_change_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={payload['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
