#!/usr/bin/env python3
"""Specify Phase 11.10T fracture gate runtime wiring with guards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10T"
STATUS = "FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED"
NEXT_PHASE = "PHASE11_10U_SPECIFY_RUNTIME_WIRING_TEST_FIXTURES"


def build_spec() -> dict[str, Any]:
    required_components = [
        "FractureModelSelector",
        "SigmaThetaInitialStateGuard",
        "PressureSigmaThetaFractureCriterionGuard",
        "PknModel",
        "PennyShapedDiagnosticAdapter",
        "PennyShapedDiagnosticWriter",
    ]
    runtime_sequence = [
        "Read CaseData after parser/schema defaults have selected PKN when fracture_model is absent.",
        "Resolve selected_fracture_model with FractureModelSelector.",
        "Keep PKN on the existing retrocompatible runtime path unless an explicit gate is enabled.",
        "Collect pressure semantics and sigma-theta initial-state metadata before any non-PKN dispatch.",
        "Run SigmaThetaInitialStateGuard.",
        "Block fracture gate if the sigma-theta initial-state guard is not ready.",
        "Build PressureSigmaThetaCriterionInput only after the initial-state guard passes.",
        "Run PressureSigmaThetaFractureCriterionGuard.",
        "Block dispatch if the pressure x sigma-theta criterion is not ready or not initiated.",
        "Dispatch PKN only through the existing validated PKN route.",
        "Keep PENNY_SHAPED diagnostic-only until explicit runtime tests authorize execution.",
    ]
    gate_states = [
        "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE",
        "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION",
        "FRACTURE_GATE_READY_NOT_REACHED",
        "FRACTURE_GATE_REACHED",
        "FRACTURE_DISPATCH_NOT_ALLOWED",
        "FRACTURE_DISPATCH_NOT_EXECUTED",
        "FRACTURE_DISPATCH_PKN_ELIGIBLE",
        "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE",
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
        "tensile_strength_Pa",
        "sigma_theta_guard_status",
        "pressure_sigmatheta_criterion_status",
        "fracture_initiation_gate_status",
        "fracture_dispatch_status",
        "fracture_initiated",
        "fracture_margin_Pa",
        "blocking_reasons",
    ]
    blocking_rules = [
        "FractureModelSelector must resolve selected model before dispatch.",
        "SigmaThetaInitialStateGuard must pass before pressure x sigma-theta criterion.",
        "PressureSigmaThetaFractureCriterionGuard must pass before dispatch.",
        "Unknown pressure semantics blocks the criterion.",
        "Unknown sigma_theta reference frame blocks the criterion.",
        "Unknown or non compression-positive sign convention blocks the criterion.",
        "PENNY_SHAPED remains diagnostic_only.",
        "BUZ29-PENNY remains blocked.",
        "PKN default must preserve existing behavior.",
        "Runtime wiring remains blocked until future integration tests prove no PKN regression.",
    ]
    return {
        "phase": PHASE,
        "runtime_wiring_spec_status": STATUS,
        "source": "DOCUMENTED_PHASE_SUMMARY",
        "required_components": required_components,
        "component_audit": [
            {
                "component": "FractureModelSelector",
                "current_status": "IMPLEMENTED_ISOLATED_SELECTOR",
                "future_role": "Resolve PKN vs PENNY_SHAPED before fracture gate dispatch.",
            },
            {
                "component": "SigmaThetaInitialStateGuard",
                "current_status": "IMPLEMENTED_ISOLATED_GUARD",
                "future_role": "Block gate until sigma-theta state, source, time, sign and frame are explicit.",
            },
            {
                "component": "PressureSigmaThetaFractureCriterionGuard",
                "current_status": "IMPLEMENTED_ISOLATED_GUARD",
                "future_role": "Evaluate fracture criterion only after sigma-theta guard passes.",
            },
            {
                "component": "PknModel",
                "current_status": "DEFAULT_RUNTIME_PATH",
                "future_role": "Remain retrocompatible and unaffected by non-PKN diagnostic gates.",
            },
            {
                "component": "PennyShapedDiagnosticAdapter",
                "current_status": "DIAGNOSTIC_ONLY",
                "future_role": "Remain blocked from physical runtime dispatch until explicitly authorized.",
            },
        ],
        "runtime_sequence": runtime_sequence,
        "gate_states": gate_states,
        "required_fields": required_fields,
        "blocking_rules": blocking_rules,
        "runtime_wiring_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_diagnostic_only": True,
        "pkn_status": "DEFAULT_RETROCOMPATIBLE_NO_BEHAVIOR_CHANGE",
        "penny_shaped_status": (
            "DIAGNOSTIC_ONLY_NOT_PHYSICALLY_VALIDATED_NOT_LEGACY_EQUIVALENT"
        ),
        "classifications": [
            "PHASE11_10T_FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED",
            STATUS,
            "FRACTURE_MODEL_SELECTOR_REQUIRED",
            "SIGMATHETA_INITIAL_STATE_GUARD_REQUIRED",
            "PRESSURE_SIGMATHETA_CRITERION_GUARD_REQUIRED",
            "RUNTIME_WIRING_NOT_IMPLEMENTED",
            "DISPATCH_REMAINS_BLOCKED",
        ],
        "recommended_next_phase": NEXT_PHASE,
        "caveats": [
            "Phase 11.10T is specification only.",
            "No C++, parser, schema, CLI or runtime dispatch is changed.",
            "PENNY_SHAPED remains diagnostic, not physically validated and not legacy-equivalent.",
            "BUZ29-PENNY is not executed.",
            "PKN remains the default retrocompatible path.",
        ],
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10T fracture gate runtime wiring specification",
        "",
        f"- phase: `{spec['phase']}`",
        f"- runtime_wiring_spec_status: `{spec['runtime_wiring_spec_status']}`",
        f"- runtime_wiring_allowed_next: `{str(spec['runtime_wiring_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(spec['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(spec['buz29_execution_allowed_next']).lower()}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Required Components",
        "",
    ]
    lines.extend(f"- `{item}`" for item in spec["required_components"])
    lines.extend(["", "## Runtime Sequence", ""])
    lines.extend(
        f"{index}. {step}" for index, step in enumerate(spec["runtime_sequence"], 1)
    )
    lines.extend(["", "## Gate States", ""])
    lines.extend(f"- `{item}`" for item in spec["gate_states"])
    lines.extend(["", "## Required Fields", ""])
    lines.extend(f"- `{item}`" for item in spec["required_fields"])
    lines.extend(["", "## Blocking Rules", ""])
    lines.extend(f"- {item}" for item in spec["blocking_rules"])
    lines.extend(["", "## Classifications", ""])
    lines.extend(f"- `{item}`" for item in spec["classifications"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10T fracture gate runtime wiring with guards."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args(argv)

    spec = build_spec()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(spec, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(spec, args.output_md)

    print(f"PHASE={spec['phase']}")
    print(f"RUNTIME_WIRING_SPEC_STATUS={spec['runtime_wiring_spec_status']}")
    print(f"RUNTIME_WIRING_ALLOWED_NEXT={str(spec['runtime_wiring_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(spec['runtime_execution_allowed_next']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(spec['buz29_execution_allowed_next']).lower()}")
    print(f"PKN_BEHAVIOR_CHANGE_ALLOWED={str(spec['pkn_behavior_change_allowed']).lower()}")
    print(f"PENNY_SHAPED_DIAGNOSTIC_ONLY={str(spec['penny_shaped_diagnostic_only']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
