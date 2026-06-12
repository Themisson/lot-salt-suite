import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import spec_phase11_11d_limited_fracture_gate_runtime_integration as tool  # noqa: E402


SCRIPT = Path("tools/spec_phase11_11d_limited_fracture_gate_runtime_integration.py")


def test_help_contract_is_declared() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11D" in text
    assert "--output-json" in text


def test_spec_status() -> None:
    data = tool.specification()
    assert (
        data["integration_spec_status"]
        == "LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_SPECIFIED"
    )


def test_next_implementation_allowed_but_dispatch_disabled() -> None:
    data = tool.specification()
    assert data["implementation_allowed_next"] is True
    assert data["runtime_dispatch_allowed_next"] is False
    assert data["runtime_physical_dispatch_allowed_next"] is False


def test_pkn_and_buz29_are_protected() -> None:
    data = tool.specification()
    assert data["pkn_behavior_change_allowed"] is False
    assert data["buz29_execution_allowed_next"] is False


def test_penny_remains_diagnostic_only() -> None:
    data = tool.specification()
    assert data["penny_runtime_allowed"] is False
    assert data["penny_diagnostic_only"] is True


def test_acceptance_gates_include_output_preservation() -> None:
    gates = tool.specification()["acceptance_gates_for_next_phase"]
    assert "diagnostic_enabled_preserves_result_json" in gates
    assert "diagnostic_enabled_preserves_timeseries_csv" in gates
    assert "diagnostic_json_isolated" in gates


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "spec.json"
    output_md = tmp_path / "spec.md"

    assert tool.main(["--output-json", str(output_json), "--output-md", str(output_md)]) == 0

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert (
        data["recommended_next_phase"]
        == "PHASE11_11E_IMPLEMENT_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION"
    )
    assert "Forbidden Changes" in output_md.read_text(encoding="utf-8")
