import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/decide_phase11_11l_limited_gate_real_sigmatheta_readiness.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=True, text=True)


def load_decision(tmp_path: Path) -> dict:
    output = tmp_path / "decision.json"
    run_script("--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    assert "Phase 11.11L" in SCRIPT.read_text(encoding="utf-8")


def test_generates_json(tmp_path: Path) -> None:
    data = load_decision(tmp_path)
    assert data["phase"] == "11.11L"
    assert data["readiness_status"] == "LIMITED_GATE_REMAINS_DIAGNOSTIC_BLOCKED_BY_REAL_SOURCE"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "decision.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE" in text
    assert "implementation_allowed_next" in text


def test_implementation_not_allowed_next(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["implementation_allowed_next"] is False


def test_runtime_dispatch_not_allowed_next(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["runtime_dispatch_allowed_next"] is False


def test_buz29_not_allowed_next(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["buz29_execution_allowed_next"] is False


def test_pkn_behavior_change_not_allowed(tmp_path: Path) -> None:
    assert load_decision(tmp_path)["pkn_behavior_change_allowed"] is False


def test_decision_checks_keep_pressure_available_but_sigmatheta_missing(tmp_path: Path) -> None:
    checks = load_decision(tmp_path)["decision_checks"]
    assert checks["wellbore_pressure_runtime_available"] is True
    assert checks["sigma_theta_initial_runtime_available"] is False
    assert checks["sigma_theta_current_runtime_available"] is False


def test_next_phase_is_diagnostic_plan(tmp_path: Path) -> None:
    assert (
        load_decision(tmp_path)["recommended_next_phase"]
        == "PHASE11_11M_KEEP_LIMITED_GATE_DIAGNOSTIC_AND_PLAN_SIGMATHETA_SOURCE"
    )
