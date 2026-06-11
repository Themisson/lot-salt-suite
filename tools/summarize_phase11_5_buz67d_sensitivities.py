#!/usr/bin/env python3
"""Summarize Phase 11.5 BUZ-67D modern-refined sensitivity studies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


STATUS_OK = "BUZ67D_MODERN_REFINED_SENSITIVITIES_CONSOLIDATED"


def build_report() -> dict:
    return {
        "phase": "11.5C",
        "status": STATUS_OK,
        "source": "DOCUMENTED_PHASE_SUMMARY",
        "cgeom_extended": {
            "study_id": "buz67d_cgeom_extended_sensitivity_v2",
            "classification": "CGEOM_EXTENDED_SENSITIVITY_ANALYZED",
            "best_by_opening_time": "cgeom_075_next_step",
            "best_by_max_pressure": "cgeom_055_next_step",
            "best_by_combined_score": "cgeom_075_next_step",
        },
        "cgeom_sink_timing": {
            "study_id": "buz67d_cgeom_sink_timing_sensitivity_v2",
            "classification": "CGEOM_SINK_TIMING_MATRIX_ANALYZED",
            "scenario_count": 8,
            "mean_opening_delta_next_minus_same_s": 0.0,
            "mean_sink_delay_delta_next_minus_same_s": 30.0,
            "mean_max_pressure_delta_next_minus_same_Pa": 1821956.0465000253,
            "sink_delay_reproduced_where_expected": True,
        },
        "interpretation": {
            "cgeom_effect": (
                "C_geom controls apparent stiffness, maximum pressure and opening chronology in the "
                "BUZ-67D modern-refined diagnostic studies."
            ),
            "sink_timing_effect": (
                "sink_timing mainly controls whether the positive fracture/leakoff sink is consumed in "
                "the opening step or in the following 30 s step."
            ),
            "ranking_caveat": (
                "C_geom=0.75x is the best combined diagnostic ranking while C_geom=0.55x is the best "
                "maximum-pressure ranking; this metric dependence blocks automatic calibration."
            ),
            "caveat": "diagnostic only; not physical calibration",
        },
        "missing_fields_for_future_analysis": [
            "fracture_volume_max_m3",
            "leakoff_volume_max_m3",
            "fracture_length_max_m",
            "fracture_width_max_m",
            "net_pressure_max_Pa",
        ],
        "recommended_next_phase": "PHASE11_6A_BUZ29_VISCO_FIRST_WELL_AUDIT",
    }


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Phase 11.5C BUZ-67D Modern-Refined Sensitivity Consolidation",
        "",
        f"- status: `{report['status']}`",
        f"- source: `{report['source']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## C_geom Extended Study",
        "",
        f"- study_id: `{report['cgeom_extended']['study_id']}`",
        f"- classification: `{report['cgeom_extended']['classification']}`",
        f"- best_by_opening_time: `{report['cgeom_extended']['best_by_opening_time']}`",
        f"- best_by_max_pressure: `{report['cgeom_extended']['best_by_max_pressure']}`",
        f"- best_by_combined_score: `{report['cgeom_extended']['best_by_combined_score']}`",
        "",
        "## C_geom x sink_timing Study",
        "",
        f"- study_id: `{report['cgeom_sink_timing']['study_id']}`",
        f"- classification: `{report['cgeom_sink_timing']['classification']}`",
        f"- scenario_count: `{report['cgeom_sink_timing']['scenario_count']}`",
        f"- mean_opening_delta_next_minus_same_s: `{report['cgeom_sink_timing']['mean_opening_delta_next_minus_same_s']}`",
        f"- mean_sink_delay_delta_next_minus_same_s: `{report['cgeom_sink_timing']['mean_sink_delay_delta_next_minus_same_s']}`",
        f"- sink_delay_reproduced_where_expected: `{report['cgeom_sink_timing']['sink_delay_reproduced_where_expected']}`",
        "",
        "## Interpretation",
        "",
        f"- C_geom effect: {report['interpretation']['cgeom_effect']}",
        f"- sink_timing effect: {report['interpretation']['sink_timing_effect']}",
        f"- ranking caveat: {report['interpretation']['ranking_caveat']}",
        f"- caveat: {report['interpretation']['caveat']}",
        "",
        "## Missing Fields For Future Analysis",
        "",
    ]
    lines.extend(f"- `{field}`" for field in report["missing_fields_for_future_analysis"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, report)
    print(f"STATUS={report['status']}")
    print(f"SOURCE={report['source']}")
    print(f"NEXT={report['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
