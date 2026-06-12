import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/validate_phase11_11g_limited_gate_controlled_cases.py")
FIXTURES = Path("tests/fixtures/comparison/phase11_11f")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=check, text=True)


def load_report(tmp_path: Path) -> dict:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def test_help() -> None:
    run_script("--help")
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11G" in text
    assert "--fixtures-dir" in text


def test_generates_json(tmp_path: Path) -> None:
    data = load_report(tmp_path)
    assert data["phase"] == "11.11G"
    assert data["validation_status"] == "LIMITED_GATE_CONTROLLED_CASES_VALID"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    run_script("--fixtures-dir", str(FIXTURES), "--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "LIMITED_GATE_CONTROLLED_CASES_VALID" in text
    assert "PHASE11_11H_DECIDE_LIMITED_GATE_READINESS_FOR_RUNTIME_USE" in text


def test_validation_status_present(tmp_path: Path) -> None:
    assert load_report(tmp_path)["validation_status"]


def test_limited_gate_opt_in_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["limited_gate_opt_in_valid"] is True


def test_default_disabled_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["default_disabled_valid"] is True


def test_pkn_limited_gate_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["pkn_limited_gate_valid"] is True


def test_penny_diagnostic_only_valid(tmp_path: Path) -> None:
    assert load_report(tmp_path)["penny_diagnostic_only_valid"] is True


def test_dispatch_true_rejected(tmp_path: Path) -> None:
    assert load_report(tmp_path)["dispatch_true_rejected"] is True


def test_missing_sigmatheta_blocks(tmp_path: Path) -> None:
    assert load_report(tmp_path)["missing_sigmatheta_blocks"] is True


def test_invalid_model_blocked(tmp_path: Path) -> None:
    assert load_report(tmp_path)["invalid_model_blocked"] is True


def test_physical_outputs_identical(tmp_path: Path) -> None:
    assert load_report(tmp_path)["physical_outputs_identical"] is True


def test_diagnostic_output_isolated(tmp_path: Path) -> None:
    assert load_report(tmp_path)["diagnostic_output_isolated"] is True


def test_runtime_dispatch_enabled_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["runtime_dispatch_enabled"] is False


def test_buz29_execution_allowed_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["buz29_execution_allowed"] is False


def test_pkn_behavior_changed_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["pkn_behavior_changed"] is False


def test_penny_shaped_runtime_enabled_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["penny_shaped_runtime_enabled"] is False


def test_missing_fixture_is_invalid(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, fixtures)
    (fixtures / "limited_gate_missing_sigmatheta_blocks.yaml").unlink()
    output = tmp_path / "report.json"
    result = run_script("--fixtures-dir", str(fixtures), "--output-json", str(output), check=False)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert data["validation_status"] == "LIMITED_GATE_CONTROLLED_CASES_INVALID"
