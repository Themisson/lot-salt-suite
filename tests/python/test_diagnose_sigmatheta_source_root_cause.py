import json
import subprocess
import sys
from pathlib import Path

from tools.diagnose_sigmatheta_source_root_cause import build_diagnosis


SCRIPT = Path("tools/diagnose_sigmatheta_source_root_cause.py")


def test_help() -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--help"], check=True, text=True)


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "diagnosis.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-json", str(output)],
        check=True,
        text=True,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["diagnosis_status"] == "SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "diagnosis.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-md", str(output)],
        check=True,
        text=True,
    )
    text = output.read_text(encoding="utf-8")
    assert "PostDrillingSigmaThetaProvider" in text
    assert "implementation_allowed_next" in text


def test_initial_runtime_sigma_theta_missing() -> None:
    assert build_diagnosis()["sigma_theta_initial_runtime_available"] is False


def test_current_runtime_sigma_theta_missing() -> None:
    assert build_diagnosis()["sigma_theta_current_runtime_available"] is False


def test_wellbore_pressure_available() -> None:
    assert build_diagnosis()["wellbore_pressure_runtime_available"] is True


def test_elastic_provider_implementable() -> None:
    assert build_diagnosis()["elastic_provider_implementable"] is True


def test_implementation_allowed_next() -> None:
    assert build_diagnosis()["implementation_allowed_next"] is True


def test_recommended_solution_path() -> None:
    assert (
        build_diagnosis()["recommended_solution_path"]
        == "SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE"
    )


def test_pressure_semantics_not_physical_ready() -> None:
    assert build_diagnosis()["pressure_semantics_resolved"] is False


def test_sign_convention_not_runtime_resolved() -> None:
    assert build_diagnosis()["sign_convention_resolved"] is False


def test_reference_frame_not_runtime_resolved() -> None:
    assert build_diagnosis()["reference_frame_resolved"] is False


def test_constraints_keep_dispatch_off() -> None:
    constraints = build_diagnosis()["required_constraints"]
    assert "runtime_dispatch_enabled remains false" in constraints


def test_proposed_component() -> None:
    assert build_diagnosis()["proposed_component"] == "PostDrillingSigmaThetaProvider"
