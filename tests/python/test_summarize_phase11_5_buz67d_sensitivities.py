from __future__ import annotations

import json
from pathlib import Path

from tools import summarize_phase11_5_buz67d_sensitivities as summary


def test_help() -> None:
    help_text = summary.build_parser().format_help()

    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_report_contains_required_markers() -> None:
    report = summary.build_report()

    assert report["status"] == "BUZ67D_MODERN_REFINED_SENSITIVITIES_CONSOLIDATED"
    assert report["cgeom_extended"]["best_by_opening_time"] == "cgeom_075_next_step"
    assert report["cgeom_extended"]["best_by_max_pressure"] == "cgeom_055_next_step"
    assert report["cgeom_sink_timing"]["mean_sink_delay_delta_next_minus_same_s"] == 30.0
    assert "diagnostic only" in report["interpretation"]["caveat"]
    assert report["recommended_next_phase"] == "PHASE11_6A_BUZ29_VISCO_FIRST_WELL_AUDIT"


def test_json_and_markdown_outputs(tmp_path: Path) -> None:
    output_json = tmp_path / "summary.json"
    output_md = tmp_path / "summary.md"

    assert summary.main(["--output-json", str(output_json), "--output-md", str(output_md)]) == 0

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["status"] == "BUZ67D_MODERN_REFINED_SENSITIVITIES_CONSOLIDATED"
    text = output_md.read_text(encoding="utf-8")
    assert "best_by_opening_time" in text
    assert "PHASE11_6A_BUZ29_VISCO_FIRST_WELL_AUDIT" in text
