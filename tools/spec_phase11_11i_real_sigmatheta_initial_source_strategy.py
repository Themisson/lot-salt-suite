#!/usr/bin/env python3
"""Specify Phase 11.11I real sigma-theta initial source strategy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11I"
STRATEGY_STATUS = "REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED"
PRIMARY_SOURCE = "ELASTIC_INITIAL_WELLBORE_STATE"
FALLBACK_SOURCES = ["EXPLICIT_DIAGNOSTIC_INPUT", "SYNTHETIC_FIXTURE"]
NEXT_PHASE = "PHASE11_11J_AUDIT_RUNTIME_SIGMATHETA_AND_PRESSURE_AVAILABILITY"


def build_strategy() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "strategy_status": STRATEGY_STATUS,
        "primary_source": PRIMARY_SOURCE,
        "fallback_sources": FALLBACK_SOURCES,
        "candidate_sources": [
            "ELASTIC_INITIAL_WELLBORE_STATE",
            "APB_SALT_COUPLED_STATE",
            "LEGACY_DIAGNOSTIC_TRACE",
            "EXPLICIT_DIAGNOSTIC_INPUT",
            "SYNTHETIC_FIXTURE",
            "UNKNOWN",
        ],
        "not_validation_sources": ["LEGACY_DIAGNOSTIC_TRACE"],
        "requires_post_drilling_state": True,
        "lot_time_zero_is_not_drilling_time_zero": True,
        "legacy_trace_validation_allowed": False,
        "sign_convention": "COMPRESSION_POSITIVE",
        "reference_frame": "WELLBORE_WALL_TOTAL_STRESS",
        "state_time": "POST_DRILLING_BEFORE_LOT",
        "implementation_allowed_next": False,
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, strategy: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11I real sigma-theta initial source strategy",
        "",
        f"- strategy_status: `{strategy['strategy_status']}`",
        f"- primary_source: `{strategy['primary_source']}`",
        f"- fallback_sources: `{', '.join(strategy['fallback_sources'])}`",
        f"- requires_post_drilling_state: `{strategy['requires_post_drilling_state']}`",
        "- lot_time_zero_is_not_drilling_time_zero: "
        f"`{strategy['lot_time_zero_is_not_drilling_time_zero']}`",
        f"- legacy_trace_validation_allowed: `{strategy['legacy_trace_validation_allowed']}`",
        f"- implementation_allowed_next: `{strategy['implementation_allowed_next']}`",
        f"- recommended_next_phase: `{strategy['recommended_next_phase']}`",
        "",
        "## Candidate Sources",
        "",
    ]
    lines.extend(f"- `{item}`" for item in strategy["candidate_sources"])
    lines.extend(
        [
            "",
            "## Required Premise",
            "",
            "The LOT initial state must represent the post-drilling state at the "
            "wellbore wall, not a null stress state created at the first LOT step.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.11I real sigma-theta initial source strategy."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    strategy = build_strategy()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(strategy, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, strategy)

    print(f"phase={strategy['phase']}")
    print(f"strategy_status={strategy['strategy_status']}")
    print(f"primary_source={strategy['primary_source']}")
    print(
        "lot_time_zero_is_not_drilling_time_zero="
        f"{strategy['lot_time_zero_is_not_drilling_time_zero']}"
    )
    print(f"implementation_allowed_next={strategy['implementation_allowed_next']}")
    print(f"recommended_next_phase={strategy['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
