from __future__ import annotations

import json
from pathlib import Path

from tools import analyze_phase11_5a_cgeom_extended as analyzer


SUMMARY = Path("tests/fixtures/comparison/phase11_5a_cgeom_extended_summary.csv")
METADATA = Path("tests/fixtures/comparison/phase11_5a_cgeom_extended_metadata.json")


def test_help() -> None:
    help_text = analyzer.build_parser().format_help()

    assert "--summary" in help_text
    assert "--output-json" in help_text


def test_valid_summary_and_metadata_are_analyzed() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    assert report["classification"] == "CGEOM_EXTENDED_SENSITIVITY_ANALYZED"
    assert report["matrix_id"] == "buz67d_modern_refined_cgeom_extended_v2"
    assert report["scenario_count"] == 3


def test_missing_optional_fields_generate_caveat() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    assert any("optional columns missing" in item for item in report["caveats"])


def test_diagnostic_ranking_is_calculated() -> None:
    report = analyzer.analyze(SUMMARY, METADATA)

    assert report["best_by_opening_time"] == "cgeom_075_next_step"
    assert report["best_by_combined_score"] is not None


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
    assert json.loads(output_json.read_text(encoding="utf-8"))["classification"] == "CGEOM_EXTENDED_SENSITIVITY_ANALYZED"
    assert "Phase 11.5A" in output_md.read_text(encoding="utf-8")
