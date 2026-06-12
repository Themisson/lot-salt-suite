#!/usr/bin/env python3
"""Specify Phase 11.10Q fracture gate dispatch with sigma-theta guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10Q"
SPECIFIED = "FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED"
NEXT_PHASE = "PHASE11_10R_SPECIFY_PRESSURE_SIGMATHETA_FRACTURE_CRITERION"


def build_spec() -> dict[str, Any]:
    gate_states = [
        {
            "state": "FRACTURE_GATE_BLOCKED_BY_SIGMATHETA_GUARD",
            "meaning": "SigmaThetaInitialStateGuard returned gate_ready=false.",
            "dispatch_status": "FRACTURE_MODEL_DISPATCH_NOT_ALLOWED",
        },
        {
            "state": "FRACTURE_GATE_READY_FOR_CRITERION_EVALUATION",
            "meaning": "SigmaThetaInitialStateGuard returned SIGMATHETA_INITIAL_STATE_READY.",
            "dispatch_status": "FRACTURE_MODEL_DISPATCH_NOT_ALLOWED_UNTIL_CRITERION_REACHED",
        },
        {
            "state": "FRACTURE_GATE_NOT_REACHED",
            "meaning": "Guard passed, but future physical pressure x sigma-theta criterion was not reached.",
            "dispatch_status": "FRACTURE_MODEL_DISPATCH_NOT_ALLOWED",
        },
        {
            "state": "FRACTURE_GATE_REACHED",
            "meaning": "Guard passed and future physical criterion was reached.",
            "dispatch_status": "FRACTURE_MODEL_DISPATCH_ALLOWED_ONLY_AFTER_FUTURE_CRITERION_SPEC",
        },
        {
            "state": "FRACTURE_MODEL_DISPATCH_NOT_ALLOWED",
            "meaning": "Default state for Phase 11.10Q and any blocked/incomplete gate.",
        },
        {
            "state": "FRACTURE_MODEL_DISPATCH_ALLOWED",
            "meaning": "Future-only state; not enabled by Phase 11.10Q.",
        },
    ]

    required_fields = [
        "selected_fracture_model",
        "fracture_model_selection_source",
        "wellbore_pressure_Pa",
        "pressure_semantics",
        "sigma_theta_initial_compression_positive_Pa",
        "sigma_theta_current_compression_positive_Pa",
        "sigma_theta_source",
        "sigma_theta_state_time",
        "sigma_theta_reference_frame",
        "sigma_theta_sign_convention",
        "sigma_theta_guard_status",
        "fracture_initiation_gate_status",
        "fracture_dispatch_status",
        "blocking_reasons",
    ]

    blocking_rules = [
        {
            "status": "SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH",
            "rule": "fracture_model must not dispatch when sigma_theta_guard_status is not SIGMATHETA_INITIAL_STATE_READY",
        },
        {
            "status": "PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED",
            "rule": "fracture_model must not dispatch while pressure x sigma-theta criterion semantics are unspecified",
        },
        {
            "status": "SIGN_CONVENTION_RESOLUTION_REQUIRED",
            "rule": "fracture_model must not dispatch when sigma_theta_sign_convention is UNKNOWN",
        },
        {
            "status": "FRACTURE_MODEL_SELECTOR_REQUIRED_BEFORE_DISPATCH",
            "rule": "FractureModelSelector must resolve the selected model before the gate can dispatch",
        },
        {
            "status": "PENNY_SHAPED_RUNTIME_DISPATCH_BLOCKED",
            "rule": "PENNY_SHAPED must not dispatch as physical runtime while diagnostic_only is true",
        },
        {
            "status": "BUZ29_RUNTIME_EXECUTION_NOT_ALLOWED",
            "rule": "BUZ29-PENNY remains blocked until future phases authorize runtime execution",
        },
    ]

    dispatch_sequence = [
        "parser_reads_lot_fracture_fracture_model",
        "fracture_model_selector_resolves_selected_fracture_model",
        "lot_simulation_calculates_or_receives_initial_sigma_theta_state",
        "sigma_theta_initial_state_guard_validates_initial_state_and_pressure_semantics",
        "blocked_guard_sets_fracture_gate_blocked_and_dispatch_not_allowed",
        "ready_guard_allows_future_pressure_sigmatheta_criterion_evaluation",
        "criterion_not_reached_keeps_dispatch_not_allowed",
        "criterion_reached_may_dispatch_selected_model_only_in_future_authorized_phase",
    ]

    return {
        "phase": PHASE,
        "dispatch_spec_status": SPECIFIED,
        "sigmatheta_guard_required": True,
        "fracture_model_selector_required": True,
        "dispatch_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "requires_pressure_sigmatheta_criterion_spec": True,
        "requires_sign_convention_resolution": True,
        "dispatch_sequence": dispatch_sequence,
        "gate_states": gate_states,
        "required_fields": required_fields,
        "blocking_rules": blocking_rules,
        "audited_current_state": {
            "explicit_fracture_initiation_gate_function_exists": False,
            "gate_logic_currently_spread_across": [
                "src/lot/PknModel.cpp",
                "include/lot/FractureModelSelector.hpp",
                "include/lot/SigmaThetaInitialStateGuard.hpp",
            ],
            "safe_future_integration_point": (
                "future fracture_initiation_gate boundary before model dispatch, "
                "after FractureModelSelector and before any physical criterion"
            ),
        },
        "required_statuses": [
            "PHASE11_10Q_FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED",
            "FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED",
            "SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH",
            "FRACTURE_MODEL_SELECTOR_REQUIRED_BEFORE_DISPATCH",
            "PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED",
            "SIGN_CONVENTION_RESOLUTION_REQUIRED",
            "DISPATCH_REMAINS_BLOCKED",
        ],
        "recommended_next_phase": NEXT_PHASE,
        "caveats": [
            "Phase 11.10Q is specification only.",
            "No C++, parser, schema, CLI or runtime dispatch is changed.",
            "SigmaThetaInitialStateGuard remains isolated from runtime execution.",
            "PENNY_SHAPED remains diagnostic, not physically validated and not legacy-equivalent.",
            "BUZ29-PENNY is not executed.",
        ],
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10Q Fracture Gate Dispatch with Sigma-Theta Guard Spec",
        "",
        f"- phase: `{spec['phase']}`",
        f"- dispatch_spec_status: `{spec['dispatch_spec_status']}`",
        f"- sigmatheta_guard_required: `{str(spec['sigmatheta_guard_required']).lower()}`",
        f"- fracture_model_selector_required: `{str(spec['fracture_model_selector_required']).lower()}`",
        f"- dispatch_allowed_next: `{str(spec['dispatch_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(spec['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(spec['buz29_execution_allowed_next']).lower()}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Dispatch Sequence",
        "",
    ]
    lines.extend(f"- `{step}`" for step in spec["dispatch_sequence"])
    lines.extend(["", "## Gate States", ""])
    for state in spec["gate_states"]:
        lines.append(f"- `{state['state']}`: {state['meaning']}")
    lines.extend(["", "## Required Fields", ""])
    lines.extend(f"- `{field}`" for field in spec["required_fields"])
    lines.extend(["", "## Blocking Rules", ""])
    for rule in spec["blocking_rules"]:
        lines.append(f"- `{rule['status']}`: {rule['rule']}")
    lines.extend(["", "## Required Statuses", ""])
    lines.extend(f"- `{status}`" for status in spec["required_statuses"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in spec["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10Q fracture gate dispatch with sigma-theta guard."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = build_spec()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(spec, args.output_md)

    print(f"PHASE={spec['phase']}")
    print(f"DISPATCH_SPEC_STATUS={spec['dispatch_spec_status']}")
    print(f"SIGMATHETA_GUARD_REQUIRED={str(spec['sigmatheta_guard_required']).lower()}")
    print(
        "FRACTURE_MODEL_SELECTOR_REQUIRED="
        f"{str(spec['fracture_model_selector_required']).lower()}"
    )
    print(f"DISPATCH_ALLOWED_NEXT={str(spec['dispatch_allowed_next']).lower()}")
    print(
        "RUNTIME_EXECUTION_ALLOWED_NEXT="
        f"{str(spec['runtime_execution_allowed_next']).lower()}"
    )
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(spec['buz29_execution_allowed_next']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
