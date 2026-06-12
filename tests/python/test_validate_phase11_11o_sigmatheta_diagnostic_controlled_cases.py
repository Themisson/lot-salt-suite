import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/validate_phase11_11o_sigmatheta_diagnostic_controlled_cases.py")
FIXTURES = Path("tests/fixtures/comparison/phase11_11o")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=check, text=True)


def load_report(tmp_path: Path) -> dict:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11O" in text
    assert "--fixtures-dir" in text


def test_generates_json(tmp_path: Path) -> None:
    data = load_report(tmp_path)
    assert data["phase"] == "11.11O"
    assert data["validation_status"] == "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    run_script("--fixtures-dir", str(FIXTURES), "--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID" in text
    assert "PHASE11_11P_DECIDE_DIAGNOSTIC_SIGMATHETA_GATE_READINESS" in text


def test_validation_status_present(tmp_path: Path) -> None:
    assert load_report(tmp_path)["validation_status"]


def test_ready_not_reached_case_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["ready_not_reached_case_valid"] is True


def test_pkn_reached_case_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["pkn_reached_case_valid"] is True


def test_penny_reached_diagnostic_case_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["penny_reached_diagnostic_case_valid"] is True


def test_missing_sigmatheta_blocks(tmp_path: Path) -> None:
    assert load_report(tmp_path)["missing_sigmatheta_blocks"] is True


def test_physically_validated_true_rejected(tmp_path: Path) -> None:
    assert load_report(tmp_path)["physically_validated_true_rejected"] is True


def test_legacy_equivalent_true_rejected(tmp_path: Path) -> None:
    assert load_report(tmp_path)["legacy_equivalent_true_rejected"] is True


def test_runtime_dispatch_enabled_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["runtime_dispatch_enabled"] is False


def test_buz29_execution_allowed_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["buz29_execution_allowed"] is False


def test_pkn_behavior_changed_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["pkn_behavior_changed"] is False


def test_penny_shaped_runtime_enabled_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["penny_shaped_runtime_enabled"] is False


def test_diagnostic_output_isolated_true(tmp_path: Path) -> None:
    assert load_report(tmp_path)["diagnostic_output_isolated"] is True


def test_missing_fixture_is_invalid(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, fixtures)
    (fixtures / "controlled_pkn_reached.yaml").unlink()
    output = tmp_path / "report.json"
    result = run_script("--fixtures-dir", str(fixtures), "--output-json", str(output), check=False)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert data["validation_status"] != "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID"

