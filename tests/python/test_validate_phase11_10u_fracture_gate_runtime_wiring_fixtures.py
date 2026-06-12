from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import validate_phase11_10u_fracture_gate_runtime_wiring_fixtures as validator


FIXTURE_DIR = Path("tests/fixtures/comparison/phase11_10u")
SCENARIOS = FIXTURE_DIR / "fracture_gate_runtime_wiring_scenarios.json"
METADATA = FIXTURE_DIR / "fracture_gate_runtime_wiring_metadata.json"


def _summary() -> dict:
    return validator.validate_files(SCENARIOS, METADATA)


def _scenario_by_id(scenario_id: str) -> dict:
    scenarios = validator.load_scenarios(SCENARIOS)
    return {item["id"]: item for item in scenarios}[scenario_id]


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        validator.main(["--help"])
    assert exc.value.code == 0
    assert "Phase 11.10U" in capsys.readouterr().out


def test_valid_scenarios() -> None:
    summary = _summary()
    assert summary["fixture_status"] == "FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID"
    assert summary["scenario_count"] == 7


def test_valid_metadata() -> None:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata["fixture_type"] == "runtime_wiring_contract_only"
    assert "FractureModelSelector" in metadata["required_components"]


def test_default_pkn_scenario_present() -> None:
    scenario = _scenario_by_id("missing_model_defaults_pkn_not_reached")
    assert scenario["fracture_model_input"] is None
    assert scenario["expected_selected_model"] == "PKN"


def test_explicit_pkn_scenario_present() -> None:
    scenario = _scenario_by_id("explicit_pkn_initiated_dispatch_eligible")
    assert scenario["fracture_model_input"] == "PKN"
    assert scenario["expected_dispatch_status"] == "FRACTURE_DISPATCH_PKN_ELIGIBLE"


def test_explicit_penny_scenario_present() -> None:
    scenario = _scenario_by_id("explicit_penny_initiated_diagnostic_eligible")
    assert scenario["fracture_model_input"] == "PENNY_SHAPED"
    assert (
        scenario["expected_dispatch_status"]
        == "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE"
    )


def test_sigmatheta_guard_blocked_scenario_present() -> None:
    scenario = _scenario_by_id("sigmatheta_guard_blocks_dispatch")
    assert scenario["sigma_theta_guard_ready"] is False
    assert (
        scenario["expected_gate_status"]
        == "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE"
    )


def test_criterion_blocked_scenario_present() -> None:
    scenario = _scenario_by_id("pressure_sigmatheta_criterion_blocks_dispatch")
    assert scenario["criterion_ready"] is False
    assert (
        scenario["expected_gate_status"]
        == "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION"
    )


def test_kgd_unsupported_scenario_present() -> None:
    scenario = _scenario_by_id("unsupported_kgd_model_blocked")
    assert scenario["fracture_model_input"] == "KGD"
    assert scenario["expected_selection_error"] == "UNSUPPORTED_FRACTURE_MODEL"


def test_explicit_empty_blocked_scenario_present() -> None:
    scenario = _scenario_by_id("explicit_empty_model_blocked")
    assert scenario["fracture_model_input"] == ""
    assert (
        scenario["expected_selection_error"]
        == "EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED"
    )


def test_penny_physically_validated_false() -> None:
    assert _scenario_by_id("explicit_penny_initiated_diagnostic_eligible")[
        "physically_validated"
    ] is False


def test_penny_legacy_equivalent_false() -> None:
    assert _scenario_by_id("explicit_penny_initiated_diagnostic_eligible")[
        "legacy_equivalent"
    ] is False


def test_runtime_wiring_implemented_false() -> None:
    assert _summary()["runtime_wiring_implemented"] is False


def test_runtime_execution_allowed_false() -> None:
    assert _summary()["runtime_execution_allowed"] is False


def test_buz29_execution_allowed_false() -> None:
    assert _summary()["buz29_execution_allowed"] is False


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "summary.json"
    code = validator.main(
        [
            "--scenarios",
            str(SCENARIOS),
            "--metadata",
            str(METADATA),
            "--output-json",
            str(output),
        ]
    )
    assert code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["fixture_status"] == "FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "summary.md"
    code = validator.main(
        [
            "--scenarios",
            str(SCENARIOS),
            "--metadata",
            str(METADATA),
            "--output-md",
            str(output),
        ]
    )
    assert code == 0
    text = output.read_text(encoding="utf-8")
    assert "fracture gate runtime wiring fixture validation" in text
    assert "FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID" in text
