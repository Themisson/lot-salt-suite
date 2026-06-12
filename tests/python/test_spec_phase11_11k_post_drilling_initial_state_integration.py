import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/spec_phase11_11k_post_drilling_initial_state_integration.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=True, text=True)


def load_spec(tmp_path: Path) -> dict:
    output = tmp_path / "spec.json"
    run_script("--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    assert "Phase 11.11K" in SCRIPT.read_text(encoding="utf-8")


def test_generates_json(tmp_path: Path) -> None:
    data = load_spec(tmp_path)
    assert data["phase"] == "11.11K"
    assert data["integration_status"].startswith("POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED")


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "spec.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "PostDrillingInitialState" in text
    assert "POST_DRILLING_BEFORE_LOT" in text


def test_source_status_is_missing_runtime_sigmatheta_source(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["source_status"] == "MISSING_RUNTIME_SIGMATHETA_SOURCE"


def test_sign_convention_is_compression_positive(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["sign_convention"] == "COMPRESSION_POSITIVE"


def test_reference_frame_is_wellbore_wall_total_stress(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["reference_frame"] == "WELLBORE_WALL_TOTAL_STRESS"


def test_requires_post_drilling_state(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["requires_post_drilling_state"] is True


def test_implementation_not_allowed_next(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["implementation_allowed_next"] is False


def test_runtime_dispatch_not_allowed_next(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["runtime_dispatch_allowed_next"] is False


def test_buz29_not_allowed_next(tmp_path: Path) -> None:
    assert load_spec(tmp_path)["buz29_execution_allowed_next"] is False


def test_next_phase_is_limited_gate_real_sigmatheta_readiness(tmp_path: Path) -> None:
    assert (
        load_spec(tmp_path)["recommended_next_phase"]
        == "PHASE11_11L_DECIDE_LIMITED_GATE_REAL_SIGMATHETA_READINESS"
    )
