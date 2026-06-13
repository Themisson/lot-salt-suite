#!/usr/bin/env python3
"""Decide readiness of the diagnostic PostDrillingSigmaThetaProvider path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


READINESS_STATUS = "SIGMATHETA_PROVIDER_READY_FOR_DIAGNOSTIC_RUNTIME_USE"
NEXT_PHASE = "PHASE_IMPLEMENT_ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE"


def build_decision() -> dict[str, Any]:
    evidence = [
        {
            "phase": "master-A",
            "status": "SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE",
            "meaning": "root cause isolated to missing sigma-theta source",
        },
        {
            "phase": "master-B",
            "status": "SIGMATHETA_SOURCE_SOLUTION_PLAN_READY",
            "meaning": "PostDrillingSigmaThetaProvider selected",
        },
        {
            "phase": "master-C",
            "status": "POST_DRILLING_SIGMATHETA_PROVIDER_IMPLEMENTED",
            "meaning": "provider implemented as diagnostic component",
        },
        {
            "phase": "master-D",
            "status": "SIGMATHETA_PROVIDER_WIRED_TO_DIAGNOSTIC_PRE_RUNNER",
            "meaning": "provider feeds FractureGateDiagnosticPreRunner",
        },
        {
            "phase": "master-E",
            "status": "SIGMATHETA_PROVIDER_CONTROLLED_CASES_VALID",
            "meaning": "controlled fixtures cover ready/reached/rejected cases",
        },
    ]
    return {
        "phase": "master-F",
        "readiness_status": READINESS_STATUS,
        "ready_for_diagnostic_runtime_use": True,
        "ready_for_physical_dispatch": False,
        "ready_for_physical_validation": False,
        "ready_for_real_source_extension": True,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "legacy_equivalence_claimed": False,
        "provider_component": "PostDrillingSigmaThetaProvider",
        "current_sources": [
            "EXPLICIT_DIAGNOSTIC_INPUT",
            "SYNTHETIC_FIXTURE",
            "ELASTIC_INITIAL_WELLBORE_STATE",
        ],
        "diagnostic_guards": [
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PKN_BEHAVIOR_NOT_CHANGED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
            "NO_LEGACY_EQUIVALENCE_CLAIM",
        ],
        "remaining_blockers": [
            "NO_PHYSICAL_SIGMATHETA_RUNTIME_SOURCE_CONSUMED_YET",
            "NO_SALT_WALL_STRESS_RUNTIME_WIRING",
            "NO_BUZ29_PHYSICAL_EXECUTION_ALLOWED",
        ],
        "evidence": evidence,
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, decision: dict[str, Any]) -> None:
    lines = [
        "# Master Phase F sigma-theta provider readiness decision",
        "",
        f"- readiness_status: `{decision['readiness_status']}`",
        f"- ready_for_diagnostic_runtime_use: `{decision['ready_for_diagnostic_runtime_use']}`",
        f"- ready_for_physical_dispatch: `{decision['ready_for_physical_dispatch']}`",
        f"- ready_for_real_source_extension: `{decision['ready_for_real_source_extension']}`",
        f"- runtime_dispatch_enabled: `{decision['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{decision['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{decision['pkn_behavior_changed']}`",
        f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
        "",
        "## Evidence",
        "",
    ]
    for item in decision["evidence"]:
        lines.append(f"- `{item['phase']}`: `{item['status']}` — {item['meaning']}")
    lines.extend(["", "## Remaining Blockers", ""])
    lines.extend(f"- `{item}`" for item in decision["remaining_blockers"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide readiness of the diagnostic PostDrillingSigmaThetaProvider path."
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
        "ready_for_diagnostic_runtime_use="
        f"{decision['ready_for_diagnostic_runtime_use']}"
    )
    print(f"ready_for_physical_dispatch={decision['ready_for_physical_dispatch']}")
    print(f"runtime_dispatch_enabled={decision['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

