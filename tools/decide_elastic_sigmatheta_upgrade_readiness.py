#!/usr/bin/env python3
"""Decide readiness of the axisymmetric elastic sigma-theta upgrade source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


READY_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_READY_FOR_DIAGNOSTIC_USE"
PARTIAL_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_READINESS_PARTIAL"
SOURCE = "AXISYMMETRIC_ELASTIC_WELLBORE_STATE"


def build_decision(*, analytic_valid: bool = True, source_implemented: bool = True) -> dict:
    ready = analytic_valid and source_implemented
    status = READY_STATUS if ready else PARTIAL_STATUS
    return {
        "phase": "ELASTIC_SIGMATHETA_UPGRADE_READINESS_DECISION",
        "readiness_status": status,
        "source": SOURCE,
        "selected_formula": "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE",
        "source_implemented": source_implemented,
        "analytic_validation_valid": analytic_valid,
        "ready_for_diagnostic_use": ready,
        "ready_for_controlled_physical_comparison": False,
        "ready_for_physical_dispatch": False,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "kirsch_full_blocked": True,
        "kirsch_blocking_fields": ["sigma_H", "sigma_h", "azimuth_angle_rad"],
        "required_statuses": [
            "ELASTIC_SIGMATHETA_UPGRADE_FIELDS_DIAGNOSED",
            "ELASTIC_SIGMATHETA_UPGRADE_FORMULA_SELECTED",
            "ELASTIC_SIGMATHETA_UPGRADE_IMPLEMENTATION_PLAN_READY",
            "ELASTIC_SIGMATHETA_UPGRADE_SOURCE_IMPLEMENTED",
            "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES_VALID",
        ],
        "caveats": [
            "Ready for diagnostic use only.",
            "Not physically validated.",
            "Not legacy-equivalent.",
            "Runtime dispatch remains disabled.",
            "BUZ29-PENNY remains blocked.",
            "Kirsch full orientation remains blocked until sigma_H, sigma_h and azimuth are available.",
        ],
        "recommended_next_phase": (
            "PHASE_COMPARE_ELASTIC_SIGMATHETA_SOURCE_WITH_LEGACY_OR_ANALYTIC_REFERENCE"
        ),
    }


def write_outputs(decision: dict, output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Elastic Sigma-Theta Upgrade Readiness Decision",
            "",
            f"- readiness_status: `{decision['readiness_status']}`",
            f"- source: `{decision['source']}`",
            f"- ready_for_diagnostic_use: `{str(decision['ready_for_diagnostic_use']).lower()}`",
            f"- ready_for_controlled_physical_comparison: `{str(decision['ready_for_controlled_physical_comparison']).lower()}`",
            f"- ready_for_physical_dispatch: `{str(decision['ready_for_physical_dispatch']).lower()}`",
            f"- physically_validated: `{str(decision['physically_validated']).lower()}`",
            f"- legacy_equivalent: `{str(decision['legacy_equivalent']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(decision['runtime_dispatch_enabled']).lower()}`",
            f"- buz29_execution_allowed: `{str(decision['buz29_execution_allowed']).lower()}`",
            f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
            "",
            "The source is ready for diagnostic use only. It must not be used "
            "as physical validation, legacy equivalence or runtime dispatch.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide readiness of the axisymmetric elastic sigma-theta upgrade."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument(
        "--analytic-valid",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether the analytic validation gate passed.",
    )
    parser.add_argument(
        "--source-implemented",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether the provider source implementation gate passed.",
    )
    args = parser.parse_args()

    decision = build_decision(
        analytic_valid=args.analytic_valid,
        source_implemented=args.source_implemented,
    )
    write_outputs(decision, args.output_json, args.output_md)
    print(f"phase={decision['phase']}")
    print(f"readiness_status={decision['readiness_status']}")
    print(f"source={decision['source']}")
    print(f"ready_for_diagnostic_use={decision['ready_for_diagnostic_use']}")
    print(f"ready_for_physical_dispatch={decision['ready_for_physical_dispatch']}")
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0 if decision["readiness_status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
