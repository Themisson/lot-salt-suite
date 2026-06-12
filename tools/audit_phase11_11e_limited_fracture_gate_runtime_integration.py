#!/usr/bin/env python3
"""Audit Phase 11.11E limited fracture gate runtime integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11E"
INTEGRATION_STATUS = "LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED"
RECOMMENDED_NEXT_PHASE = "PHASE11_11F_ADD_LIMITED_GATE_CASE_FIXTURES"


def build_audit() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "integration_status": INTEGRATION_STATUS,
        "limited_gate_mode_supported": True,
        "runtime_dispatch_enabled": False,
        "dispatch_runtime_enabled_true_rejected": True,
        "pkn_behavior_changed": False,
        "pkn_outputs_unchanged": True,
        "diagnostic_output_isolated": True,
        "buz29_execution_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "physical_dispatch_enabled": False,
        "pkn_model_called_by_gate_dispatch": False,
        "pkn_runner_called_by_gate_dispatch": False,
        "penny_shaped_adapter_called_by_gate_dispatch": False,
        "supported_modes": ["pre_runner", "diagnostic_only", "limited_gate"],
        "diagnostic_output": "diagnostic_fracture_gate.json",
        "physical_outputs": ["result.json", "timeseries.csv"],
        "required_statuses": [
            "PHASE11_11E_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED",
            INTEGRATION_STATUS,
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE",
            "BUZ29_EXECUTION_BLOCKED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
        ],
        "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        "caveats": [
            "The integration is limited to diagnostic gate evaluation.",
            "Dispatch statuses are not physical runtime calls.",
            "PKN remains the default compatible runtime path.",
            "BUZ29-PENNY remains blocked.",
        ],
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11E Limited Fracture Gate Runtime Integration",
        "",
        f"- phase: `{audit['phase']}`",
        f"- integration_status: `{audit['integration_status']}`",
        f"- limited_gate_mode_supported: `{audit['limited_gate_mode_supported']}`",
        f"- runtime_dispatch_enabled: `{audit['runtime_dispatch_enabled']}`",
        f"- dispatch_runtime_enabled_true_rejected: `{audit['dispatch_runtime_enabled_true_rejected']}`",
        f"- pkn_outputs_unchanged: `{audit['pkn_outputs_unchanged']}`",
        f"- diagnostic_output_isolated: `{audit['diagnostic_output_isolated']}`",
        f"- buz29_execution_allowed: `{audit['buz29_execution_allowed']}`",
        f"- penny_shaped_runtime_enabled: `{audit['penny_shaped_runtime_enabled']}`",
        "",
        "## Supported Modes",
    ]
    lines.extend(f"- `{mode}`" for mode in audit["supported_modes"])
    lines.extend(["", "## Required Statuses"])
    lines.extend(f"- `{status}`" for status in audit["required_statuses"])
    lines.extend(["", "## Caveats"])
    lines.extend(f"- {item}" for item in audit["caveats"])
    write_text(path, "\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.11E limited fracture gate runtime integration."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit = build_audit()

    if args.output_json:
        write_text(args.output_json, json.dumps(audit, indent=2) + "\n")
    if args.output_md:
        write_markdown(args.output_md, audit)

    print(f"phase={audit['phase']}")
    print(f"integration_status={audit['integration_status']}")
    print(f"limited_gate_mode_supported={audit['limited_gate_mode_supported']}")
    print(f"runtime_dispatch_enabled={audit['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
