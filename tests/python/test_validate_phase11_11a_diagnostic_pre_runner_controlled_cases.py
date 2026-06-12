import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/validate_phase11_11a_diagnostic_pre_runner_controlled_cases.py")
FIXTURES = Path("tests/fixtures/comparison/phase11_10z")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=check, text=True)


def test_help() -> None:
    run_script("--help")
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11A" in text
    assert "--fixtures-dir" in text


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "11.11A"
    assert data["validation_status"] == "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    run_script("--fixtures-dir", str(FIXTURES), "--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID" in text
    assert "PHASE11_11B_COMPARE_PKN_RESULTS_WITH_DIAGNOSTIC_DISABLED_ENABLED" in text


def test_validation_status_present(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["validation_status"]


def test_diagnostic_opt_in_behavior_valid(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["diagnostic_opt_in_behavior_valid"] is True


def test_default_disabled_behavior_valid(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["default_disabled_behavior_valid"] is True


def test_dispatch_runtime_enabled_true_rejected(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["dispatch_runtime_enabled_true_rejected"] is True


def test_invalid_mode_rejected(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["invalid_mode_rejected"] is True


def test_missing_sigmatheta_blocks(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["missing_sigmatheta_blocks"] is True


def test_diagnostic_output_isolated(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["diagnostic_output_isolated"] is True


def test_runtime_physical_dispatch_disabled(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["runtime_physical_dispatch_enabled"] is False


def test_buz29_execution_blocked(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    assert json.loads(output.read_text(encoding="utf-8"))["buz29_execution_allowed"] is False


def test_missing_fixture_is_invalid(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, fixtures)
    (fixtures / "diagnostic_missing_sigmatheta_blocks.yaml").unlink()
    output = tmp_path / "report.json"
    result = run_script("--fixtures-dir", str(fixtures), "--output-json", str(output), check=False)
    assert result.returncode == 1
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["validation_status"] == "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_INVALID"
