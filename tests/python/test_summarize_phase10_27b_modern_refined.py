from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import summarize_phase10_27b_modern_refined as phase10_27b  # noqa: E402


def test_help() -> None:
    help_text = phase10_27b.build_parser().format_help()

    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "summary.json"
    output_md = tmp_path / "summary.md"

    summary = phase10_27b.run(
        phase10_27b.build_parser().parse_args(
            ["--output-json", str(output_json), "--output-md", str(output_md)]
        )
    )

    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert summary["phase"] == "10.27B"
    assert loaded["mode"] == "modern_refined"


def test_generates_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "summary.json"
    output_md = tmp_path / "summary.md"

    phase10_27b.run(
        phase10_27b.build_parser().parse_args(
            ["--output-json", str(output_json), "--output-md", str(output_md)]
        )
    )

    markdown = output_md.read_text(encoding="utf-8")
    assert "BUZ67D modern-refined" in markdown
    assert "MODERN_REFINED_NOT_LEGACY_EQUIVALENT" in markdown


def test_status_not_legacy_equivalent() -> None:
    summary = phase10_27b.build_summary()

    assert summary["legacy_equivalence_status"] == "NOT_LEGACY_EQUIVALENT"
    assert "MODERN_REFINED_NOT_LEGACY_EQUIVALENT" in summary["classifications"]


def test_status_pressure_source_timing_blocked_by_geometry() -> None:
    summary = phase10_27b.build_summary()

    assert summary["pressure_source_timing_status"] == "BLOCKED_BY_GEOMETRY"
    assert "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY" in summary["classifications"]


def test_status_different_but_not_automatic_error() -> None:
    summary = phase10_27b.build_summary()

    assert summary["opening_time_status"] == "DIFFERENT_BUT_NOT_AUTOMATIC_ERROR"
    assert summary["metrics"]["modern_opening_time_s"] == 660.0
    assert summary["metrics"]["legacy_opening_time_s"] == 510.0
