from __future__ import annotations

import json
from pathlib import Path

from tools.audit_phase11_10c_penny_math_axisymmetric_1rad import (
    AXISYMMETRIC_CAVEAT,
    FUTURE_OUTPUT_REQUIREMENT,
    NEXT_CORRECT_MATH,
    NEXT_OUTPUT_CONTRACT,
    NEXT_PRESSURE,
    NEXT_VOLUME,
    audit_math,
    build_parser,
    write_markdown,
)


def test_help_mentions_axisymmetric_1rad() -> None:
    help_text = build_parser().format_help()
    assert "axisymmetric 1 rad" in help_text
    assert "--output-json" in help_text


def test_generates_json(tmp_path: Path) -> None:
    result = audit_math()
    out = tmp_path / "audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["phase"] == "11.10C"
    assert loaded["math_audit_passed"] is True


def test_generates_markdown(tmp_path: Path) -> None:
    result = audit_math()
    out = tmp_path / "audit.md"
    write_markdown(result, out)
    text = out.read_text(encoding="utf-8")
    assert "PennyShaped Math" in text
    assert "Dimension Audit" in text


def test_contains_primary_and_secondary_classifications() -> None:
    result = audit_math()
    assert result["primary_classification"] == "PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING"
    assert result["secondary_classification"] == "PENNY_MATH_AXISYMMETRIC_1RAD_PROXY"


def test_contains_dimension_pressure_and_volume_audits() -> None:
    result = audit_math()
    assert result["dimension_audit"]
    assert result["pressure_semantics"] == "PRESSURE_SEMANTICS_CLEAR"
    assert result["volume_multiplier_semantics"] == "VOLUME_MULTIPLIER_EMPIRICAL"


def test_preserves_axisymmetric_and_future_output_markers() -> None:
    result = audit_math()
    assert result["axisymmetric_interpretation"] == AXISYMMETRIC_CAVEAT
    assert result["future_output_requirement"] == FUTURE_OUTPUT_REQUIREMENT


def test_dimensionally_consistent_case_passes_and_requires_output_contract() -> None:
    result = audit_math("consistent")
    assert result["math_audit_passed"] is True
    assert result["requires_code_correction"] is False
    assert result["requires_output_contract"] is True
    assert result["recommended_next_phase"] == NEXT_OUTPUT_CONTRACT


def test_dimension_inconsistency_requires_code_correction() -> None:
    result = audit_math("inconsistent")
    assert result["math_audit_passed"] is False
    assert result["requires_code_correction"] is True
    assert result["recommended_next_phase"] == NEXT_CORRECT_MATH


def test_volume_multiplier_ambiguous_requires_contract_resolution() -> None:
    result = audit_math("volume_ambiguous")
    assert result["math_audit_passed"] is False
    assert result["requires_output_contract"] is True
    assert result["recommended_next_phase"] == NEXT_VOLUME


def test_pressure_sigma_theta_ambiguous_requires_semantic_resolution() -> None:
    result = audit_math("pressure_ambiguous")
    assert result["math_audit_passed"] is False
    assert result["recommended_next_phase"] == NEXT_PRESSURE


def test_dimension_rows_include_opening_radius_and_volume() -> None:
    result = audit_math()
    fields = {row["field"] for row in result["dimension_audit"]}
    assert "opening_m" in fields
    assert "radius_m" in fields
    assert "fracture_volume_proxy_m3" in fields


def test_recommended_next_phase_matches_output_contract_for_current_audit() -> None:
    result = audit_math()
    assert result["recommended_next_phase"] == "PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT"
