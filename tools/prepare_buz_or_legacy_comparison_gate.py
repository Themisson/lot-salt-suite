#!/usr/bin/env python3
"""Prepare the BUZ/legacy comparison gate without executing physical validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_PREPARE_BUZ_OR_LEGACY_COMPARISON_GATE"
GATE_STATUS = "BUZ_OR_LEGACY_COMPARISON_GATE_PREPARED"


def build_gate() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "gate_status": GATE_STATUS,
        "source": "AXISYMMETRIC_ELASTIC_WELLBORE_STATE",
        "recommended_first_comparison": "ANALYTIC_OR_BUZ67D_PKN_DIAGNOSTIC",
        "candidate_cases": [
            {
                "case_id": "axisymmetric_analytic_reference",
                "route": "analytic",
                "allowed": True,
                "purpose": "keep algebraic reference pinned before field/legacy comparisons",
            },
            {
                "case_id": "buz67d_pkn_diagnostic",
                "route": "modern_pkn_diagnostic",
                "allowed": True,
                "purpose": "future controlled diagnostic comparison, not physical validation",
            },
            {
                "case_id": "buz29_penny",
                "route": "non_pkn_legacy",
                "allowed": False,
                "purpose": "blocked until explicit non-PKN physical/runtime gate exists",
            },
        ],
        "fields_to_align_before_comparison": [
            "wellbore_pressure_Pa",
            "far_field_stress_compression_positive_Pa",
            "tensile_strength_Pa",
            "sigma_theta_current_compression_positive_Pa",
            "fracture_gate_reached",
            "time_s",
            "pressure_semantics",
            "stress_reference_frame",
            "sign_convention",
        ],
        "initial_tolerances": {
            "analytic_reference_abs_error_Pa": 1.0e-9,
            "diagnostic_pressure_relative_error_requires_future_gate": True,
            "opening_time_error_requires_future_gate": True,
        },
        "required_caveats": [
            "No physical validation is allowed by this gate.",
            "No legacy equivalence is allowed by this gate.",
            "BUZ29-PENNY execution remains blocked.",
            "PKN behavior must remain unchanged.",
            "Runtime dispatch remains disabled.",
            "Legacy traces may be used only as diagnostic context until a separate gate allows comparison.",
        ],
        "buz29_penny_execution_allowed": False,
        "legacy_equivalence_allowed": False,
        "physical_validation_allowed": False,
        "runtime_dispatch_enabled": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "results_versioned": False,
        "recommended_next_phase": "PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON",
    }


def write_outputs(gate: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# BUZ or Legacy Comparison Gate",
            "",
            f"- gate_status: `{gate['gate_status']}`",
            f"- source: `{gate['source']}`",
            f"- recommended_first_comparison: `{gate['recommended_first_comparison']}`",
            f"- buz29_penny_execution_allowed: `{str(gate['buz29_penny_execution_allowed']).lower()}`",
            f"- legacy_equivalence_allowed: `{str(gate['legacy_equivalence_allowed']).lower()}`",
            f"- physical_validation_allowed: `{str(gate['physical_validation_allowed']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(gate['runtime_dispatch_enabled']).lower()}`",
            f"- pkn_behavior_change_allowed: `{str(gate['pkn_behavior_change_allowed']).lower()}`",
            f"- recommended_next_phase: `{gate['recommended_next_phase']}`",
            "",
            "Candidate cases:",
            "",
        ]
        for row in gate["candidate_cases"]:
            lines.append(
                f"- `{row['case_id']}`: allowed=`{str(row['allowed']).lower()}`, route=`{row['route']}`"
            )
        lines.extend(
            [
                "",
                "The gate is preparatory. It does not execute BUZ29-PENNY, "
                "does not validate physics and does not declare legacy equivalence.",
                "",
            ]
        )
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare BUZ/legacy comparison gate without executing validation."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    gate = build_gate()
    write_outputs(gate, args.output_json, args.output_md)
    print(f"phase={gate['phase']}")
    print(f"gate_status={gate['gate_status']}")
    print(f"recommended_first_comparison={gate['recommended_first_comparison']}")
    print(f"buz29_penny_execution_allowed={gate['buz29_penny_execution_allowed']}")
    print(f"legacy_equivalence_allowed={gate['legacy_equivalence_allowed']}")
    print(f"physical_validation_allowed={gate['physical_validation_allowed']}")
    print(f"recommended_next_phase={gate['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
