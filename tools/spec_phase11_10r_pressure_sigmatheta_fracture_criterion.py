#!/usr/bin/env python3
"""Specify Phase 11.10R pressure x sigma-theta fracture criterion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10R"
STATUS = "PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED"
NEXT_PHASE = "PHASE11_10S_IMPLEMENT_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD"


def build_spec() -> dict[str, Any]:
    pressure_fields = [
        {
            "field": "wellbore_pressure_Pa",
            "semantics": "absolute_or_total_wellbore_pressure_candidate",
            "status": "runtime_diagnostic_in_volumetric_balance",
            "use_in_future_gate": "preferred_pressure_input_when_semantics_are_explicit",
        },
        {
            "field": "wall_pressure_Pa",
            "semantics": "compressive_wall_pressure_for_salt_bridge",
            "status": "coupling_and_salt_diagnostic_field",
            "use_in_future_gate": "not_direct_lot_fracture_gate_input_without_mapping",
        },
        {
            "field": "net_pressure_Pa",
            "semantics": "PKN_net_pressure_increment",
            "status": "runtime_pkn_direct_output",
            "use_in_future_gate": "blocked_as_absolute_pressure_without_reference_transform",
        },
        {
            "field": "trial_pressure_Pa",
            "semantics": "internal_step_candidate_before_sink_application",
            "status": "local_PknModel_implementation_detail",
            "use_in_future_gate": "future_guard_may_use_equivalent_explicit_field",
        },
        {
            "field": "fracture_threshold_pressure_Pa",
            "semantics": "derived_threshold_from_stress_state_and_tensile_strength",
            "status": "future_required_field",
            "use_in_future_gate": "alternative_threshold_form",
        },
    ]
    sigma_theta_fields = [
        {
            "field": "sigma_theta_compression_positive_Pa",
            "semantics": "compression_positive_sigma_theta_sample",
            "status": "diagnostic_and_provider_field",
            "use_in_future_gate": "only_when_reference_frame_and_time_are_known",
        },
        {
            "field": "sigma_theta_initial_compression_positive_Pa",
            "semantics": "initial_after_drilling_before_LOT_state",
            "status": "guard_input_available",
            "use_in_future_gate": "precondition_not_current_criterion_by_itself",
        },
        {
            "field": "sigma_theta_current_compression_positive_Pa",
            "semantics": "current_total_or_effective_sigma_theta_at_gate_time",
            "status": "future_required_preferred_field",
            "use_in_future_gate": "preferred_stress_input",
        },
        {
            "field": "sigma_theta_increment_due_to_lot_Pa",
            "semantics": "LOT_induced_increment_to_initial_sigma_theta",
            "status": "future_optional_if_current_state_is_not_available",
            "use_in_future_gate": "requires_explicit_reference_frame",
        },
    ]
    criterion_states = [
        "FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY",
        "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN",
        "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN",
        "FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH",
        "FRACTURE_CRITERION_READY",
        "FRACTURE_NOT_INITIATED",
        "FRACTURE_INITIATED",
    ]
    required_fields = [
        "wellbore_pressure_Pa",
        "sigma_theta_current_compression_positive_Pa",
        "tensile_strength_Pa",
        "pressure_semantics",
        "sigma_theta_reference_frame",
        "sigma_theta_sign_convention",
        "fracture_margin_Pa",
    ]
    forbidden_shortcuts = [
        "pressure_greater_than_sigma_theta_without_sign_reference_transform",
        "wellbore_pressure_Pa > sigma_theta_compression_positive_Pa as final physical criterion",
        "net_pressure_Pa compared directly with sigma_theta_compression_positive_Pa",
    ]
    return {
        "phase": PHASE,
        "criterion_spec_status": STATUS,
        "sigma_theta_sign_convention": "COMPRESSION_POSITIVE",
        "sigma_theta_positive_meaning": "compression",
        "sigma_theta_negative_meaning": "tension",
        "pressure_semantics_required": True,
        "guard_required": True,
        "forbidden_shortcut": "pressure_greater_than_sigma_theta_without_sign_reference_transform",
        "forbidden_shortcuts": forbidden_shortcuts,
        "preferred_criterion": "sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa",
        "preferred_tensile_condition": "tensile_condition_Pa = -sigma_theta_current_compression_positive_Pa",
        "alternative_threshold_form": "fracture_margin_Pa = wellbore_pressure_Pa - fracture_threshold_pressure_Pa",
        "threshold_requirement": (
            "fracture_threshold_pressure_Pa must be derived from sigma_theta, "
            "tensile_strength_Pa, and an explicit reference frame"
        ),
        "dispatch_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "implementation_allowed_next": True,
        "recommended_next_phase": NEXT_PHASE,
        "pressure_fields": pressure_fields,
        "sigma_theta_fields": sigma_theta_fields,
        "criterion_states": criterion_states,
        "required_fields": required_fields,
        "classifications": [
            STATUS,
            "SIGMATHETA_COMPRESSION_POSITIVE_SIGN_CONVENTION_RESOLVED",
            "PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN",
            "DISPATCH_REMAINS_BLOCKED_UNTIL_CRITERION_GUARD_IMPLEMENTED",
        ],
        "caveats": [
            "This phase specifies algebra only; it does not implement C++ runtime logic.",
            "The existing legacy_algebra comparison remains diagnostic and is not the final physical criterion.",
            "A future guard must reject unknown pressure semantics, unknown sign convention, and reference-frame mismatch.",
        ],
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10R pressure x sigma-theta fracture criterion",
        "",
        f"- phase: `{spec['phase']}`",
        f"- status: `{spec['criterion_spec_status']}`",
        f"- sign convention: `{spec['sigma_theta_sign_convention']}`",
        f"- preferred criterion: `{spec['preferred_criterion']}`",
        f"- alternative threshold form: `{spec['alternative_threshold_form']}`",
        f"- dispatch_allowed_next: `{str(spec['dispatch_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(spec['runtime_execution_allowed_next']).lower()}`",
        f"- implementation_allowed_next: `{str(spec['implementation_allowed_next']).lower()}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Forbidden shortcuts",
        "",
    ]
    lines.extend(f"- `{item}`" for item in spec["forbidden_shortcuts"])
    lines.extend(["", "## Criterion States", ""])
    lines.extend(f"- `{item}`" for item in spec["criterion_states"])
    lines.extend(["", "## Required Fields", ""])
    lines.extend(f"- `{item}`" for item in spec["required_fields"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10R pressure x sigma-theta fracture criterion."
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
    print(f"CRITERION_SPEC_STATUS={spec['criterion_spec_status']}")
    print(f"SIGMA_THETA_SIGN_CONVENTION={spec['sigma_theta_sign_convention']}")
    print(f"PRESSURE_SEMANTICS_REQUIRED={str(spec['pressure_semantics_required']).lower()}")
    print(f"GUARD_REQUIRED={str(spec['guard_required']).lower()}")
    print(f"DISPATCH_ALLOWED_NEXT={str(spec['dispatch_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(spec['runtime_execution_allowed_next']).lower()}")
    print(f"IMPLEMENTATION_ALLOWED_NEXT={str(spec['implementation_allowed_next']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
