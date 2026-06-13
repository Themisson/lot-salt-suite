#!/usr/bin/env python3
"""Decide the elastic sigma-theta upgrade formula."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS = "ELASTIC_SIGMATHETA_UPGRADE_FORMULA_SELECTED"
SELECTED_FORMULA = "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE"


def decide() -> dict[str, Any]:
    return {
        "phase": "ELASTIC_SIGMATHETA_UPGRADE_FORMULA_DECISION",
        "formula_decision_status": STATUS,
        "selected_formula": SELECTED_FORMULA,
        "rejected_formulas": [
            {
                "formula": "KIRSCH_ELASTIC_WELLBORE_SOURCE",
                "reason": "missing sigma_H, sigma_h and azimuth_angle_rad in current provider contract",
            },
            {
                "formula": "KEEP_SIMPLIFIED_ELASTIC_SOURCE",
                "reason": "axisymmetric diagnostic source can be specified with current controlled fields",
            },
        ],
        "implementation_allowed_next": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "decision_basis": [
            "Current runtime/cases are axisymmetric for this diagnostic path.",
            "The provider has far-field stress, wellbore pressure and tensile strength.",
            "The provider does not have oriented horizontal stresses for Kirsch.",
            "The upgrade must remain opt-in and diagnostic.",
        ],
        "recommended_next_phase": "PHASE_PLAN_ELASTIC_SIGMATHETA_UPGRADE_IMPLEMENTATION",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Elastic sigma-theta upgrade formula decision",
        "",
        f"- formula_decision_status: `{report['formula_decision_status']}`",
        f"- selected_formula: `{report['selected_formula']}`",
        f"- implementation_allowed_next: `{report['implementation_allowed_next']}`",
        f"- physically_validated: `{report['physically_validated']}`",
        f"- legacy_equivalent: `{report['legacy_equivalent']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_change_allowed: `{report['pkn_behavior_change_allowed']}`",
        "",
        "## Decision basis",
        "",
    ]
    lines.extend(f"- {item}" for item in report["decision_basis"])
    lines.extend(["", "## Rejected formulas", ""])
    lines.extend(
        f"- `{item['formula']}`: {item['reason']}"
        for item in report["rejected_formulas"]
    )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide the elastic sigma-theta upgrade formula."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = decide()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.output_md:
        write_markdown(args.output_md, report)
    print(f"phase={report['phase']}")
    print(f"formula_decision_status={report['formula_decision_status']}")
    print(f"selected_formula={report['selected_formula']}")
    print(f"implementation_allowed_next={report['implementation_allowed_next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
