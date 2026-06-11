#!/usr/bin/env python3
"""Plan non-PKN model work after the BUZ29-VISCO first-well audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


PHASE = "11.6B"
STATUS = "NON_PKN_MODEL_ROADMAP_RECORDED"


def build_plan(preferred_track: str = "penny_shaped") -> dict:
    tracks = [
        {
            "track": "penny_shaped",
            "priority": 1,
            "driver": "BUZ29_VISCO_FIRST_WELL",
            "objective": "Audit and design a modern penny-shaped LOT model before any BUZ29 YAML migration.",
            "precondition": "Document legacy penny-shaped formulation and required outputs.",
            "expected_output": "Penny-shaped formulation audit and implementation gate.",
            "status": "PLANNED",
            "risk": "High if forced through the existing PKN runner.",
        },
        {
            "track": "kgd_circular_elliptical",
            "priority": 2,
            "driver": "BUZ29_ZAMORA_AND_OTHER_BUZ29_VARIANTS",
            "objective": "Audit circular/elliptical KGD branches and decide whether they need modern support.",
            "precondition": "Separate KGD mechanics from Zamora/compositional fluid effects.",
            "expected_output": "KGD/circular model feasibility decision.",
            "status": "PLANNED_OPTIONAL",
            "risk": "Medium; model family may not be needed for immediate modern-refined validation.",
        },
        {
            "track": "zamora_compositional_fluid",
            "priority": 3,
            "driver": "BUZ29_ZAMORA_VARIANTS",
            "objective": "Keep Zamora/compositional fluid outside LOT/PKN until a dedicated fluid-model gate exists.",
            "precondition": "Define fluid state variables, units and parser contract.",
            "expected_output": "Zamora fluid roadmap, not runtime coupling.",
            "status": "BLOCKED_BY_FORMULATION_GATE",
            "risk": "High if mixed with fracture model migration.",
        },
        {
            "track": "legacy_output_provenance",
            "priority": 4,
            "driver": "BUZ29_PKN_OUTPUT_ONLY_ARTIFACTS",
            "objective": "Audit provenance of BUZ29 PKN .dat outputs before using them as references.",
            "precondition": "Find exact source or build script that produced PKN outputs.",
            "expected_output": "Decision whether BUZ29 PKN outputs can inform a future case.",
            "status": "PLANNED",
            "risk": "Medium; output-only evidence can mislead migration.",
        },
        {
            "track": "modern_refined_buz67d_continuation",
            "priority": 5,
            "driver": "BUZ67D_MODERN_REFINED",
            "objective": "Continue BUZ67D parametric infrastructure while non-PKN support remains out of runtime.",
            "precondition": "No new fracture solver required.",
            "expected_output": "Stable sensitivity reports and summaries.",
            "status": "AVAILABLE_NOW",
            "risk": "Low; remains diagnostic and documented.",
        },
    ]
    valid_tracks = {track["track"] for track in tracks}
    if preferred_track not in valid_tracks:
        preferred_track = "penny_shaped"
    return {
        "phase": PHASE,
        "status": STATUS,
        "source": "DOCUMENTED_PHASE11_6A_AUDIT",
        "drivers": ["BUZ29_VISCO_FIRST_WELL", "BUZ29_ZAMORA_VARIANTS", "BUZ29_PKN_OUTPUT_ONLY_ARTIFACTS"],
        "gate_inputs": {
            "phase11_6a_primary_classification": "BUZ29_VISCO_FIRST_WELL_NOT_PKN",
            "phase11_6a_future_yaml_readiness": "BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY",
            "pkn_line_status": "COMMENT_ONLY",
            "active_first_well_model": "PENNY_SHAPED",
        },
        "tracks": tracks,
        "recommended_next_phase": "PHASE11_6C_PENNY_SHAPED_FORMULATION_AUDIT",
        "preferred_track": preferred_track,
        "blocking_gates": [
            "NON_PKN_FORMULATION_NOT_IMPLEMENTED",
            "BUZ29_PKN_OUTPUT_PROVENANCE_NOT_ESTABLISHED",
            "ZAMORA_FLUID_MODEL_OUT_OF_SCOPE",
        ],
        "forbidden_shortcuts": [
            "Do not convert BUZ29 penny-shaped to PKN by parameter inference.",
            "Do not create BUZ29 modern YAML from output-only PKN artifacts.",
            "Do not mix Zamora fluid with fracture model migration in the same gate.",
        ],
    }


def write_markdown(path: Path, plan: dict) -> None:
    lines = [
        "# Phase 11.6B non-PKN model roadmap",
        "",
        "## Summary",
        "",
        f"- `status`: `{plan['status']}`",
        f"- `source`: `{plan['source']}`",
        f"- `recommended_next_phase`: `{plan['recommended_next_phase']}`",
        f"- `preferred_track`: `{plan['preferred_track']}`",
        "",
        "## Gate inputs",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in plan["gate_inputs"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Tracks", "", "| Priority | Track | Driver | Status | Objective |", "|---:|---|---|---|---|"])
    for track in plan["tracks"]:
        lines.append(
            f"| {track['priority']} | `{track['track']}` | `{track['driver']}` | `{track['status']}` | {track['objective']} |"
        )
    lines.extend(["", "## Blocking gates", ""])
    for gate in plan["blocking_gates"]:
        lines.append(f"- `{gate}`")
    lines.extend(["", "## Forbidden shortcuts", ""])
    for shortcut in plan["forbidden_shortcuts"]:
        lines.append(f"- {shortcut}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preferred-track", default="penny_shaped")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    plan = build_plan(args.preferred_track)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, plan)
    print(f"PHASE={plan['phase']}")
    print(f"STATUS={plan['status']}")
    print(f"NEXT_PHASE={plan['recommended_next_phase']}")
    print(f"PREFERRED_TRACK={plan['preferred_track']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
