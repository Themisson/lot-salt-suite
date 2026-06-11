from __future__ import annotations

import json
from pathlib import Path

from tools import analyze_phase11_5b_cgeom_sink_timing as analyzer


SUMMARY = Path("tests/fixtures/comparison/phase11_5b_cgeom_sink_timing_summary.csv")
METADATA = Path("tests/fixtures/comparison/phase11_5b_cgeom_sink_timing_metadata.json")


def test_help() -> None:
    help_text = analyzer.build_parser().format_help()

    assert "--summary" in help_text
    assert "--output-json" in help_text


def test_valid_summary_and_metadata_are_analyzed() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    assert report["classification"] == "CGEOM_SINK_TIMING_MATRIX_ANALYZED"
    assert report["matrix_id"] == "buz67d_modern_refined_cgeom_sink_timing_v2"
    assert report["scenario_count"] == 6


def test_same_cgeom_comparison_is_calculated() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    comparison = next(item for item in report["same_cgeom_comparisons"] if item["cgeom_factor"] == 0.75)
    assert comparison["sink_delay_delta_next_minus_same_s"] == 30.0
    assert comparison["max_pressure_delta_next_minus_same_Pa"] == 2100000.0


def test_same_sink_timing_comparison_is_calculated() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    comparison = next(
        item
        for item in report["same_sink_timing_comparisons"]
        if item["sink_timing"] == "next_step" and item["from_cgeom_factor"] == 0.75
    )
    assert comparison["to_cgeom_factor"] == 1.0
    assert comparison["opening_time_delta_s"] == 150.0


def test_missing_optional_fields_generate_caveat() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    assert any("optional columns missing" in item for item in report["caveats"])


def test_json_and_markdown_outputs(tmp_path: Path) -> None:
    output_json = tmp_path / "analysis.json"
    output_md = tmp_path / "analysis.md"

    assert analyzer.main(
        [
            "--summary",
            str(SUMMARY),
            "--metadata",
            str(METADATA),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    ) == 0
    assert json.loads(output_json.read_text(encoding="utf-8"))["classification"] == "CGEOM_SINK_TIMING_MATRIX_ANALYZED"
    assert "Phase 11.5B" in output_md.read_text(encoding="utf-8")
