from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools.spec_phase11_10r_pressure_sigmatheta_fracture_criterion as spec_tool


def test_help_mentions_pressure_sigmatheta_criterion(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        spec_tool.main(["--help"])
    assert excinfo.value.code == 0
    assert "pressure x sigma-theta fracture criterion" in capsys.readouterr().out


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "criterion.json"
    assert spec_tool.main(["--output-json", str(output)]) == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10R"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "criterion.md"
    assert spec_tool.main(["--output-md", str(output)]) == 0
    text = output.read_text(encoding="utf-8")
    assert "preferred criterion" in text


def test_criterion_spec_status_present() -> None:
    data = spec_tool.build_spec()
    assert (
        data["criterion_spec_status"]
        == "PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED"
    )


def test_sigma_theta_sign_convention_is_compression_positive() -> None:
    data = spec_tool.build_spec()
    assert data["sigma_theta_sign_convention"] == "COMPRESSION_POSITIVE"


def test_pressure_semantics_required_true() -> None:
    data = spec_tool.build_spec()
    assert data["pressure_semantics_required"] is True


def test_guard_required_true() -> None:
    data = spec_tool.build_spec()
    assert data["guard_required"] is True


def test_forbidden_shortcut_present() -> None:
    data = spec_tool.build_spec()
    assert (
        data["forbidden_shortcut"]
        == "pressure_greater_than_sigma_theta_without_sign_reference_transform"
    )


def test_preferred_criterion_contains_required_expression() -> None:
    data = spec_tool.build_spec()
    assert (
        "sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa"
        in data["preferred_criterion"]
    )


def test_dispatch_allowed_next_false() -> None:
    data = spec_tool.build_spec()
    assert data["dispatch_allowed_next"] is False


def test_runtime_execution_allowed_next_false() -> None:
    data = spec_tool.build_spec()
    assert data["runtime_execution_allowed_next"] is False


def test_implementation_allowed_next_true() -> None:
    data = spec_tool.build_spec()
    assert data["implementation_allowed_next"] is True


def test_recommended_next_phase_is_criterion_guard() -> None:
    data = spec_tool.build_spec()
    assert (
        data["recommended_next_phase"]
        == "PHASE11_10S_IMPLEMENT_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD"
    )


@pytest.mark.parametrize(
    "state",
    [
        "FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY",
        "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN",
        "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN",
        "FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH",
        "FRACTURE_CRITERION_READY",
        "FRACTURE_NOT_INITIATED",
        "FRACTURE_INITIATED",
    ],
)
def test_required_criterion_states_present(state: str) -> None:
    data = spec_tool.build_spec()
    assert state in data["criterion_states"]


def test_required_fields_include_current_sigma_theta_and_tensile_strength() -> None:
    data = spec_tool.build_spec()
    assert "sigma_theta_current_compression_positive_Pa" in data["required_fields"]
    assert "tensile_strength_Pa" in data["required_fields"]
