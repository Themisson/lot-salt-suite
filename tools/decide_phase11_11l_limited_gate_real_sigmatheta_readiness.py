#!/usr/bin/env python3
"""Decide Phase 11.11L limited_gate real sigma-theta readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11L"
READINESS_STATUS = "LIMITED_GATE_REMAINS_DIAGNOSTIC_BLOCKED_BY_REAL_SOURCE"
NEXT_PHASE = "PHASE11_11M_KEEP_LIMITED_GATE_DIAGNOSTIC_AND_PLAN_SIGMATHETA_SOURCE"


def build_decision() -> dict[str, Any]:
    checks = {
        "sigma_theta_initial_runtime_available": False,
        "sigma_theta_current_runtime_available": False,
        "wellbore_pressure_runtime_available": True,
        "pressure_semantics_resolved": False,
        "sign_convention_resolved": False,
        "reference_frame_resolved": False,
        "pkn_behavior_changed": False,
        "runtime_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
    }
    return {
        "phase": PHASE,
        "readiness_status": READINESS_STATUS,
        "implementation_allowed_next": False,
        "runtime_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "decision_checks": checks,
        "blocking_reasons": [
            "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE",
            "MISSING_RUNTIME_SIGMATHETA_CURRENT_SOURCE",
            "PRESSURE_SEMANTICS_NOT_RESOLVED_FOR_REAL_GATE",
            "SIGMATHETA_SIGN_CONVENTION_NOT_RUNTIME_RESOLVED",
            "SIGMATHETA_REFERENCE_FRAME_NOT_RUNTIME_RESOLVED",
        ],
        "evidence": [
            "LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE",
            "REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED",
            "RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED",
            "POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED_BUT_SOURCE_MISSING",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, decision: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11L limited_gate real sigma-theta readiness",
        "",
        f"- readiness_status: `{decision['readiness_status']}`",
        f"- implementation_allowed_next: `{decision['implementation_allowed_next']}`",
        f"- runtime_dispatch_allowed_next: `{decision['runtime_dispatch_allowed_next']}`",
        f"- buz29_execution_allowed_next: `{decision['buz29_execution_allowed_next']}`",
        f"- pkn_behavior_change_allowed: `{decision['pkn_behavior_change_allowed']}`",
        f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
        "",
        "## Decision Checks",
        "",
    ]
    lines.extend(f"- `{key}` = `{value}`" for key, value in decision["decision_checks"].items())
    lines.extend(["", "## Blocking Reasons", ""])
    lines.extend(f"- `{item}`" for item in decision["blocking_reasons"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.11L limited_gate real sigma-theta readiness."
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
    print(f"implementation_allowed_next={decision['implementation_allowed_next']}")
    print(f"runtime_dispatch_allowed_next={decision['runtime_dispatch_allowed_next']}")
    print(f"buz29_execution_allowed_next={decision['buz29_execution_allowed_next']}")
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
