#!/usr/bin/env python3
"""Plan Phase 11.11M sigma-theta source completion for limited_gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11M"
PLAN_STATUS = "LIMITED_GATE_REMAINS_DIAGNOSTIC_SIGMATHETA_SOURCE_PLAN_RECORDED"
NEXT_PHASE = "PHASE11_11N_IMPLEMENT_OR_CONNECT_SIGMATHETA_SOURCE"


def build_plan() -> dict[str, Any]:
    completion_steps = [
        {
            "step": "define_runtime_post_drilling_sigmatheta_source",
            "status": "required",
            "output": "post_drilling_sigma_theta_initial_state",
        },
        {
            "step": "resolve_pressure_semantics",
            "status": "required",
            "output": "wellbore_pressure_reference_for_gate",
        },
        {
            "step": "resolve_sign_convention",
            "status": "required",
            "output": "compression_positive_sigma_theta_contract",
        },
        {
            "step": "resolve_reference_frame",
            "status": "required",
            "output": "wellbore_wall_total_stress_or_documented_alternative",
        },
        {
            "step": "add_controlled_runtime_fixtures",
            "status": "future",
            "output": "fixtures_that_do_not_change_pkn_physics",
        },
    ]
    return {
        "phase": PHASE,
        "plan_status": PLAN_STATUS,
        "implementation_performed": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "limited_gate_status": "DIAGNOSTIC_ONLY",
        "real_sigmatheta_source_status": "MISSING_RUNTIME_SOURCE",
        "blocking_reasons": [
            "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE",
            "MISSING_RUNTIME_SIGMATHETA_CURRENT_SOURCE",
            "PRESSURE_SEMANTICS_NOT_RESOLVED_FOR_REAL_GATE",
            "SIGMATHETA_SIGN_CONVENTION_NOT_RUNTIME_RESOLVED",
            "SIGMATHETA_REFERENCE_FRAME_NOT_RUNTIME_RESOLVED",
        ],
        "completion_steps": completion_steps,
        "required_guards_for_next_phase": [
            "PKN_DEFAULT_RETROCOMPATIBLE",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
            "RESULT_JSON_PHYSICAL_OUTPUT_UNCHANGED",
            "TIMESERIES_CSV_PHYSICAL_OUTPUT_UNCHANGED",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, plan: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11M sigma-theta source completion plan",
        "",
        f"- plan_status: `{plan['plan_status']}`",
        f"- implementation_performed: `{plan['implementation_performed']}`",
        f"- runtime_dispatch_enabled: `{plan['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{plan['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{plan['pkn_behavior_changed']}`",
        f"- penny_shaped_runtime_enabled: `{plan['penny_shaped_runtime_enabled']}`",
        f"- recommended_next_phase: `{plan['recommended_next_phase']}`",
        "",
        "## Blocking Reasons",
        "",
    ]
    lines.extend(f"- `{item}`" for item in plan["blocking_reasons"])
    lines.extend(["", "## Completion Steps", ""])
    for item in plan["completion_steps"]:
        lines.append(
            f"- `{item['step']}`: `{item['status']}` -> `{item['output']}`"
        )
    lines.extend(["", "## Required Guards", ""])
    lines.extend(f"- `{item}`" for item in plan["required_guards_for_next_phase"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan Phase 11.11M sigma-theta source completion for limited_gate."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    plan = build_plan()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, plan)

    print(f"phase={plan['phase']}")
    print(f"plan_status={plan['plan_status']}")
    print(f"implementation_performed={plan['implementation_performed']}")
    print(f"runtime_dispatch_enabled={plan['runtime_dispatch_enabled']}")
    print(f"buz29_execution_allowed={plan['buz29_execution_allowed']}")
    print(f"recommended_next_phase={plan['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
