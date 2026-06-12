import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/decide_phase11_11h_limited_gate_runtime_readiness.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=True, text=True)


def load_decision(tmp_path: Path) -> dict:
    output = tmp_path / "decision.json"
    run_script("--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    assert "Phase 11.11H" in SCRIPT.read_text(encoding="utf-8")


def test_generates_json(tmp_path: Path) -> None:
    data = load_decision(tmp_path)
    assert data["phase"] == "11.11H"
    assert data["readiness_status"] == "LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "decision.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE" in text
    assert "PHASE11_11I_SPECIFY_REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY" in text


def test_readiness_status_present(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["readiness_status"]


def test_ready_for_diagnostic_runtime_use_true(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["ready_for_diagnostic_runtime_use"] is True


def test_ready_for_physical_dispatch_false(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["ready_for_physical_dispatch"] is False


def test_pkn_outputs_unchanged_true(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["pkn_outputs_unchanged"] is True


def test_diagnostic_output_isolated_true(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["diagnostic_output_isolated"] is True


def test_runtime_dispatch_enabled_false(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["runtime_dispatch_enabled"] is False


def test_buz29_execution_allowed_false(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["buz29_execution_allowed"] is False


def test_pkn_behavior_changed_false(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["pkn_behavior_changed"] is False


def test_penny_shaped_runtime_enabled_false(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["penny_shaped_runtime_enabled"] is False
