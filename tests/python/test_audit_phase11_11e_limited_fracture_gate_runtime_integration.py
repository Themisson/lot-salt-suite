import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import audit_phase11_11e_limited_fracture_gate_runtime_integration as tool  # noqa: E402


SCRIPT = Path("tools/audit_phase11_11e_limited_fracture_gate_runtime_integration.py")


def test_help_contract_is_declared() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11E" in text
    assert "--output-json" in text
    assert "--output-md" in text


def test_build_audit_reports_implemented_status() -> None:
    audit = tool.build_audit()
    assert audit["integration_status"] == (
        "LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED"
    )
    assert audit["limited_gate_mode_supported"] is True
    assert audit["runtime_dispatch_enabled"] is False


def test_build_audit_rejects_runtime_dispatch() -> None:
    audit = tool.build_audit()
    assert audit["dispatch_runtime_enabled_true_rejected"] is True
    assert audit["physical_dispatch_enabled"] is False


def test_build_audit_keeps_pkn_outputs_unchanged() -> None:
    audit = tool.build_audit()
    assert audit["pkn_behavior_changed"] is False
    assert audit["pkn_outputs_unchanged"] is True
    assert audit["diagnostic_output_isolated"] is True


def test_build_audit_keeps_non_pkn_runtime_blocked() -> None:
    audit = tool.build_audit()
    assert audit["buz29_execution_allowed"] is False
    assert audit["penny_shaped_runtime_enabled"] is False
    assert audit["penny_shaped_adapter_called_by_gate_dispatch"] is False


def test_supported_modes_include_limited_gate() -> None:
    audit = tool.build_audit()
    assert audit["supported_modes"] == [
        "pre_runner",
        "diagnostic_only",
        "limited_gate",
    ]


def test_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"

    assert tool.main(["--output-json", str(output_json), "--output-md", str(output_md)]) == 0

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert payload["phase"] == "11.11E"
    assert "LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED" in markdown
    assert "limited_gate" in markdown
