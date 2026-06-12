import json
from pathlib import Path

import pytest

from tools import audit_phase11_10w_fracture_gate_runtime_wiring as audit_tool


SCENARIOS = Path(
    "tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_scenarios.json"
)


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        audit_tool.main(["--help"])
    assert exc.value.code == 0
    assert "Phase 11.10W" in capsys.readouterr().out


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"

    assert audit_tool.main(["--scenarios", str(SCENARIOS), "--output-json", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["phase"] == "11.10W"
    assert payload["implementation_status"] == "FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"

    assert audit_tool.main(["--scenarios", str(SCENARIOS), "--output-md", str(output)]) == 0

    text = output.read_text(encoding="utf-8")
    assert "fracture gate runtime wiring audit" in text
    assert "FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED" in text


def test_implementation_status_present() -> None:
    payload = audit_tool.build_audit(SCENARIOS)
    assert payload["implementation_status"] == "FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED"


def test_runtime_wiring_component_created_true() -> None:
    assert audit_tool.build_audit(SCENARIOS)["runtime_wiring_component_created"] is True


def test_runtime_execution_enabled_false() -> None:
    assert audit_tool.build_audit(SCENARIOS)["runtime_execution_enabled"] is False


def test_buz29_execution_allowed_false() -> None:
    assert audit_tool.build_audit(SCENARIOS)["buz29_execution_allowed"] is False


def test_pkn_model_called_false() -> None:
    assert audit_tool.build_audit(SCENARIOS)["pkn_model_called"] is False


def test_penny_adapter_called_false() -> None:
    assert audit_tool.build_audit(SCENARIOS)["penny_adapter_called"] is False


def test_fixtures_covered_true() -> None:
    assert audit_tool.build_audit(SCENARIOS)["fixtures_covered"] is True
