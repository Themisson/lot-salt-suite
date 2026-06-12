#!/usr/bin/env python3
"""Specify Phase 11.11K post-drilling initial state integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11K"
INTEGRATION_STATUS = "POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED_BUT_SOURCE_MISSING"
NEXT_PHASE = "PHASE11_11L_DECIDE_LIMITED_GATE_REAL_SIGMATHETA_READINESS"


def build_spec() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "integration_status": INTEGRATION_STATUS,
        "contract": "PostDrillingInitialState",
        "required_fields": [
            "sigma_theta_initial_compression_positive_Pa",
            "sigma_theta_current_compression_positive_Pa",
            "source",
            "state_time",
            "sign_convention",
            "reference_frame",
            "pressure_reference",
            "is_total_stress",
            "physically_validated",
        ],
        "requires_post_drilling_state": True,
        "state_time": "POST_DRILLING_BEFORE_LOT",
        "sign_convention": "COMPRESSION_POSITIVE",
        "reference_frame": "WELLBORE_WALL_TOTAL_STRESS",
        "pressure_reference": "WELLBORE_PRESSURE",
        "is_total_stress": True,
        "physically_validated": False,
        "source_status": "MISSING_RUNTIME_SIGMATHETA_SOURCE",
        "implementation_allowed_next": False,
        "runtime_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, spec: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11K post-drilling initial state integration",
        "",
        f"- integration_status: `{spec['integration_status']}`",
        f"- contract: `{spec['contract']}`",
        f"- state_time: `{spec['state_time']}`",
        f"- sign_convention: `{spec['sign_convention']}`",
        f"- reference_frame: `{spec['reference_frame']}`",
        f"- pressure_reference: `{spec['pressure_reference']}`",
        f"- source_status: `{spec['source_status']}`",
        f"- implementation_allowed_next: `{spec['implementation_allowed_next']}`",
        f"- runtime_dispatch_allowed_next: `{spec['runtime_dispatch_allowed_next']}`",
        f"- buz29_execution_allowed_next: `{spec['buz29_execution_allowed_next']}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Required Fields",
        "",
    ]
    lines.extend(f"- `{item}`" for item in spec["required_fields"])
    lines.extend(
        [
            "",
            "The post-drilling initial state must represent the condition before "
            "the LOT starts, not a null state created at the first test step.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.11K post-drilling initial state integration."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    spec = build_spec()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(spec, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, spec)

    print(f"phase={spec['phase']}")
    print(f"integration_status={spec['integration_status']}")
    print(f"state_time={spec['state_time']}")
    print(f"source_status={spec['source_status']}")
    print(f"implementation_allowed_next={spec['implementation_allowed_next']}")
    print(f"runtime_dispatch_allowed_next={spec['runtime_dispatch_allowed_next']}")
    print(f"recommended_next_phase={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
