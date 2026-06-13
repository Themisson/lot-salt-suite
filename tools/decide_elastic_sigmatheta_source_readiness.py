#!/usr/bin/env python3
"""Decide readiness of the elastic sigma-theta source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


READINESS_STATUS = "ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE"
NEXT_PHASE = "PHASE_SPECIFY_KIRSCH_OR_AXISYMMETRIC_ELASTIC_SIGMATHETA_UPGRADE"


def build_decision() -> dict[str, Any]:
    return {
        "phase": "ELASTIC_SIGMATHETA_SOURCE_READINESS",
        "readiness_status": READINESS_STATUS,
        "classifications": [
            READINESS_STATUS,
            "ELASTIC_SIGMATHETA_SOURCE_READY_FOR_KIRSCH_UPGRADE_SPEC",
            "READY_FOR_KIRSCH_OR_AXISYMMETRIC_UPGRADE_SPEC",
            "PHYSICALLY_VALIDATED_FALSE",
            "LEGACY_EQUIVALENT_FALSE",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PKN_BEHAVIOR_NOT_CHANGED",
        ],
        "source": "ELASTIC_INITIAL_WELLBORE_STATE",
        "source_status": "SEMI_PHYSICAL_DIAGNOSTIC_SOURCE",
        "ready_for_diagnostic_semiphysical_use": True,
        "ready_for_physical_validation": False,
        "ready_for_physical_dispatch": False,
        "ready_for_kirsch_upgrade_spec": True,
        "formula_verified": True,
        "sign_convention_verified": True,
        "threshold_behavior_verified": True,
        "semi_physical": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "preferred_upgrade_path": "AXISYMMETRIC_ELASTIC_SIGMATHETA_UPGRADE",
        "recommended_next_phase": NEXT_PHASE,
        "evidence": {
            "formula": (
                "sigma_theta_current_compression_positive_Pa = "
                "far_field_stress_compression_positive_Pa - wellbore_pressure_Pa"
            ),
            "criterion": (
                "fracture_margin_Pa = "
                "-sigma_theta_current_compression_positive_Pa - tensile_strength_Pa"
            ),
            "analytic_validation_status": "ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID",
            "validated_case_count": 5,
        },
        "alternatives": [
            {
                "id": "A",
                "name": "Kirsch/hoop stress simplified",
                "status": "READY_FOR_SPECIFICATION",
                "risk": "requires horizontal stresses and orientation, or an axisymmetric reduction",
            },
            {
                "id": "B",
                "name": "Axisymmetric elastic sigma-theta provider",
                "status": "PREFERRED_FOR_NEXT_SPEC",
                "risk": "requires explicit mapping of wall pressure, layers and material state",
            },
            {
                "id": "C",
                "name": "APB/salt/coupled state",
                "status": "FUTURE_WORK",
                "risk": "requires salt/APB runtime coupling and resolved wall-stress semantics",
            },
        ],
        "caveats": [
            "Diagnostic semi-physical readiness is not physical validation.",
            "The source is not legacy-equivalent.",
            "Physical dispatch remains disabled.",
            "BUZ29-PENNY remains blocked.",
            "PKN behavior remains unchanged.",
            "The current formula is a simplified elastic approximation.",
        ],
    }


def write_markdown(path: Path, decision: dict[str, Any]) -> None:
    lines = [
        "# Elastic sigma-theta source readiness",
        "",
        f"- phase: `{decision['phase']}`",
        f"- readiness_status: `{decision['readiness_status']}`",
        f"- source: `{decision['source']}`",
        f"- ready_for_diagnostic_semiphysical_use: `{decision['ready_for_diagnostic_semiphysical_use']}`",
        f"- ready_for_physical_validation: `{decision['ready_for_physical_validation']}`",
        f"- ready_for_physical_dispatch: `{decision['ready_for_physical_dispatch']}`",
        f"- ready_for_kirsch_upgrade_spec: `{decision['ready_for_kirsch_upgrade_spec']}`",
        f"- formula_verified: `{decision['formula_verified']}`",
        f"- sign_convention_verified: `{decision['sign_convention_verified']}`",
        f"- threshold_behavior_verified: `{decision['threshold_behavior_verified']}`",
        f"- physically_validated: `{decision['physically_validated']}`",
        f"- legacy_equivalent: `{decision['legacy_equivalent']}`",
        f"- runtime_dispatch_enabled: `{decision['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{decision['buz29_execution_allowed']}`",
        f"- pkn_behavior_change_allowed: `{decision['pkn_behavior_change_allowed']}`",
        f"- preferred_upgrade_path: `{decision['preferred_upgrade_path']}`",
        f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
        "",
        "## Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in decision["classifications"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in decision["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide readiness of the elastic sigma-theta source."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    decision = build_decision()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, decision)

    print(f"phase={decision['phase']}")
    print(f"readiness_status={decision['readiness_status']}")
    print(
        "ready_for_diagnostic_semiphysical_use="
        f"{decision['ready_for_diagnostic_semiphysical_use']}"
    )
    print(f"ready_for_physical_validation={decision['ready_for_physical_validation']}")
    print(f"ready_for_physical_dispatch={decision['ready_for_physical_dispatch']}")
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
