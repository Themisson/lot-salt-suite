import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/audit_phase11_11j_runtime_sigmatheta_pressure_availability.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=True, text=True)


def load_audit(tmp_path: Path) -> dict:
    output = tmp_path / "audit.json"
    run_script("--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    assert "Phase 11.11J" in SCRIPT.read_text(encoding="utf-8")


def test_generates_json(tmp_path: Path) -> None:
    data = load_audit(tmp_path)
    assert data["phase"] == "11.11J"
    assert data["audit_status"] == "RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE" in text
    assert "wellbore_pressure_runtime_available" in text


def test_initial_sigmatheta_runtime_is_not_available(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["sigma_theta_initial_runtime_available"] is False


def test_current_sigmatheta_runtime_is_not_available(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["sigma_theta_current_runtime_available"] is False


def test_wellbore_pressure_runtime_is_available(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["wellbore_pressure_runtime_available"] is True


def test_pressure_semantics_unresolved(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["pressure_semantics_resolved"] is False


def test_sign_convention_unresolved(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["sign_convention_resolved"] is False


def test_reference_frame_unresolved(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["reference_frame_resolved"] is False


def test_runtime_real_wiring_not_allowed_next(tmp_path: Path) -> None:
    assert load_audit(tmp_path)["runtime_real_wiring_allowed_next"] is False


def test_next_phase_is_post_drilling_initial_state_spec(tmp_path: Path) -> None:
    assert (
        load_audit(tmp_path)["recommended_next_phase"]
        == "PHASE11_11K_SPECIFY_POST_DRILLING_INITIAL_STATE_INTEGRATION"
    )
