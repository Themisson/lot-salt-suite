import json
from pathlib import Path

import pytest

from tools import decide_phase11_10x_runtime_integration_gate as gate_tool


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        gate_tool.main(["--help"])
    assert exc.value.code == 0
    assert "Phase 11.10X" in capsys.readouterr().out


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "gate.json"
    assert gate_tool.main(["--output-json", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["phase"] == "11.10X"
    assert payload["integration_gate_status"] == "RUNTIME_INTEGRATION_GATE_SPECIFIED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "gate.md"
    assert gate_tool.main(["--output-md", str(output)]) == 0

    text = output.read_text(encoding="utf-8")
    assert "runtime integration gate" in text
    assert "DIAGNOSTIC_PRE_RUNNER_OPT_IN" in text


def test_integration_gate_status_present() -> None:
    assert gate_tool.build_decision()["integration_gate_status"] == "RUNTIME_INTEGRATION_GATE_SPECIFIED"


def test_selected_integration_option_present() -> None:
    assert gate_tool.build_decision()["selected_integration_option"] == "DIAGNOSTIC_PRE_RUNNER_OPT_IN"


def test_implementation_allowed_next_present() -> None:
    assert gate_tool.build_decision()["implementation_allowed_next"] is True


def test_runtime_physical_dispatch_allowed_next_false() -> None:
    assert gate_tool.build_decision()["runtime_physical_dispatch_allowed_next"] is False


def test_buz29_execution_allowed_next_false() -> None:
    assert gate_tool.build_decision()["buz29_execution_allowed_next"] is False


def test_pkn_behavior_change_allowed_false() -> None:
    assert gate_tool.build_decision()["pkn_behavior_change_allowed"] is False


def test_requires_feature_flag_true() -> None:
    assert gate_tool.build_decision()["requires_feature_flag"] is True


def test_requires_diagnostic_output_isolation_true() -> None:
    assert gate_tool.build_decision()["requires_diagnostic_output_isolation"] is True


def test_recommended_next_phase_coherent() -> None:
    assert (
        gate_tool.build_decision()["recommended_next_phase"]
        == "PHASE11_10Y_IMPLEMENT_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE"
    )
