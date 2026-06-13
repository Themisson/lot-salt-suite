#!/usr/bin/env python3
"""Decide APB/LOT modern mode defaults for new cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def decision(opt_in_only: bool = False) -> dict[str, Any]:
    status = (
        "APB_LOT_MODERN_MODES_READY_OPT_IN_ONLY"
        if opt_in_only
        else "APB_LOT_MODERN_MODES_READY_AS_DEFAULT_FOR_NEW_CASES"
    )
    return {
        "phase": "APB_LOT_MODERN_MODES_DEFAULT_DECISION",
        "decision_status": status,
        "default_output_format_for_new_cases": "json",
        "default_output_suffix": "_out.json",
        "default_leakoff_coupling_mode": "volume_balance",
        "default_salt_displacement_mode": "pre_iterative",
        "legacy_modes_preserved": True,
        "pkn_behavior_changed": False,
        "defaults_applied_in_parser": True,
        "recommended_next_phase": "APB_LOT_RUN_EXTENDED_REGRESSION_SUITE",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# APB/LOT modern modes default decision",
        "",
        f"Decision: `{report['decision_status']}`",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for key, value in report.items():
        lines.append(f"| `{key}` | `{value}` |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Decide APB/LOT modern mode defaults.")
    parser.add_argument("--opt-in-only", action="store_true")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = decision(opt_in_only=args.opt_in_only)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)
    print(report["decision_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
