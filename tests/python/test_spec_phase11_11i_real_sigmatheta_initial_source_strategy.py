import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/spec_phase11_11i_real_sigmatheta_initial_source_strategy.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=True, text=True)


def load_strategy(tmp_path: Path) -> dict:
    output = tmp_path / "strategy.json"
    run_script("--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    assert "Phase 11.11I" in SCRIPT.read_text(encoding="utf-8")


def test_generates_json(tmp_path: Path) -> None:
    data = load_strategy(tmp_path)
    assert data["phase"] == "11.11I"
    assert data["strategy_status"] == "REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "strategy.md"
    run_script("--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "ELASTIC_INITIAL_WELLBORE_STATE" in text
    assert "post-drilling state" in text


def test_primary_source_is_elastic_initial_wellbore_state(tmp_path: Path) -> None:
    assert load_strategy(tmp_path)["primary_source"] == "ELASTIC_INITIAL_WELLBORE_STATE"


def test_fallback_sources_are_diagnostic_inputs(tmp_path: Path) -> None:
    data = load_strategy(tmp_path)
    assert data["fallback_sources"] == ["EXPLICIT_DIAGNOSTIC_INPUT", "SYNTHETIC_FIXTURE"]


def test_requires_post_drilling_state(tmp_path: Path) -> None:
    assert load_strategy(tmp_path)["requires_post_drilling_state"] is True


def test_lot_time_zero_is_not_drilling_time_zero(tmp_path: Path) -> None:
    assert load_strategy(tmp_path)["lot_time_zero_is_not_drilling_time_zero"] is True


def test_legacy_trace_not_physical_validation_source(tmp_path: Path) -> None:
    data = load_strategy(tmp_path)
    assert data["legacy_trace_validation_allowed"] is False
    assert "LEGACY_DIAGNOSTIC_TRACE" in data["not_validation_sources"]


def test_implementation_not_allowed_next(tmp_path: Path) -> None:
    assert load_strategy(tmp_path)["implementation_allowed_next"] is False


def test_next_phase_is_runtime_availability_audit(tmp_path: Path) -> None:
    assert (
        load_strategy(tmp_path)["recommended_next_phase"]
        == "PHASE11_11J_AUDIT_RUNTIME_SIGMATHETA_AND_PRESSURE_AVAILABILITY"
    )
