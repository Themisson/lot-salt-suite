#!/usr/bin/env python3
"""Decide the post-BUZ29 priority track for the first non-PKN model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


PHASE = "11.7A"
STATUS = "NEXT_MODEL_TRACK_SELECTED"
SELECTED_TRACK = "PENNY_SHAPED"


def build_decision() -> dict:
    candidate_tracks = [
        {
            "track": "PENNY_SHAPED",
            "status": "SELECTED",
            "reason": "BUZ29-VISCO-first-well uses active penny-shaped LOT; the PKN line is commented.",
        },
        {
            "track": "BUZ29_PKN_YAML",
            "status": "BLOCKED",
            "reason": "BUZ29 is not PKN-ready; PKN evidence is comment-only or output-only.",
        },
        {
            "track": "KGD_CIRCULAR",
            "status": "DEFERRED",
            "reason": "KGD/circular appears in related variants but is not the active first-well driver.",
        },
        {
            "track": "KGD_ELLIPTICAL",
            "status": "DEFERRED",
            "reason": "Elliptical/KGD remains a separate optional route.",
        },
        {
            "track": "ZAMORA_COMPOSITIONAL_FLUID",
            "status": "BLOCKED",
            "reason": "Zamora/compositional fluid requires a dedicated fluid-model gate.",
        },
    ]
    blocked_tracks = [track for track in candidate_tracks if track["status"] == "BLOCKED"]
    return {
        "phase": PHASE,
        "status": STATUS,
        "source": "DOCUMENTED_PHASE11_6A_AND_11_6B_SUMMARY",
        "buz29_classification": "BUZ29_VISCO_FIRST_WELL_NOT_PKN",
        "modern_pkn_ready": False,
        "candidate_tracks": candidate_tracks,
        "selected_track": SELECTED_TRACK,
        "selection_reason": (
            "The audited BUZ29 first-well source is present and its active LOT model is "
            "penny-shaped. Selecting PENNY_SHAPED avoids forcing a PKN YAML from a "
            "commented line or output-only evidence."
        ),
        "blocked_tracks": blocked_tracks,
        "required_evidence_for_next_phase": [
            "legacy penny-shaped source locations",
            "net-pressure, radius/volume and leakoff relations",
            "required inputs and SI units",
            "minimum outputs for a modern isolated model",
            "explicit caveat that no BUZ29 physical validation is claimed",
        ],
        "recommended_next_phase": "PHASE11_7B_LEGACY_MATH_AUDIT_SELECTED_MODEL",
        "caveats": [
            "Phase 11.7A selects a technical priority track only.",
            "No new physical model is implemented in this phase.",
            "No BUZ29 physical validation or legacy equivalence is claimed.",
        ],
    }


def write_markdown(path: Path, decision: dict) -> None:
    lines = [
        "# Phase 11.7A next model track decision",
        "",
        "## Summary",
        "",
        f"- `phase`: `{decision['phase']}`",
        f"- `status`: `{decision['status']}`",
        f"- `selected_track`: `{decision['selected_track']}`",
        f"- `recommended_next_phase`: `{decision['recommended_next_phase']}`",
        "",
        "A decisão da 11.7A seleciona uma trilha técnica prioritária. Ela não implementa modelo físico novo e não declara validação física do BUZ29.",
        "",
        "## Evidence considered",
        "",
        "- `docs/57_buz29_visco_first_well_audit.md`: BUZ29 first-well is present but not PKN.",
        "- `docs/58_non_pkn_model_roadmap.md`: penny-shaped is the priority non-PKN route.",
        "- `docs/59_summary_fracture_leakoff_maxima.md`: summaries are ready for future diagnostics.",
        "- `docs/56_buz67d_modern_refined_sensitivity_consolidation.md`: BUZ-67D remains the executable LOT/PKN path.",
        "- `docs/44_stage11_parametric_infrastructure_plan.md`: Stage 11 infrastructure remains diagnostic.",
        "",
        "## Candidate tracks",
        "",
        "| Track | Status | Reason |",
        "|---|---|---|",
    ]
    for track in decision["candidate_tracks"]:
        lines.append(f"| `{track['track']}` | `{track['status']}` | {track['reason']} |")
    lines.extend(
        [
            "",
            "## Selected track",
            "",
            f"`{decision['selected_track']}`",
            "",
            decision["selection_reason"],
            "",
            "## Required evidence for 11.7B",
            "",
        ]
    )
    for item in decision["required_evidence_for_next_phase"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Caveats", ""])
    for caveat in decision["caveats"]:
        lines.append(f"- {caveat}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision = build_decision()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, decision)
    print(f"PHASE={decision['phase']}")
    print(f"STATUS={decision['status']}")
    print(f"SELECTED_TRACK={decision['selected_track']}")
    print(f"NEXT_PHASE={decision['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
