from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "tests" / "fixtures" / "comparison" / "level1_readiness_gate.json"


def load_gate() -> dict[str, Any]:
    with GATE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def test_level1_gate_file_exists_and_is_parseable() -> None:
    assert GATE_PATH.exists()
    data = load_gate()

    assert data["phase"] == "10.14EF"
    assert data["status"] == "LEVEL1_CONTROLLED_EQUIVALENT_CASE_CREATED_RUN_PENDING"


def test_time_unit_is_resolved_as_minutes_by_author_context() -> None:
    data = load_gate()
    time_unit = data["time_unit"]

    assert time_unit["status"] == "RESOLVED_MINUTES_AUTHOR_CONTEXT"
    assert time_unit["legacy_unit"] == "min"
    assert time_unit["modern_unit"] == "s"
    assert time_unit["evidence_type"] == "author_provided_context"
    assert time_unit["conversion"]["formula"] == "time_s = Time_raw * 60.0"
    assert time_unit["conversion"]["factor_to_seconds"] == 60.0


def test_converted_legacy_duration_matches_configured_controlled_case() -> None:
    data = load_gate()
    time_unit = data["time_unit"]

    assert time_unit["legacy_time_min_s"] == 0.0
    assert time_unit["legacy_time_max_s"] == 750.0
    assert time_unit["reduced_modern_fixture_time_min_s"] == 0.0
    assert time_unit["reduced_modern_fixture_time_max_s"] == 420.0
    assert time_unit["controlled_case_time_min_s"] == 0.0
    assert time_unit["controlled_case_time_max_s"] == 750.0
    assert time_unit["time_range_equivalent"] is True
    assert time_unit["time_range_equivalence_scope"] == "configured_controlled_case_only"


def test_level1_numeric_and_physical_validation_remain_closed() -> None:
    data = load_gate()

    assert data["level1_ready"] is False
    assert data["physical_validation"] is False
    assert data["numeric_equivalence"] is False
    assert data["case_equivalence"]["status"] == "CONTROLLED_EQUIVALENT"
    assert data["controlled_case"] == "cases/validation/buz67d_pkn_legacy_aligned.yaml"


def test_blocked_items_preserve_level1_evidence_gate() -> None:
    data = load_gate()
    blocked = set(data["blocked_items"])

    for field in (
        "sigmaTheta",
        "pw",
        "margin",
        "opened",
        "legacy dP semantic meaning",
        "legacy Layer equivalence",
        "Level 1 numeric temporal equivalence",
    ):
        assert field in blocked


def test_forbidden_next_steps_prevent_physical_comparison_shortcuts() -> None:
    data = load_gate()
    forbidden = "\n".join(data["forbidden_next_steps"])

    assert "Level 1 numeric comparison" in forbidden
    assert "dP to net_pressure_Pa equivalence" in forbidden
    assert "sigmaTheta comparison" in forbidden
    assert "pw comparison" in forbidden
    assert "physical fracture validation" in forbidden


def test_no_blocked_field_is_promoted_to_allowed_next_step() -> None:
    data = load_gate()
    allowed = "\n".join(data["allowed_next_steps"]).lower()

    for phrase in ("sigmatheta comparison", "pw comparison", "margin comparison", "opened comparison"):
        assert phrase not in allowed
