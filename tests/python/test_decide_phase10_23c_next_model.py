from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools import decide_phase10_23c_next_model


def _write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def _run(tmp_path: Path, row_b: dict[str, object]) -> dict[str, object]:
    summary_a = tmp_path / "a.csv"
    summary_b = tmp_path / "b.csv"
    _write_csv(summary_a, {"phase": "10.23A", "classification": "NEXT_STEP_SINK_EFFECTIVE"})
    _write_csv(summary_b, {"phase": "10.23B", **row_b})
    return decide_phase10_23c_next_model.run_decision(
        argparse.Namespace(
            phase10_23a_summary=summary_a,
            phase10_23b_summary=summary_b,
            output_json=tmp_path / "out" / "decision.json",
            output_md=tmp_path / "out" / "decision.md",
        )
    )


def test_decide_phase10_23c_help_exposes_required_arguments() -> None:
    help_text = decide_phase10_23c_next_model.build_parser().format_help()

    assert "--phase10-23a-summary" in help_text
    assert "--phase10-23b-summary" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_decide_phase10_23c_prioritizes_sigma_theta_runtime(tmp_path: Path) -> None:
    decision = _run(
        tmp_path,
        {
            "classification": "COMBINED_DIAGNOSTIC_PRESSURE_OK_OPENING_SHIFTED",
            "relative_error_max_pressure": -0.02,
            "modern_fracture_initiation_time_s": 660.0,
            "modern_sink_delay_s": 30.0,
        },
    )

    assert decision["decision"] == "NEXT_MODEL_SIGMA_THETA_RUNTIME"
    assert decision["sigma_theta_runtime_priority"] is True
    assert decision["pressure_tabulated_geometric_allowed"] is False


def test_decide_phase10_23c_prioritizes_phase_dependent_compliance(tmp_path: Path) -> None:
    decision = _run(
        tmp_path,
        {
            "classification": "COMBINED_DIAGNOSTIC_PARTIAL",
            "relative_error_max_pressure": 0.25,
            "modern_fracture_initiation_time_s": 690.0,
            "modern_sink_delay_s": 30.0,
        },
    )

    assert decision["decision"] == "NEXT_MODEL_PHASE_DEPENDENT_COMPLIANCE"
    assert decision["phase_dependent_compliance_priority"] is True


def test_decide_phase10_23c_accepts_constant_geometric_diagnostic_sufficient(
    tmp_path: Path,
) -> None:
    decision = _run(
        tmp_path,
        {
            "classification": "COMBINED_DIAGNOSTIC_EFFECTIVE",
            "relative_error_max_pressure": 0.02,
            "modern_fracture_initiation_time_s": 510.0,
            "modern_sink_delay_s": 30.0,
        },
    )

    assert decision["decision"] == "NEXT_MODEL_CONSTANT_GEOMETRIC_DIAGNOSTIC_SUFFICIENT"
    assert decision["physical_validation"] is False


def test_decide_phase10_23c_reports_missing_summaries(tmp_path: Path) -> None:
    decision = decide_phase10_23c_next_model.run_decision(
        argparse.Namespace(
            phase10_23a_summary=tmp_path / "missing_a.csv",
            phase10_23b_summary=tmp_path / "missing_b.csv",
            output_json=tmp_path / "out" / "decision.json",
            output_md=tmp_path / "out" / "decision.md",
        )
    )

    assert decision["status"] == "PHASE10_23C_BLOCKED_MISSING_PHASE_SUMMARIES"
    assert decision["decision"] == "NEXT_MODEL_INCONCLUSIVE"
    assert len(decision["missing_inputs"]) == 2
