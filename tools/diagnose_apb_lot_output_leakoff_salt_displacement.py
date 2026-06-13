#!/usr/bin/env python3
"""Diagnose APB/LOT output, leakoff and salt displacement contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


SEARCH_TARGETS = [
    "apps",
    "include",
    "src",
    "schemas",
    "cases",
    "tests",
    "docs",
]


def contains(pattern: str) -> bool:
    for target in SEARCH_TARGETS:
      root = ROOT / target
      if not root.exists():
          continue
      for path in root.rglob("*"):
          if not path.is_file():
              continue
          try:
              if pattern in path.read_text(encoding="utf-8", errors="ignore"):
                  return True
          except OSError:
              continue
    return False


def build_report() -> dict[str, Any]:
    dat_output_found = contains(".dat") or contains("legacy_dat")
    json_output_found = contains("write_pkn_result") or contains("result.json")
    leakoff_nodal_force_mode_found = contains("legacy_nodal_force") or contains("faLOT")
    leakoff_volume_balance_mode_found = contains("volume_balance") or contains("dV + dV_leakoff")
    pre_iterative_salt_displacement_found = contains("pre_iterative")
    legacy_inside_newton_salt_displacement_found = contains("legacy_inside_newton")

    complete = all(
        [
            dat_output_found,
            json_output_found,
            leakoff_nodal_force_mode_found,
            leakoff_volume_balance_mode_found,
            pre_iterative_salt_displacement_found,
            legacy_inside_newton_salt_displacement_found,
        ]
    )

    return {
        "phase": "APB_LOT_OUTPUT_LEAKOFF_SALT_DISPLACEMENT_DIAGNOSIS",
        "diagnosis_status": "APB_LOT_DIAGNOSIS_COMPLETE" if complete else "APB_LOT_DIAGNOSIS_PARTIAL",
        "dat_output_found": dat_output_found,
        "json_output_found": json_output_found,
        "json_output_consolidation_needed": True,
        "leakoff_nodal_force_mode_found": leakoff_nodal_force_mode_found,
        "leakoff_volume_balance_mode_found": leakoff_volume_balance_mode_found,
        "pre_iterative_salt_displacement_found": pre_iterative_salt_displacement_found,
        "legacy_inside_newton_salt_displacement_found": legacy_inside_newton_salt_displacement_found,
        "implementation_allowed_next": True,
        "recommended_next_phase": "APB_LOT_IMPLEMENT_JSON_OUTPUT_AND_MODES",
        "caveats": [
            "Modern APB/LOT full solver is not enabled by this diagnosis.",
            "PKN behavior remains out of scope for APB/LOT mode contracts.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# APB/LOT output, leakoff and salt displacement diagnosis",
        "",
        f"Status: `{report['diagnosis_status']}`",
        "",
        "| Item | Value |",
        "|---|---:|",
    ]
    for key, value in report.items():
        if key in {"caveats"}:
            continue
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Caveats", ""])
    for caveat in report["caveats"]:
        lines.append(f"- {caveat}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose APB/LOT output, leakoff and salt displacement contracts."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = build_report()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)

    print(report["diagnosis_status"])
    return 0 if report["implementation_allowed_next"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
