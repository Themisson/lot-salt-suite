#!/usr/bin/env python3
"""Diagnose available fields for the elastic sigma-theta upgrade."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS = "ELASTIC_SIGMATHETA_UPGRADE_FIELDS_DIAGNOSED"
RECOMMENDED_PATH = "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE"


def diagnose() -> dict[str, Any]:
    available = {
        "wellbore_pressure_Pa": True,
        "far_field_stress_compression_positive_Pa": True,
        "far_field_min_horizontal_stress_Pa": False,
        "far_field_max_horizontal_stress_Pa": False,
        "vertical_stress_Pa": False,
        "azimuth_angle_rad": False,
        "wellbore_radius_m": False,
        "casing_radius_m": False,
        "poisson_ratio": False,
        "young_modulus_Pa": False,
        "tensile_strength_Pa": True,
        "axisymmetric_angle_rad": False,
        "layer_material_properties": True,
    }
    has_kirsch = (
        available["far_field_min_horizontal_stress_Pa"]
        and available["far_field_max_horizontal_stress_Pa"]
        and available["azimuth_angle_rad"]
        and available["wellbore_pressure_Pa"]
    )
    has_axisymmetric = (
        available["far_field_stress_compression_positive_Pa"]
        and available["wellbore_pressure_Pa"]
        and available["tensile_strength_Pa"]
    )
    has_simplified = has_axisymmetric
    implementation_allowed = has_axisymmetric and not has_kirsch
    return {
        "phase": "ELASTIC_SIGMATHETA_UPGRADE_FIELD_DIAGNOSIS",
        "diagnosis_status": STATUS,
        "field_availability": available,
        "has_kirsch_required_fields": has_kirsch,
        "has_axisymmetric_required_fields": has_axisymmetric,
        "has_simplified_required_fields": has_simplified,
        "recommended_formula_path": RECOMMENDED_PATH
        if implementation_allowed
        else "BLOCKED_BY_MISSING_STRESS_OR_GEOMETRY_FIELDS",
        "implementation_allowed_next": implementation_allowed,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "physically_validated": False,
        "legacy_equivalent": False,
        "evidence": [
            "sigma_theta_provider currently exposes far_field_stress_compression_positive_Pa",
            "sigma_theta_provider currently exposes wellbore_pressure_Pa",
            "sigma_theta_provider currently exposes tensile_strength_Pa",
            "schema/parser do not expose sigma_H, sigma_h or azimuth_angle_rad",
            "runtime/cases remain axisymmetric for this diagnostic path",
        ],
        "caveats": [
            "Kirsch full orientation is not implementable with current fields.",
            "Axisymmetric upgrade can remain opt-in and diagnostic.",
            "No physical dispatch is allowed by this diagnosis.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Elastic sigma-theta upgrade field diagnosis",
        "",
        f"- diagnosis_status: `{report['diagnosis_status']}`",
        f"- has_kirsch_required_fields: `{report['has_kirsch_required_fields']}`",
        f"- has_axisymmetric_required_fields: `{report['has_axisymmetric_required_fields']}`",
        f"- has_simplified_required_fields: `{report['has_simplified_required_fields']}`",
        f"- recommended_formula_path: `{report['recommended_formula_path']}`",
        f"- implementation_allowed_next: `{report['implementation_allowed_next']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_change_allowed: `{report['pkn_behavior_change_allowed']}`",
        "",
        "## Fields",
        "",
    ]
    for name, value in report["field_availability"].items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(["", "## Evidence", ""])
    lines.extend(f"- {item}" for item in report["evidence"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in report["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose available fields for the elastic sigma-theta upgrade."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = diagnose()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.output_md:
        write_markdown(args.output_md, report)
    print(f"phase={report['phase']}")
    print(f"diagnosis_status={report['diagnosis_status']}")
    print(f"has_kirsch_required_fields={report['has_kirsch_required_fields']}")
    print(
        f"has_axisymmetric_required_fields={report['has_axisymmetric_required_fields']}"
    )
    print(f"recommended_formula_path={report['recommended_formula_path']}")
    print(f"implementation_allowed_next={report['implementation_allowed_next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
