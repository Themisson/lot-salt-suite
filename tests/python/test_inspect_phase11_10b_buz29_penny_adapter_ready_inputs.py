from __future__ import annotations

from pathlib import Path

import yaml

from tools.inspect_phase11_10b_buz29_penny_adapter_ready_inputs import (
    AXISYMMETRIC_CAVEAT,
    CLASS_BLOCKED,
    CLASS_INCONCLUSIVE,
    CLASS_PARTIAL,
    CLASS_READY,
    FUTURE_OUTPUT_REQUIREMENT,
    NEXT_MATH_AUDIT,
    build_parser,
    inspect_adapter_ready_inputs,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = REPO_ROOT / "cases/validation/non_pkn/buz29_penny_candidate.yaml"


def _candidate_data() -> dict:
    return {
        "case": {"id": "buz29_penny_candidate", "active": False},
        "track": {"gate": "BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A"},
        "diagnostic_evidence": {
            "pressure_history_status": "PRESSURE_HISTORY_FOUND_CONSUMABLE",
            "opening_time_status": "OPENING_TIME_FOUND_CONSUMABLE",
            "opening_time_min": 10.4,
            "available_blocks": ["dP", "dV_leakoff", "V_outflow"],
        },
        "axisymmetric_interpretation": {
            "angle_rad": 1.0,
            "caveat": AXISYMMETRIC_CAVEAT,
            "future_output_requirement": FUTURE_OUTPUT_REQUIREMENT,
        },
        "diagnostics": {
            "physically_validated": False,
            "legacy_equivalent": False,
            "active_simulation_case": False,
        },
    }


def _write_candidate(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "candidate.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_help_mentions_case_argument() -> None:
    help_text = build_parser().format_help()
    assert "adapter-ready inputs" in help_text
    assert "--case" in help_text


def test_repository_candidate_is_partial_adapter_ready() -> None:
    result = inspect_adapter_ready_inputs(CANDIDATE)
    assert result["classification"] == CLASS_PARTIAL
    assert result["adapter_ready"] is False
    assert result["partial_adapter_ready"] is True
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["active_simulation_case"] is False
    assert result["recommended_next_phase"] == NEXT_MATH_AUDIT


def test_mapping_contains_required_adapter_fields(tmp_path: Path) -> None:
    result = inspect_adapter_ready_inputs(_write_candidate(tmp_path, _candidate_data()))
    assert "young_modulus_Pa" in result["required_adapter_fields"]
    assert "sigma_theta_compression_positive_Pa" in result["required_adapter_fields"]
    assert result["field_mapping"]
    fields = {row["adapter_field"] for row in result["field_mapping"]}
    assert "pressure_history" in fields
    assert "axisymmetric_angle_rad" in fields


def test_partial_mapping_records_missing_and_deferred_fields(tmp_path: Path) -> None:
    result = inspect_adapter_ready_inputs(_write_candidate(tmp_path, _candidate_data()))
    assert result["classification"] == CLASS_PARTIAL
    assert "young_modulus_Pa" in result["missing_fields"]
    assert "sigma_theta_compression_positive_Pa" in result["missing_fields"]
    assert "mathematical audit of PennyShapedModel" in result["deferred_fields"]


def test_blocked_when_pressure_opening_evidence_is_missing(tmp_path: Path) -> None:
    data = _candidate_data()
    data["diagnostic_evidence"]["pressure_history_status"] = "MISSING"
    data["diagnostic_evidence"]["opening_time_status"] = "MISSING"
    result = inspect_adapter_ready_inputs(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASS_BLOCKED
    assert "pressure_or_opening_evidence" in result["blocking_gaps"]


def test_inconclusive_when_conversion_has_severe_ambiguity(tmp_path: Path, monkeypatch) -> None:
    data = _candidate_data()
    path = _write_candidate(tmp_path, data)

    from tools import inspect_phase11_10b_buz29_penny_adapter_ready_inputs as module

    original = module.build_field_mapping

    def ambiguous(candidate: dict):
        rows = original(candidate)
        for row in rows:
            if row["adapter_field"] == "pressure_history":
                row["notes"] = "ambiguous unit provenance"
        return rows

    monkeypatch.setattr(module, "build_field_mapping", ambiguous)
    result = module.inspect_adapter_ready_inputs(path)
    assert result["classification"] == CLASS_INCONCLUSIVE


def test_ready_when_all_required_fields_are_consumable(tmp_path: Path, monkeypatch) -> None:
    path = _write_candidate(tmp_path, _candidate_data())
    from tools import inspect_phase11_10b_buz29_penny_adapter_ready_inputs as module

    def ready_mapping(candidate: dict):
        rows = []
        for field in module.REQUIRED_ADAPTER_FIELDS:
            rows.append(
                module.mapping(
                    field,
                    "FOUND_CONSUMABLE",
                    "fixture",
                    field,
                    "SI",
                    "none",
                    True,
                    "fixture ready",
                )
            )
        return rows

    monkeypatch.setattr(module, "build_field_mapping", ready_mapping)
    result = module.inspect_adapter_ready_inputs(path)
    assert result["classification"] == CLASS_READY
    assert result["adapter_ready"] is True
    assert result["recommended_next_phase"] == NEXT_MATH_AUDIT


def test_axisymmetric_and_future_output_requirements_are_preserved(tmp_path: Path) -> None:
    result = inspect_adapter_ready_inputs(_write_candidate(tmp_path, _candidate_data()))
    assert result["axisymmetric_interpretation"] == AXISYMMETRIC_CAVEAT
    assert result["future_output_requirement"] == FUTURE_OUTPUT_REQUIREMENT
    assert AXISYMMETRIC_CAVEAT in result["caveats"]
    assert FUTURE_OUTPUT_REQUIREMENT in result["caveats"]


def test_flags_remain_negative_for_physical_validation(tmp_path: Path) -> None:
    result = inspect_adapter_ready_inputs(_write_candidate(tmp_path, _candidate_data()))
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["active_simulation_case"] is False


def test_prompt_example_fields_are_mapped_as_non_api_inputs(tmp_path: Path) -> None:
    result = inspect_adapter_ready_inputs(_write_candidate(tmp_path, _candidate_data()))
    rows = {row["adapter_field"]: row for row in result["field_mapping"]}
    assert rows["netPressure_Pa"]["status"] == "NOT_APPLICABLE"
    assert rows["characteristicRadius_m"]["status"] == "NOT_APPLICABLE"
