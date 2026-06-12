#!/usr/bin/env python3
"""Decide Phase 11.11H limited_gate runtime readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11H"
READINESS_STATUS = "LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE"
NEXT_PHASE = "PHASE11_11I_SPECIFY_REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY"


def build_decision() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "readiness_status": READINESS_STATUS,
        "ready_for_diagnostic_runtime_use": True,
        "ready_for_physical_dispatch": False,
        "pkn_outputs_unchanged": True,
        "diagnostic_output_isolated": True,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "evidence": [
            "LIMITED_GATE_FIXTURES_VALID",
            "LIMITED_GATE_CONTROLLED_CASES_VALID",
            "PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE",
            "DIAGNOSTIC_OUTPUT_ISOLATED",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
        ],
        "limits": [
            "Physical dispatch remains disabled.",
            "PENNY_SHAPED remains diagnostic-only.",
            "BUZ29-PENNY remains blocked.",
            "No physical legacy equivalence is claimed.",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, decision: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11H limited_gate runtime readiness",
        "",
        f"- readiness_status: `{decision['readiness_status']}`",
        f"- ready_for_diagnostic_runtime_use: `{decision['ready_for_diagnostic_runtime_use']}`",
        f"- ready_for_physical_dispatch: `{decision['ready_for_physical_dispatch']}`",
        f"- pkn_outputs_unchanged: `{decision['pkn_outputs_unchanged']}`",
        f"- diagnostic_output_isolated: `{decision['diagnostic_output_isolated']}`",
        f"- runtime_dispatch_enabled: `{decision['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{decision['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{decision['pkn_behavior_changed']}`",
        f"- penny_shaped_runtime_enabled: `{decision['penny_shaped_runtime_enabled']}`",
        f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{item}`" for item in decision["evidence"])
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in decision["limits"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.11H limited_gate runtime readiness."
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
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
