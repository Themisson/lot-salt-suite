#!/usr/bin/env python3
"""Summarize Phase 10 closure and Stage 11 handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


PHASE10_SUMMARY = {
    "phase": 10,
    "status": "PHASE10_CLOSED_READY_FOR_STAGE11",
    "source": "DOCUMENTED_PHASE_SUMMARY",
    "primary_artifact": "BUZ67D_MODERN_REFINED_REPRODUCIBLE_PACKAGE",
    "stage11_recommendation": "STAGE11_PARAMETRIC_INFRASTRUCTURE",
    "modern_refined_status": "BUZ67D_MODERN_REFINED_REPRODUCIBLE_PACKAGE",
    "legacy_equivalence_status": "SEPARATE_TRACK_BLOCKED_BY_APBSALT1D_GEOMETRY",
    "canonical_commands": [
        "cmake -S . -B build",
        "cmake --build build --config Debug -j",
        "python tools/run_buz67d_modern_refined_package.py --lot-sim build/Debug/lot-sim.exe --output-dir results/comparison/buz67d_modern_refined_package",
        "python tools/run_lot_pkn_sensitivity_matrix.py --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml --output-dir results/comparison/buz67d_cgeom_matrix",
        "python tools/report_lot_pkn_sensitivity_matrix.py --summary results/comparison/buz67d_cgeom_matrix/summary.csv --metadata results/comparison/buz67d_cgeom_matrix/metadata.json --output-json results/comparison/buz67d_cgeom_report.json --output-md results/comparison/buz67d_cgeom_report.md --legacy-opening-time-s 510 --legacy-max-pressure-Pa 69035836.1743195",
    ],
    "blocked_items": [
        "APBSalt1D sampling bridge remains blocked without spatial sigmaTheta samples.",
        "sigmaTheta runtime real provider is future work.",
        "pressure_tabulated_geometric remains blocked.",
        "Strict LOT_Tese legacy-equivalence remains blocked until geometry/sampling are consumed.",
        "C_geom 0.75x is diagnostic sensitivity, not automatic calibration.",
    ],
    "risk_register": [
        "Modern-refined results can be misread as strict LOT_Tese regression if caveats are removed.",
        "Best diagnostic C_geom factor requires independent physical criteria before calibration use.",
        "Generated results/ artifacts are reproducible local outputs and must not be committed.",
        "BUZ-29D is audited but not ready as a modern PKN YAML case.",
    ],
    "definition_of_done": [
        "BUZ-67D modern-refined package is reproducible end-to-end.",
        "Versioned sensitivity matrix and runner exist.",
        "Sensitivity report generator exists.",
        "Known non-equivalence gates are documented.",
        "Stage 11 is ready to focus on parametric infrastructure.",
    ],
}


def phase10_summary() -> dict:
    return dict(PHASE10_SUMMARY)


def write_markdown(path: Path, summary: dict) -> None:
    lines = [
        "# Phase 10 closure summary",
        "",
        f"- phase: `{summary['phase']}`",
        f"- status: `{summary['status']}`",
        f"- source: `{summary['source']}`",
        f"- primary_artifact: `{summary['primary_artifact']}`",
        f"- stage11_recommendation: `{summary['stage11_recommendation']}`",
        "",
        "## Canonical Commands",
        "",
    ]
    lines.extend(f"- `{command}`" for command in summary["canonical_commands"])
    lines.extend(["", "## Blocked Items", ""])
    lines.extend(f"- {item}" for item in summary["blocked_items"])
    lines.extend(["", "## Risk Register", ""])
    lines.extend(f"- {item}" for item in summary["risk_register"])
    lines.extend(["", "## Definition of Done", ""])
    lines.extend(f"- {item}" for item in summary["definition_of_done"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = phase10_summary()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, summary)
    print(f"PHASE={summary['phase']}")
    print(f"STATUS={summary['status']}")
    print(f"PRIMARY_ARTIFACT={summary['primary_artifact']}")
    print(f"STAGE11_RECOMMENDATION={summary['stage11_recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
