import json
import subprocess
import sys
from pathlib import Path

from tools.audit_sigmatheta_provider_pre_runner_wiring import build_audit


SCRIPT = Path("tools/audit_sigmatheta_provider_pre_runner_wiring.py")


def test_help() -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--help"], check=True, text=True)


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-json", str(output)],
        check=True,
        text=True,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["wiring_status"] == "SIGMATHETA_PROVIDER_WIRED_TO_DIAGNOSTIC_PRE_RUNNER"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-md", str(output)],
        check=True,
        text=True,
    )
    assert "FractureGateDiagnosticPreRunner" in output.read_text(encoding="utf-8")


def test_runtime_dispatch_remains_false() -> None:
    assert build_audit()["runtime_dispatch_enabled"] is False


def test_pkn_behavior_unchanged() -> None:
    assert build_audit()["pkn_behavior_changed"] is False


def test_no_physical_gate_calls() -> None:
    audit = build_audit()
    assert audit["pkn_model_called_by_gate"] is False
    assert audit["pkn_runner_called_by_gate"] is False
    assert audit["penny_adapter_called_by_gate"] is False


def test_provider_centralizes_normalization() -> None:
    assert build_audit()["provider_centralizes_source_normalization"] is True
