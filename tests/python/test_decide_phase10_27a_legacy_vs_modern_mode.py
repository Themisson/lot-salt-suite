from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import decide_phase10_27a_legacy_vs_modern_mode as phase10_27a  # noqa: E402


def test_help() -> None:
    help_text = phase10_27a.build_parser().format_help()

    assert "--objective" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_decision_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"

    decision = phase10_27a.run(
        phase10_27a.build_parser().parse_args(
            [
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ]
        )
    )

    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert decision["source"] == "DOCUMENTED_PHASE_SUMMARY"
    assert loaded["phase"] == "10.27A"
    assert "legacy-equivalence" in markdown
    assert "modern-refined" in markdown


def test_classifies_legacy_equivalence_radial_solver_path() -> None:
    decision = phase10_27a.decide("strict_legacy")

    assert decision["main_decision"] == "NEXT_PHASE_LEGACY_EQUIVALENCE_RADIAL_SOLVER"
    assert "APBSALT1D_SOLVER_EQUIVALENCE_REQUIRED_FOR_STRICT_MATCH" in decision["classifications"]


def test_classifies_modern_refined_documentation_path() -> None:
    decision = phase10_27a.decide("modern_refined")

    assert (
        decision["main_decision"]
        == "NEXT_PHASE_MODERN_REFINED_DOCUMENTATION_AND_VALIDATION"
    )
    assert "MODERN_REFINED_MODE_ACCEPTABLE_FOR_ANALYSIS" in decision["classifications"]
    assert "MODERN_REFINED_MODE_NOT_LEGACY_EQUIVALENT" in decision["classifications"]


def test_classifies_salt_wall_stress_runtime_path() -> None:
    decision = phase10_27a.decide("salt_wall_stress_runtime")

    assert decision["main_decision"] == "NEXT_PHASE_IMPLEMENT_SALT_WALL_STRESS_RUNTIME"
    assert "SIGMATHETA_RUNTIME_STILL_FUTURE_WORK" in decision["classifications"]


def test_confirms_pressure_source_timing_is_blocked_by_geometry() -> None:
    decision = phase10_27a.decide("modern_refined")

    assert decision["pressure_source_timing_allowed"] is False
    assert decision["pressure_source_timing_gate"] == "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY"


def test_can_explicitly_choose_return_to_pressure_timing_only_as_override() -> None:
    decision = phase10_27a.decide("return_to_pressure_timing")

    assert decision["main_decision"] == "NEXT_PHASE_RETURN_TO_PRESSURE_SOURCE_TIMING"
    assert decision["pressure_source_timing_allowed"] is True


def test_matrix_contains_required_aspects() -> None:
    aspects = {row["aspect"] for row in phase10_27a.decision_matrix()}

    assert {
        "radial_domain",
        "radial_mesh",
        "mesh_ratio",
        "integration_order",
        "sigmaTheta_sampling_point",
        "sigmaTheta_source",
        "pressure_source_timing",
        "compliance_model",
        "sink_timing",
        "thermal_term",
        "dMl_leakoff_terms",
        "runtime_salt_coupling",
        "validation_status",
    }.issubset(aspects)
