import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT = Path("tools/validate_phase11_10z_diagnostic_pre_runner_fixtures.py")
FIXTURES = Path("tests/fixtures/comparison/phase11_10z")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=check,
        text=True,
    )


def copy_fixtures(tmp_path: Path) -> Path:
    target = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, target)
    return target


def test_help() -> None:
    run_script("--help")
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.10Z" in text
    assert "--fixtures-dir" in text


def test_valid_fixture_directory_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["fixture_status"] == "DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID"
    assert data["fixture_count"] == 6


def test_valid_fixture_directory_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    run_script("--fixtures-dir", str(FIXTURES), "--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID" in text
    assert "PHASE11_11A_VALIDATE_DIAGNOSTIC_PRE_RUNNER_ON_CONTROLLED_CASES" in text


def test_default_disabled_fixture_is_covered(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["default_disabled_covered"] is True


def test_pkn_diagnostic_fixture_is_covered(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["pkn_diagnostic_covered"] is True


def test_penny_diagnostic_fixture_is_covered(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["penny_diagnostic_covered"] is True


def test_dispatch_true_invalid_fixture_is_covered(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["dispatch_true_invalid_covered"] is True


def test_invalid_mode_fixture_is_covered(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["invalid_mode_covered"] is True


def test_missing_sigmatheta_blocks_fixture_is_covered(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["missing_sigmatheta_blocks_covered"] is True


def test_missing_fixture_fails(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    (fixtures / "diagnostic_invalid_mode.yaml").unlink()
    output = tmp_path / "report.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output),
        check=False,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert data["fixture_status"] == "DIAGNOSTIC_PRE_RUNNER_FIXTURES_INVALID"


def test_runtime_dispatch_must_stay_false(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["runtime_physical_dispatch_enabled"] is False
    assert data["buz29_execution_allowed"] is False
    assert data["pkn_behavior_changed"] is False


def test_invalid_fixture_content_fails(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    path = fixtures / "diagnostic_enabled_pkn_pre_runner.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["lot"]["fracture"]["fracture_gate_diagnostics"]["dispatch_runtime_enabled"] = True
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    output = tmp_path / "report.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output),
        check=False,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert any("dispatch_runtime_enabled must be false" in item for item in data["errors"])
