import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/audit_phase11_10y_diagnostic_pre_runner_runtime_gate.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=True, text=True)


def test_help(tmp_path: Path) -> None:
    stdout_path = tmp_path / "help.txt"
    with stdout_path.open("w", encoding="utf-8") as stdout:
        subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=True,
            text=True,
            stdout=stdout,
        )
    text = stdout_path.read_text(encoding="utf-8")
    assert "Phase 11.10Y" in text
    assert "--output-json" in text


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10Y"
    assert data["integration_status"] == (
        "DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED"
    )


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED" in text
    assert "PHASE11_10Z_ADD_DIAGNOSTIC_PRE_RUNNER_CASE_FIXTURES" in text


def test_integration_status_present(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["integration_status"]


def test_diagnostic_opt_in_required_true(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["diagnostic_opt_in_required"] is True


def test_dispatch_runtime_enabled_allowed_false(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["dispatch_runtime_enabled_allowed"] is False


def test_runtime_physical_dispatch_enabled_false(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["runtime_physical_dispatch_enabled"] is False


def test_buz29_execution_allowed_false(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["buz29_execution_allowed"] is False


def test_pkn_behavior_changed_false(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["pkn_behavior_changed"] is False


def test_pkn_model_called_by_diagnostic_false(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["pkn_model_called_by_diagnostic"] is False


def test_penny_adapter_called_by_diagnostic_false(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["penny_adapter_called_by_diagnostic"] is False
