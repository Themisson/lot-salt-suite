#!/usr/bin/env python3
"""Plan implementation of the selected elastic sigma-theta upgrade."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS = "ELASTIC_SIGMATHETA_UPGRADE_IMPLEMENTATION_PLAN_READY"
SELECTED_FORMULA = "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE"
PROPOSED_SOURCE = "AXISYMMETRIC_ELASTIC_WELLBORE_STATE"


def plan() -> dict[str, Any]:
    return {
        "phase": "ELASTIC_SIGMATHETA_UPGRADE_IMPLEMENTATION_PLAN",
        "plan_status": STATUS,
        "selected_formula": SELECTED_FORMULA,
        "proposed_provider_source": PROPOSED_SOURCE,
        "minimum_fields": [
            "far_field_stress_compression_positive_Pa",
            "wellbore_pressure_Pa",
            "tensile_strength_Pa",
        ],
        "optional_future_fields": [
            "wellbore_radius_m",
            "rock_or_layer_poisson_ratio",
            "rock_or_layer_young_modulus_Pa",
        ],
        "planned_formula": {
            "sigma_theta_initial_compression_positive_Pa": "far_field_stress_compression_positive_Pa",
            "sigma_theta_current_compression_positive_Pa": (
                "far_field_stress_compression_positive_Pa - wellbore_pressure_Pa"
            ),
            "interpretation": (
                "axisymmetric wall-stress diagnostic in compression-positive convention; "
                "same controlled fields as the simplified source, with explicit source identity "
                "and upgrade caveats"
            ),
        },
        "implementation_allowed_next": True,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "physically_validated": False,
        "legacy_equivalent": False,
        "required_changes": [
            "Add AXISYMMETRIC_ELASTIC_WELLBORE_STATE to PostDrillingSigmaThetaSource.",
            "Allow the new source in parser and schema.",
            "Preserve ELASTIC_INITIAL_WELLBORE_STATE behavior.",
            "Add C++ tests for provider, parser and pre-runner wiring.",
            "Add fixtures and Python audit for the new source.",
        ],
        "recommended_next_phase": "PHASE_IMPLEMENT_ELASTIC_SIGMATHETA_UPGRADE_SOURCE",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Elastic sigma-theta upgrade implementation plan",
        "",
        f"- plan_status: `{report['plan_status']}`",
        f"- selected_formula: `{report['selected_formula']}`",
        f"- proposed_provider_source: `{report['proposed_provider_source']}`",
        f"- implementation_allowed_next: `{report['implementation_allowed_next']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_change_allowed: `{report['pkn_behavior_change_allowed']}`",
        "",
        "## Minimum fields",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["minimum_fields"])
    lines.extend(["", "## Required changes", ""])
    lines.extend(f"- {item}" for item in report["required_changes"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan implementation of the selected elastic sigma-theta upgrade."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = plan()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.output_md:
        write_markdown(args.output_md, report)
    print(f"phase={report['phase']}")
    print(f"plan_status={report['plan_status']}")
    print(f"selected_formula={report['selected_formula']}")
    print(f"proposed_provider_source={report['proposed_provider_source']}")
    print(f"implementation_allowed_next={report['implementation_allowed_next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
