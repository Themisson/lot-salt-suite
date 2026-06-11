from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools import decide_phase10_25c_sigma_theta_source as decision_tool


def _write_summary(path: Path, *, opening_error: float, peak_error: float = -0.02) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "phase",
                "classification",
                "relative_error_max_pressure",
                "opening_time_error_s",
                "sink_delay_error_s",
                "pressure_at_opening_relative_error",
                "final_pressure_relative_error",
                "modern_fracture_initiation_time_s",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "phase": path.stem,
                "classification": "fixture",
                "relative_error_max_pressure": peak_error,
                "opening_time_error_s": opening_error,
                "sink_delay_error_s": 0.0,
                "pressure_at_opening_relative_error": 0.01,
                "final_pressure_relative_error": -0.01,
                "modern_fracture_initiation_time_s": 510.0 + opening_error,
            }
        )


def _run(tmp_path: Path, old_opening: float, new_opening: float, peak_error: float = -0.02) -> dict[str, object]:
    phase10_24c = tmp_path / "phase10_24c_summary.csv"
    phase10_25b = tmp_path / "phase10_25b_summary.csv"
    _write_summary(phase10_24c, opening_error=old_opening)
    _write_summary(phase10_25b, opening_error=new_opening, peak_error=peak_error)
    return decision_tool.run_decision(
        argparse.Namespace(
            phase10_24c_summary=phase10_24c,
            phase10_25b_summary=phase10_25b,
            output_json=tmp_path / "decision.json",
            output_md=tmp_path / "decision.md",
            manual_classification=None,
            manual_relative_error_max_pressure=None,
            manual_opening_time_error_s=None,
            manual_sink_delay_error_s=None,
            manual_pressure_at_opening_relative_error=None,
            manual_final_pressure_relative_error=None,
            manual_modern_fracture_initiation_time_s=None,
        )
    )


def test_decide_phase10_25c_help_exposes_required_outputs() -> None:
    help_text = decision_tool.build_parser().format_help()

    assert "--phase10-24c-summary" in help_text
    assert "--phase10-25b-summary" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_decide_phase10_25c_prioritizes_salt_wall_stress_runtime(tmp_path: Path) -> None:
    result = _run(tmp_path, old_opening=150.0, new_opening=0.0)

    assert result["decision"] == "NEXT_MODEL_SALT_WALL_STRESS_RUNTIME"
    assert result["diagnostics"]["opening_ok"] is True
    assert (tmp_path / "decision.json").exists()
    assert (tmp_path / "decision.md").exists()


def test_decide_phase10_25c_prioritizes_pressure_source_timing_review(tmp_path: Path) -> None:
    result = _run(tmp_path, old_opening=150.0, new_opening=150.0)

    assert result["decision"] == "NEXT_MODEL_PRESSURE_SOURCE_TIMING_REVIEW"
    assert result["diagnostics"]["opening_improved"] is False


def test_decide_phase10_25c_prioritizes_sigma_theta_point_mapping_review(tmp_path: Path) -> None:
    result = _run(tmp_path, old_opening=150.0, new_opening=90.0)

    assert result["decision"] == "NEXT_MODEL_SIGMA_THETA_POINT_MAPPING_REVIEW"
    assert result["diagnostics"]["opening_improved"] is True


def test_decide_phase10_25c_blocks_missing_summaries(tmp_path: Path) -> None:
    try:
        decision_tool.run_decision(
            argparse.Namespace(
                phase10_24c_summary=tmp_path / "missing_24c.csv",
                phase10_25b_summary=tmp_path / "missing_25b.csv",
                output_json=tmp_path / "decision.json",
                output_md=tmp_path / "decision.md",
                manual_classification=None,
                manual_relative_error_max_pressure=None,
                manual_opening_time_error_s=None,
                manual_sink_delay_error_s=None,
                manual_pressure_at_opening_relative_error=None,
                manual_final_pressure_relative_error=None,
                manual_modern_fracture_initiation_time_s=None,
            )
        )
    except FileNotFoundError as exc:
        assert decision_tool.MISSING_SUMMARIES in str(exc)
        return
    raise AssertionError("missing summaries should block the decision")
