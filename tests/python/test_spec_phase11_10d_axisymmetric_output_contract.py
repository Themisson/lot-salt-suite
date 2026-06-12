from __future__ import annotations

import json
import math
from pathlib import Path

from tools.spec_phase11_10d_axisymmetric_output_contract import (
    CONTRACT_STATUS,
    NEXT_PHASE,
    VOLUME_MULTIPLIER_SEMANTICS,
    build_contract,
    build_parser,
    write_markdown,
)


def field_names(contract: dict) -> set[str]:
    return {row["name"] for row in contract["field_contract"]}


def test_help_mentions_axisymmetric_output_contract() -> None:
    help_text = build_parser().format_help()
    assert "axisymmetric 1rad to 2pi output contract" in help_text
    assert "--output-json" in help_text


def test_generates_json(tmp_path: Path) -> None:
    contract = build_contract()
    out = tmp_path / "contract.json"
    out.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["phase"] == "11.10D"
    assert loaded["contract_status"] == CONTRACT_STATUS


def test_generates_markdown(tmp_path: Path) -> None:
    contract = build_contract()
    out = tmp_path / "contract.md"
    write_markdown(contract, out)
    text = out.read_text(encoding="utf-8")
    assert "Axisymmetric 1rad to 2pi Output Contract" in text
    assert "Field Contract" in text
    assert "Conversion Rules" in text


def test_contract_status_and_flags() -> None:
    contract = build_contract()
    assert contract["contract_status"] == CONTRACT_STATUS
    assert contract["implementation_allowed"] is False
    assert contract["physical_validation"] is False
    assert contract["legacy_equivalence"] is False


def test_axisymmetric_angle_and_2pi_factor() -> None:
    contract = build_contract()
    assert contract["axisymmetric_angle_rad"] == 1.0
    assert contract["volume_conversion_factor_1rad_to_2pi"] == math.tau


def test_volume_multiplier_semantics_are_empirical() -> None:
    contract = build_contract()
    assert contract["volume_multiplier_semantics"] == VOLUME_MULTIPLIER_SEMANTICS
    assert any("volume_multiplier is not equal to 2pi" in row["rule"] for row in contract["conversion_rules"])


def test_required_fracture_and_solid_volume_fields_are_present() -> None:
    names = field_names(build_contract())
    assert "fracture_volume_proxy_1rad_m3" in names
    assert "fracture_volume_equivalent_2pi_m3" in names
    assert "solid_volume_1rad_m3" in names
    assert "solid_volume_equivalent_2pi_m3" in names


def test_2pi_equivalent_fields_require_source() -> None:
    contract = build_contract()
    rows = {row["name"]: row for row in contract["field_contract"]}
    assert rows["fracture_volume_equivalent_2pi_m3"]["source_required"] is True
    assert rows["solid_volume_equivalent_2pi_m3"]["source_required"] is True
    assert any(row["id"] == "RULE_4_2PI_SOURCE_REQUIRED" for row in contract["conversion_rules"])


def test_forbidden_interpretation_blocks_volume_multiplier_as_2pi() -> None:
    contract = build_contract()
    assert any("Do not treat volume_multiplier as 2pi" in item for item in contract["forbidden_interpretations"])


def test_recommended_next_phase_is_output_fixture_contract() -> None:
    contract = build_contract()
    assert contract["recommended_next_phase"] == NEXT_PHASE


def test_missing_volume_multiplier_semantics_is_partial() -> None:
    contract = build_contract("missing_volume_multiplier_semantics")
    assert contract["contract_status"] == "AXISYMMETRIC_OUTPUT_CONTRACT_PARTIAL"
    assert contract["recommended_next_phase"] == "PHASE11_10E_RESOLVE_VOLUME_MULTIPLIER_SEMANTICS"


def test_conflict_is_blocked() -> None:
    contract = build_contract("conflict")
    assert contract["contract_status"] == "AXISYMMETRIC_OUTPUT_CONTRACT_BLOCKED"
    assert contract["recommended_next_phase"] == "PHASE11_10E_RECONCILE_OUTPUT_CONTRACT_WITH_EXISTING_API"
