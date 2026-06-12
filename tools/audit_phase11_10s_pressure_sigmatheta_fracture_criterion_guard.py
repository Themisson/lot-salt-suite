#!/usr/bin/env python3
"""Audit Phase 11.10S pressure x sigma-theta fracture criterion guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10S"
STATUS = "PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED"
NEXT_PHASE = "PHASE11_10T_SPECIFY_FRACTURE_GATE_RUNTIME_WIRING_WITH_GUARDS"


def build_audit() -> dict[str, Any]:
    source_files = [
        "include/lot/PressureSigmaThetaFractureCriterionGuard.hpp",
        "src/lot/PressureSigmaThetaFractureCriterionGuard.cpp",
        "tests/cpp/test_pressure_sigma_theta_fracture_criterion_guard.cpp",
    ]
    return {
        "phase": PHASE,
        "implementation_status": STATUS,
        "sigma_theta_sign_convention": "COMPRESSION_POSITIVE",
        "preferred_criterion": (
            "sigma_theta_current_compression_positive_Pa <= "
            "-tensile_strength_Pa"
        ),
        "preferred_tensile_condition": (
            "tensile_condition_Pa = "
            "-sigma_theta_current_compression_positive_Pa"
        ),
        "preferred_margin": (
            "fracture_margin_Pa = tensile_condition_Pa - tensile_strength_Pa"
        ),
        "threshold_form_available": True,
        "threshold_form": (
            "fracture_margin_Pa = wellbore_pressure_Pa - "
            "fracture_threshold_pressure_Pa"
        ),
        "forbidden_shortcut": (
            "pressure_greater_than_sigma_theta_without_sign_reference_transform"
        ),
        "dispatch_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "parser_schema_changed": False,
        "runtime_dispatch_changed": False,
        "lot_pkn_behavior_changed": False,
        "source_files": source_files,
        "criterion_blocking_statuses": [
            "FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY",
            "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN",
            "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN",
            "FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH",
            "FRACTURE_CRITERION_BLOCKED_INVALID_TENSILE_STRENGTH",
            "FRACTURE_CRITERION_BLOCKED_INVALID_SIGMATHETA",
            "FRACTURE_CRITERION_BLOCKED_INVALID_PRESSURE",
        ],
        "criterion_ready_statuses": [
            "FRACTURE_CRITERION_READY_NOT_INITIATED",
            "FRACTURE_CRITERION_READY_INITIATED",
        ],
        "classifications": [
            "PHASE11_10S_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED",
            STATUS,
            "SIGMATHETA_COMPRESSION_POSITIVE_CRITERION_IMPLEMENTED",
            "PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN",
            "RUNTIME_DISPATCH_NOT_CHANGED",
            "LOT_PKN_BEHAVIOR_NOT_CHANGED",
        ],
        "recommended_next_phase": NEXT_PHASE,
        "caveats": [
            "The guard is isolated C++ helper code.",
            "The guard is not integrated into parser, schema, CLI, PknModel, "
            "PknRunner or runtime dispatch.",
            "BUZ29-PENNY is not executed.",
            "No physical validation or legacy equivalence is claimed.",
        ],
    }


def write_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10S pressure x sigma-theta fracture criterion guard",
        "",
        f"- phase: `{audit['phase']}`",
        f"- implementation_status: `{audit['implementation_status']}`",
        f"- sign convention: `{audit['sigma_theta_sign_convention']}`",
        f"- preferred criterion: `{audit['preferred_criterion']}`",
        f"- threshold form available: `{str(audit['threshold_form_available']).lower()}`",
        f"- dispatch_allowed_next: `{str(audit['dispatch_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(audit['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(audit['buz29_execution_allowed_next']).lower()}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Source Files",
        "",
    ]
    lines.extend(f"- `{item}`" for item in audit["source_files"])
    lines.extend(["", "## Blocking Statuses", ""])
    lines.extend(f"- `{item}`" for item in audit["criterion_blocking_statuses"])
    lines.extend(["", "## Classifications", ""])
    lines.extend(f"- `{item}`" for item in audit["classifications"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Phase 11.10S pressure x sigma-theta fracture criterion guard."
        )
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args(argv)

    audit = build_audit()
    if args.output_json:
      args.output_json.parent.mkdir(parents=True, exist_ok=True)
      args.output_json.write_text(
          json.dumps(audit, indent=2, sort_keys=True) + "\n",
          encoding="utf-8",
      )
    if args.output_md:
      write_markdown(audit, args.output_md)

    print(f"PHASE={audit['phase']}")
    print(f"IMPLEMENTATION_STATUS={audit['implementation_status']}")
    print(f"SIGMA_THETA_SIGN_CONVENTION={audit['sigma_theta_sign_convention']}")
    print(f"THRESHOLD_FORM_AVAILABLE={str(audit['threshold_form_available']).lower()}")
    print(f"DISPATCH_ALLOWED_NEXT={str(audit['dispatch_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(audit['runtime_execution_allowed_next']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(audit['buz29_execution_allowed_next']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
