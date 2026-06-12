#!/usr/bin/env python3
"""Decide Phase 11.11C runtime wiring readiness after diagnostic regressions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11C"
READINESS_STATUS = "RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC"
RECOMMENDED_NEXT_PHASE = "PHASE11_11D_SPECIFY_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION"


def decision() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "readiness_status": READINESS_STATUS,
        "pkn_regression_safe": True,
        "diagnostic_output_isolated": True,
        "controlled_cases_valid": True,
        "guards_available": True,
        "runtime_dispatch_allowed": False,
        "runtime_physical_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_runtime_allowed": False,
        "implementation_scope_next": "limited_runtime_gate_specification_only",
        "evidence": {
            "phase11_11a": "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID",
            "phase11_11b": "PKN_OUTPUTS_UNCHANGED_WITH_DIAGNOSTICS",
            "diagnostic_output": "diagnostic_fracture_gate.json",
        },
        "required_statuses": [
            "PHASE11_11C_RUNTIME_WIRING_READINESS_DECIDED",
            READINESS_STATUS,
            "PKN_REGRESSION_SAFE_FOR_DIAGNOSTIC_PRE_RUNNER",
            "RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
        ],
        "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        "caveats": [
            "Readiness is limited to specifying the next gate, not enabling physical dispatch.",
            "PKN outputs were proven unchanged only for the controlled protected cases.",
            "PENNY_SHAPED remains diagnostic-only.",
            "BUZ29-PENNY remains blocked.",
        ],
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11C Runtime Wiring Readiness Decision",
        "",
        f"- phase: `{data['phase']}`",
        f"- readiness_status: `{data['readiness_status']}`",
        f"- pkn_regression_safe: `{data['pkn_regression_safe']}`",
        f"- diagnostic_output_isolated: `{data['diagnostic_output_isolated']}`",
        f"- runtime_dispatch_allowed: `{data['runtime_dispatch_allowed']}`",
        f"- buz29_execution_allowed: `{data['buz29_execution_allowed']}`",
        f"- recommended_next_phase: `{data['recommended_next_phase']}`",
        "",
        "## Caveats",
    ]
    lines.extend(f"- {item}" for item in data["caveats"])
    write_text(path, "\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.11C limited runtime wiring readiness."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = decision()
    if args.output_json:
        write_text(args.output_json, json.dumps(data, indent=2) + "\n")
    if args.output_md:
        write_markdown(args.output_md, data)
    print(f"phase={data['phase']}")
    print(f"readiness_status={data['readiness_status']}")
    print(f"recommended_next_phase={data['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
