import json
import subprocess
import sys
from pathlib import Path

from tools.spec_phase11_11q_real_sigmatheta_source_integration_path import (
    build_specification,
)


SCRIPT = Path("tools/spec_phase11_11q_real_sigmatheta_source_integration_path.py")


def test_help() -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--help"], check=True, text=True)


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "spec.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-json", str(output)],
        check=True,
        text=True,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "11.11Q"
    assert data["integration_path_status"] == "REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "spec.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-md", str(output)],
        check=True,
        text=True,
    )
    text = output.read_text(encoding="utf-8")
    assert "REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED" in text
    assert "PHASE11_11R_CREATE_POST_DRILLING_SIGMATHETA_PROVIDER_FIXTURES" in text


def test_integration_path_status_present() -> None:
    assert build_specification()["integration_path_status"]


def test_primary_real_source_is_elastic_initial_wellbore_state() -> None:
    assert build_specification()["primary_real_source"] == "ELASTIC_INITIAL_WELLBORE_STATE"


def test_diagnostic_only_sources_include_explicit_input() -> None:
    assert "EXPLICIT_DIAGNOSTIC_INPUT" in build_specification()["diagnostic_only_sources"]


def test_diagnostic_only_sources_include_synthetic_fixture() -> None:
    assert "SYNTHETIC_FIXTURE" in build_specification()["diagnostic_only_sources"]


def test_legacy_trace_physical_validation_not_allowed() -> None:
    assert build_specification()["legacy_trace_physical_validation_allowed"] is False


def test_requires_post_drilling_state() -> None:
    assert build_specification()["requires_post_drilling_state"] is True


def test_lot_time_zero_is_not_drilling_time_zero() -> None:
    assert build_specification()["lot_time_zero_is_not_drilling_time_zero"] is True


def test_provider_contract_specified() -> None:
    assert build_specification()["provider_contract_specified"] is True


def test_implementation_allowed_next_false() -> None:
    assert build_specification()["implementation_allowed_next"] is False


def test_runtime_dispatch_allowed_next_false() -> None:
    assert build_specification()["runtime_dispatch_allowed_next"] is False


def test_buz29_execution_allowed_next_false() -> None:
    assert build_specification()["buz29_execution_allowed_next"] is False


def test_pkn_behavior_change_allowed_false() -> None:
    assert build_specification()["pkn_behavior_change_allowed"] is False


def test_recommended_next_phase() -> None:
    assert (
        build_specification()["recommended_next_phase"]
        == "PHASE11_11R_CREATE_POST_DRILLING_SIGMATHETA_PROVIDER_FIXTURES"
    )
