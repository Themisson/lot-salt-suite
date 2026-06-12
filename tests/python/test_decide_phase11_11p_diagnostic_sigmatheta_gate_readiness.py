import json
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType


SCRIPT = Path("tools/decide_phase11_11p_diagnostic_sigmatheta_gate_readiness.py")
GATE = Path("tests/fixtures/comparison/level1_readiness_gate.json")


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase11_11p_decision", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        text=True,
    )


def load_decision(tmp_path: Path) -> dict:
    output = tmp_path / "decision.json"
    run_script("--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    assert "Phase 11.11P" in SCRIPT.read_text(encoding="utf-8")


def test_generates_json(tmp_path: Path) -> None:
    data = load_decision(tmp_path)
    assert data["phase"] == "11.11P"
    assert data["readiness_status"] == "DIAGNOSTIC_SIGMATHETA_GATE_READY"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "decision.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_SIGMATHETA_GATE_READY" in text
    assert "PHASE11_11Q_SPECIFY_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH" in text


def test_ready_for_diagnostic_use_true(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["ready_for_diagnostic_use"] is True


def test_ready_for_physical_validation_false(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["ready_for_physical_validation"] is False


def test_ready_for_physical_dispatch_false(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["ready_for_physical_dispatch"] is False


def test_ready_for_real_source_integration_spec_true(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["ready_for_real_source_integration_spec"] is True


def test_runtime_dispatch_enabled_false(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["runtime_dispatch_enabled"] is False


def test_buz29_execution_allowed_false(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["buz29_execution_allowed"] is False


def test_pkn_behavior_change_allowed_false(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["pkn_behavior_change_allowed"] is False


def test_penny_shaped_runtime_enabled_false(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["penny_shaped_runtime_enabled"] is False


def test_pkn_outputs_unchanged_true(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["pkn_outputs_unchanged"] is True


def test_diagnostic_output_isolated_true(tmp_path: Path) -> None:
    assert load_module().build_decision(GATE)["diagnostic_output_isolated"] is True


def test_recommended_next_phase(tmp_path: Path) -> None:
    assert (
        load_module().build_decision(GATE)["recommended_next_phase"]
        == "PHASE11_11Q_SPECIFY_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH"
    )
