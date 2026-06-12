from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import audit_phase11_10s_pressure_sigmatheta_fracture_criterion_guard as audit_tool


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        audit_tool.main(["--help"])
    assert exc.value.code == 0
    assert "Phase 11.10S" in capsys.readouterr().out


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"

    assert audit_tool.main(["--output-json", str(output)]) == 0

    data = json.loads(output.read_text(encoding="utf-8"))
    assert (
        data["implementation_status"]
        == "PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED"
    )


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"

    assert audit_tool.main(["--output-md", str(output)]) == 0

    text = output.read_text(encoding="utf-8")
    assert "pressure x sigma-theta fracture criterion guard" in text
    assert "FRACTURE_CRITERION_BLOCKED_INVALID_SIGMATHETA" in text


def test_implementation_status_present() -> None:
    data = audit_tool.build_audit()

    assert (
        data["implementation_status"]
        == "PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED"
    )


def test_sigma_theta_sign_convention_is_compression_positive() -> None:
    data = audit_tool.build_audit()

    assert data["sigma_theta_sign_convention"] == "COMPRESSION_POSITIVE"


def test_preferred_criterion_uses_negative_tensile_strength_form() -> None:
    data = audit_tool.build_audit()

    assert (
        "sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa"
        in data["preferred_criterion"]
    )


def test_forbidden_shortcut_present() -> None:
    data = audit_tool.build_audit()

    assert (
        data["forbidden_shortcut"]
        == "pressure_greater_than_sigma_theta_without_sign_reference_transform"
    )


def test_dispatch_allowed_next_false() -> None:
    assert audit_tool.build_audit()["dispatch_allowed_next"] is False


def test_runtime_execution_allowed_next_false() -> None:
    assert audit_tool.build_audit()["runtime_execution_allowed_next"] is False


def test_buz29_execution_allowed_next_false() -> None:
    assert audit_tool.build_audit()["buz29_execution_allowed_next"] is False


def test_parser_schema_changed_false() -> None:
    assert audit_tool.build_audit()["parser_schema_changed"] is False


def test_runtime_dispatch_changed_false() -> None:
    assert audit_tool.build_audit()["runtime_dispatch_changed"] is False


def test_lot_pkn_behavior_changed_false() -> None:
    assert audit_tool.build_audit()["lot_pkn_behavior_changed"] is False
