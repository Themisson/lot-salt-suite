from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import spec_phase11_10t_fracture_gate_runtime_wiring as spec_tool


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        spec_tool.main(["--help"])
    assert exc.value.code == 0
    assert "Phase 11.10T" in capsys.readouterr().out


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "spec.json"

    assert spec_tool.main(["--output-json", str(output)]) == 0

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["runtime_wiring_spec_status"] == "FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "spec.md"

    assert spec_tool.main(["--output-md", str(output)]) == 0

    text = output.read_text(encoding="utf-8")
    assert "fracture gate runtime wiring specification" in text
    assert "PressureSigmaThetaFractureCriterionGuard" in text


def test_status_present() -> None:
    assert (
        spec_tool.build_spec()["runtime_wiring_spec_status"]
        == "FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED"
    )


def test_requires_fracture_model_selector() -> None:
    assert "FractureModelSelector" in spec_tool.build_spec()["required_components"]


def test_requires_sigmatheta_initial_state_guard() -> None:
    assert "SigmaThetaInitialStateGuard" in spec_tool.build_spec()["required_components"]


def test_requires_pressure_sigmatheta_guard() -> None:
    assert (
        "PressureSigmaThetaFractureCriterionGuard"
        in spec_tool.build_spec()["required_components"]
    )


def test_runtime_wiring_allowed_next_false() -> None:
    assert spec_tool.build_spec()["runtime_wiring_allowed_next"] is False


def test_runtime_execution_allowed_next_false() -> None:
    assert spec_tool.build_spec()["runtime_execution_allowed_next"] is False


def test_buz29_execution_allowed_next_false() -> None:
    assert spec_tool.build_spec()["buz29_execution_allowed_next"] is False


def test_pkn_behavior_change_allowed_false() -> None:
    assert spec_tool.build_spec()["pkn_behavior_change_allowed"] is False


def test_penny_shaped_diagnostic_only_true() -> None:
    assert spec_tool.build_spec()["penny_shaped_diagnostic_only"] is True


def test_gate_states_include_sigmatheta_block() -> None:
    states = spec_tool.build_spec()["gate_states"]

    assert "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE" in states


def test_required_fields_include_pressure_and_margin() -> None:
    fields = spec_tool.build_spec()["required_fields"]

    assert "wellbore_pressure_Pa" in fields
    assert "fracture_margin_Pa" in fields


def test_blocking_rules_preserve_pkn_and_block_penny() -> None:
    rules = "\n".join(spec_tool.build_spec()["blocking_rules"])

    assert "PKN default must preserve existing behavior" in rules
    assert "PENNY_SHAPED remains diagnostic_only" in rules
    assert "PressureSigmaThetaFractureCriterionGuard must pass" in rules
