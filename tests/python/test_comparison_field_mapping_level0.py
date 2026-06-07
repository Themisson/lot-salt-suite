from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "tests" / "fixtures" / "comparison" / "field_mapping_level0.json"

TEMPORAL_STATUSES = {
    "BLOCKED_UNKNOWN_UNIT",
    "PARTIALLY_INFERRED",
    "DETERMINED",
    "RESOLVED_MINUTES_AUTHOR_CONTEXT",
    "BLOCKED_NON_EQUIVALENT_CASE",
    "BLOCKED_INSUFFICIENT_EVIDENCE",
}


def load_mapping() -> dict[str, Any]:
    with MAPPING_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def find_mapping(data: dict[str, Any], legacy_field: str | None, modern_field: str | None) -> dict[str, Any]:
    for mapping in data["field_mappings"]:
        if mapping.get("legacy_field") == legacy_field and mapping.get("modern_field") == modern_field:
            return mapping
    raise AssertionError(f"mapping not found: {legacy_field!r} -> {modern_field!r}")


def find_modern_only_mapping(data: dict[str, Any], modern_field: str) -> dict[str, Any]:
    for mapping in data["field_mappings"]:
        if mapping.get("modern_field") == modern_field and mapping.get("comparison_allowed") == "none":
            return mapping
    raise AssertionError(f"blocked mapping not found for: {modern_field}")


def test_field_mapping_file_exists_and_is_parseable() -> None:
    assert MAPPING_PATH.exists()
    data = load_mapping()
    assert data["phase"] == "10.14D"
    assert data["field_mappings"]


def test_field_mapping_status_declares_no_physical_validation() -> None:
    data = load_mapping()

    assert data["status"] == "LEVEL0_FIELD_MAPPING_DOCUMENTED_NO_PHYSICAL_VALIDATION"
    assert data["physical_validation"] is False
    assert data["numeric_equivalence"] is False


def test_temporal_mapping_is_blocked_or_documented() -> None:
    data = load_mapping()
    mapping = find_mapping(data, "Time", "time_s")

    assert mapping["mapping_status"] in TEMPORAL_STATUSES
    if mapping["mapping_status"] == "DETERMINED":
        assert mapping["legacy_unit"] not in {"unknown_raw", None, ""}
        assert "conversion" in mapping
    elif mapping["mapping_status"] == "RESOLVED_MINUTES_AUTHOR_CONTEXT":
        assert mapping["legacy_unit"] == "min"
        assert mapping["modern_unit"] == "s"
        assert mapping["conversion"]["factor_to_seconds"] == 60.0
        assert mapping["comparison_allowed"] == "time_unit_conversion_only"
        assert mapping["numeric_comparison_allowed"] is False
        assert mapping["level1_ready"] is False
        assert "must not be compared numerically" in mapping["notes"]
    else:
        assert mapping["comparison_allowed"] != "numeric"
        assert "do not compare numerically" in mapping["notes"]


def test_blocked_fields_are_not_comparable() -> None:
    data = load_mapping()

    for field in ("sigmaTheta", "pw", "margin", "opened"):
        mapping = find_modern_only_mapping(data, field)
        assert mapping["comparison_allowed"] == "none"
        assert mapping["mapping_status"] == "NOT_AVAILABLE_FOR_COMPARISON"


def test_legacy_layer_is_not_wall_gp_equivalent() -> None:
    data = load_mapping()
    mapping = find_mapping(data, "Layer", None)

    assert mapping["mapping_status"] == "BLOCKED_NON_EQUIVALENT_INDEX"
    assert mapping["comparison_allowed"] == "presence_only"
    assert "not equivalent to modern wall_gp_*" in mapping["notes"]


def test_dp_is_not_net_pressure_equivalent() -> None:
    data = load_mapping()
    mapping = find_mapping(data, "dP", "net_pressure_Pa")

    assert mapping["mapping_status"] == "BLOCKED_SEMANTIC_AMBIGUITY"
    assert mapping["comparison_allowed"] == "presence_only"
    assert "must not be assumed equivalent" in mapping["notes"]


def test_caveats_preserved_in_mapping() -> None:
    data = load_mapping()
    caveats = "\n".join(data["caveats"])

    assert "temporal unit is minutes" in caveats
    assert "time_s = Time_raw * 60.0" in caveats
    assert "case and duration equivalence" in caveats
    assert "Layer is 1-based" in caveats
    assert "not equivalent to modern wall_gp_*" in caveats
    assert "sigmaTheta is not available" in caveats
    assert "pw is not available" in caveats
    assert "margin is not available" in caveats
    assert "opened is not available" in caveats
    assert "structural/documental only" in caveats
    assert "no physical validation" in caveats
