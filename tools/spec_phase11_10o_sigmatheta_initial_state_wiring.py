#!/usr/bin/env python3
"""Specify Phase 11.10O sigma-theta initial-state wiring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10O"
SPECIFIED = "SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED"
PARTIAL = "SIGMATHETA_INITIAL_STATE_WIRING_PARTIAL"
BLOCKED = "SIGMATHETA_INITIAL_STATE_WIRING_BLOCKED"
INCONCLUSIVE = "SIGMATHETA_INITIAL_STATE_WIRING_INCONCLUSIVE"
PREFERRED_SOURCE = "ELASTIC_INITIAL_WELLBORE_STATE"
NEXT_PHASE = "PHASE11_10P_IMPLEMENT_SIGMATHETA_INITIAL_STATE_WIRING_GUARD"


def build_spec() -> dict[str, Any]:
    required_fields = [
        {
            "field": "sigma_theta_initial_compression_positive_Pa",
            "required": True,
            "meaning": "post-drilling hoop stress state before LOT pressurization",
            "validation": "finite and positive when the fracture gate is enabled",
        },
        {
            "field": "sigma_theta_current_compression_positive_Pa",
            "required": True,
            "meaning": "current hoop stress or pressure-equivalent threshold at gate evaluation",
            "validation": "finite and pressure-compatible",
        },
        {
            "field": "sigma_theta_increment_due_to_lot_Pa",
            "required": False,
            "meaning": "optional incremental component caused by LOT loading",
            "validation": "finite if provided",
        },
        {
            "field": "sigma_theta_source",
            "required": True,
            "allowed_values": [
                "ELASTIC_INITIAL_WELLBORE_STATE",
                "APB_SALT_COUPLED_STATE",
                "LEGACY_DIAGNOSTIC_TRACE",
                "EXPLICIT_DIAGNOSTIC_INPUT",
                "SYNTHETIC_FIXTURE",
                "UNKNOWN",
            ],
        },
        {
            "field": "sigma_theta_state_time",
            "required": True,
            "allowed_values": [
                "AFTER_DRILLING_BEFORE_LOT",
                "DURING_LOT_STEP",
                "UNKNOWN",
            ],
        },
        {
            "field": "sigma_theta_initialized",
            "required": True,
            "validation": "must be true before fracture_initiation_gate evaluation",
        },
        {
            "field": "sigma_theta_initial_state_valid",
            "required": True,
            "validation": "must be true before fracture_initiation_gate evaluation",
        },
        {
            "field": "sigma_theta_sign_convention",
            "required": True,
            "allowed_values": ["COMPRESSION_POSITIVE", "TENSION_POSITIVE", "UNKNOWN"],
        },
        {
            "field": "sigma_theta_reference_frame",
            "required": True,
            "allowed_values": ["TOTAL_STRESS", "EFFECTIVE_STRESS", "INCREMENTAL_STRESS", "UNKNOWN"],
        },
    ]

    gate_rules = [
        {
            "status": "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA",
            "rule": "do not evaluate fracture if sigma_theta_initialized is false",
        },
        {
            "status": "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA",
            "rule": "do not evaluate fracture if sigma_theta_initial_state_valid is false",
        },
        {
            "status": "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
            "rule": "do not compare absolute pressure with incremental sigma-theta",
        },
        {
            "status": "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
            "rule": "do not compare pressure increment with total-stress sigma-theta",
        },
        {
            "status": "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
            "rule": "require explicit pressure semantics: wellbore_pressure_Pa, net_pressure_Pa, or pressure_increment_Pa",
        },
        {
            "status": "FRACTURE_GATE_BLOCKED_SIGN_CONVENTION_UNKNOWN",
            "rule": "do not evaluate fracture if sigma_theta_sign_convention is UNKNOWN",
        },
        {
            "status": "FRACTURE_GATE_READY_FOR_DISPATCH_SPEC",
            "rule": "allow future dispatch specification only after source, time, sign and reference frame are explicit",
        },
    ]

    compatibility = [
        {
            "pressure_semantics": "WELLBORE_PRESSURE_ABSOLUTE",
            "sigma_theta_reference_frame": "TOTAL_STRESS",
            "compatibility": "COMPATIBLE_IF_SAME_WALL_STATE_AND_SIGN_CONVENTION",
        },
        {
            "pressure_semantics": "WELLBORE_PRESSURE_ABSOLUTE",
            "sigma_theta_reference_frame": "EFFECTIVE_STRESS",
            "compatibility": "REQUIRES_PORE_PRESSURE_OR_EFFECTIVE_STRESS_DEFINITION",
        },
        {
            "pressure_semantics": "WELLBORE_PRESSURE_ABSOLUTE",
            "sigma_theta_reference_frame": "INCREMENTAL_STRESS",
            "compatibility": "BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
        },
        {
            "pressure_semantics": "PRESSURE_INCREMENT",
            "sigma_theta_reference_frame": "INCREMENTAL_STRESS",
            "compatibility": "COMPATIBLE_IF_INCREMENT_BASELINE_IS_EXPLICIT",
        },
        {
            "pressure_semantics": "PRESSURE_INCREMENT",
            "sigma_theta_reference_frame": "TOTAL_STRESS",
            "compatibility": "BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
        },
        {
            "pressure_semantics": "NET_PRESSURE",
            "sigma_theta_reference_frame": "TOTAL_STRESS",
            "compatibility": "REQUIRES_HYDROSTATIC_PORE_PRESSURE_AND_CLOSURE_REFERENCE",
        },
        {
            "pressure_semantics": "UNKNOWN",
            "sigma_theta_reference_frame": "UNKNOWN",
            "compatibility": "BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
        },
    ]

    return {
        "phase": PHASE,
        "wiring_spec_status": SPECIFIED,
        "preferred_source": PREFERRED_SOURCE,
        "source_candidates": [
            {
                "source": "ELASTIC_INITIAL_WELLBORE_STATE",
                "classification": "PREFERRED_SOURCE",
                "reason": "computed internally before LOT, after drilling-induced stress redistribution",
            },
            {
                "source": "APB_SALT_COUPLED_STATE",
                "classification": "FUTURE_SOURCE",
                "reason": "physically richer, but requires future coupled wall-stress runtime",
            },
            {
                "source": "LEGACY_DIAGNOSTIC_TRACE",
                "classification": "VALID_DIAGNOSTIC_SOURCE",
                "reason": "useful for trace comparison, not a production runtime source",
            },
            {
                "source": "EXPLICIT_DIAGNOSTIC_INPUT",
                "classification": "FALLBACK_WITH_CAVEAT",
                "reason": "acceptable only for controlled diagnostics, not as arbitrary production input",
            },
            {
                "source": "SYNTHETIC_FIXTURE",
                "classification": "FALLBACK_WITH_CAVEAT",
                "reason": "test fixture only",
            },
            {
                "source": "UNKNOWN",
                "classification": "BLOCKED_SOURCE",
                "reason": "cannot authorize fracture gate evaluation",
            },
        ],
        "required_fields": required_fields,
        "gate_rules": gate_rules,
        "pressure_sigmatheta_compatibility": compatibility,
        "sign_convention": "COMPRESSION_POSITIVE",
        "t0_lot_vs_drilling": {
            "lot_t0_meaning": "start of LOT pressurization",
            "drilling_t0_meaning": "wellbore creation",
            "required_assumption": "AFTER_DRILLING_BEFORE_LOT state must exist before fracture gate evaluation",
        },
        "dispatch_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "implementation_allowed_next": True,
        "recommended_next_phase": NEXT_PHASE,
        "required_statuses": [
            "PHASE11_10O_SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED",
            "SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED",
            "ELASTIC_INITIAL_WELLBORE_STATE_SELECTED_AS_PREFERRED_SOURCE",
            "FRACTURE_GATE_BLOCKED_UNTIL_SIGMATHETA_INITIALIZED",
            "PRESSURE_SIGMATHETA_COMPATIBILITY_REQUIRED",
            "DISPATCH_REMAINS_BLOCKED",
        ],
        "caveats": [
            "Phase 11.10O is specification only.",
            "No C++, parser, schema, runtime or protected case is changed.",
            "Dispatch remains blocked until a future guard implements the initial-state contract.",
            "BUZ29-PENNY is not executed and is not physically validated.",
        ],
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10O Sigma-Theta Initial-State Wiring Spec",
        "",
        f"- phase: `{spec['phase']}`",
        f"- wiring_spec_status: `{spec['wiring_spec_status']}`",
        f"- preferred_source: `{spec['preferred_source']}`",
        f"- sign_convention: `{spec['sign_convention']}`",
        f"- dispatch_allowed_next: `{str(spec['dispatch_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(spec['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(spec['buz29_execution_allowed_next']).lower()}`",
        f"- implementation_allowed_next: `{str(spec['implementation_allowed_next']).lower()}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Required Fields",
        "",
    ]
    for field in spec["required_fields"]:
        lines.append(f"- `{field['field']}`")
    lines.extend(["", "## Gate Rules", ""])
    for rule in spec["gate_rules"]:
        lines.append(f"- `{rule['status']}`: {rule['rule']}")
    lines.extend(["", "## Pressure x Sigma-Theta Compatibility", ""])
    lines.append("| Pressure semantics | Sigma-theta frame | Compatibility |")
    lines.append("|---|---|---|")
    for row in spec["pressure_sigmatheta_compatibility"]:
        lines.append(
            "| "
            f"`{row['pressure_semantics']}` | "
            f"`{row['sigma_theta_reference_frame']}` | "
            f"`{row['compatibility']}` |"
        )
    lines.extend(["", "## Required Statuses", ""])
    lines.extend(f"- `{status}`" for status in spec["required_statuses"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in spec["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10O sigma-theta initial-state wiring."
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
    print(f"WIRING_SPEC_STATUS={spec['wiring_spec_status']}")
    print(f"PREFERRED_SOURCE={spec['preferred_source']}")
    print(f"SIGN_CONVENTION={spec['sign_convention']}")
    print(f"DISPATCH_ALLOWED_NEXT={str(spec['dispatch_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(spec['runtime_execution_allowed_next']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(spec['buz29_execution_allowed_next']).lower()}")
    print(f"IMPLEMENTATION_ALLOWED_NEXT={str(spec['implementation_allowed_next']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
