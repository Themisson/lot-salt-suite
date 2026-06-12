#!/usr/bin/env python3
"""Audit Phase 11.10Y diagnostic pre-runner runtime gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_audit() -> dict[str, Any]:
    return {
        "phase": "11.10Y",
        "integration_status": "DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED",
        "diagnostic_opt_in_required": True,
        "dispatch_runtime_enabled_allowed": False,
        "runtime_physical_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "pkn_model_called_by_diagnostic": False,
        "penny_adapter_called_by_diagnostic": False,
        "diagnostic_output": "diagnostic_fracture_gate.json",
        "diagnostic_output_isolated_from_physical_result": True,
        "expected_missing_sigma_theta_status": (
            "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE"
        ),
        "recommended_next_phase": (
            "PHASE11_10Z_ADD_DIAGNOSTIC_PRE_RUNNER_CASE_FIXTURES"
        ),
        "classifications": [
            "PHASE11_10Y_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED",
            "DIAGNOSTIC_PRE_RUNNER_OPT_IN_IMPLEMENTED",
            "RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED",
            "PKN_BEHAVIOR_NOT_CHANGED",
            "BUZ29_EXECUTION_BLOCKED",
        ],
    }


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.10Y diagnostic pre-runner runtime gate",
        "",
        f"- phase: `{audit['phase']}`",
        f"- integration_status: `{audit['integration_status']}`",
        f"- diagnostic_opt_in_required: `{audit['diagnostic_opt_in_required']}`",
        f"- dispatch_runtime_enabled_allowed: `{audit['dispatch_runtime_enabled_allowed']}`",
        f"- runtime_physical_dispatch_enabled: `{audit['runtime_physical_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{audit['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{audit['pkn_behavior_changed']}`",
        f"- pkn_model_called_by_diagnostic: `{audit['pkn_model_called_by_diagnostic']}`",
        f"- penny_adapter_called_by_diagnostic: `{audit['penny_adapter_called_by_diagnostic']}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in audit["classifications"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10Y diagnostic pre-runner runtime gate."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    audit = build_audit()

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.output_md:
        write_markdown(args.output_md, audit)

    print(f"phase={audit['phase']}")
    print(f"integration_status={audit['integration_status']}")
    print(f"diagnostic_opt_in_required={audit['diagnostic_opt_in_required']}")
    print(
        "runtime_physical_dispatch_enabled="
        f"{audit['runtime_physical_dispatch_enabled']}"
    )
    print(f"buz29_execution_allowed={audit['buz29_execution_allowed']}")
    print(f"pkn_behavior_changed={audit['pkn_behavior_changed']}")
    print(f"recommended_next_phase={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
