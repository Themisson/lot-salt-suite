import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.audit_buz29_penny_diagnostic_runner import (
    FIXTURE_DIR,
    RUNNER_STATUS,
    audit_runner,
)


SCRIPT = Path("tools/audit_buz29_penny_diagnostic_runner.py")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def copy_fixtures(tmp_path: Path) -> Path:
    target = tmp_path / "fixtures"
    shutil.copytree(FIXTURE_DIR, target)
    return target


def test_help() -> None:
    result = run_script("--help")
    assert result.returncode == 0
    assert "BUZ29/PENNY diagnostic runner" in result.stdout


def test_valid_fixtures_report_runner_implemented_inputs_partial() -> None:
    report = audit_runner(FIXTURE_DIR)
    assert report["runner_status"] == RUNNER_STATUS
    assert report["synthetic_complete_case_runs"] is True
    assert report["buz29_candidate_inputs_complete"] is False


def test_partial_inputs_blocked() -> None:
    report = audit_runner(FIXTURE_DIR)
    assert report["partial_inputs_blocked"] is True


def test_invalid_flags_rejected() -> None:
    report = audit_runner(FIXTURE_DIR)
    assert report["invalid_flags_rejected"] is True


def test_unsupported_model_rejected() -> None:
    report = audit_runner(FIXTURE_DIR)
    assert report["unsupported_model_rejected"] is True


def test_safety_flags_remain_closed() -> None:
    report = audit_runner(FIXTURE_DIR)
    assert report["diagnostic_only"] is True
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False
    assert report["runtime_dispatch_enabled"] is False
    assert report["penny_shaped_runtime_enabled"] is False
    assert report["pkn_behavior_changed"] is False


def test_json_and_markdown_are_written(tmp_path: Path) -> None:
    output_json = tmp_path / "runner.json"
    output_md = tmp_path / "runner.md"
    result = run_script(
        "--fixtures-dir",
        str(FIXTURE_DIR),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    )
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["runner_status"] == RUNNER_STATUS
    assert RUNNER_STATUS in output_md.read_text(encoding="utf-8")


def test_missing_fixture_makes_runner_inconclusive(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    (fixtures / "runner_valid_complete_inputs.json").unlink()
    output_json = tmp_path / "runner.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output_json),
        check=False,
    )
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert payload["runner_status"] == "BUZ29_PENNY_DIAGNOSTIC_RUNNER_INCONCLUSIVE"


def test_invalid_fixture_flag_is_rejected(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    path = fixtures / "runner_invalid_runtime_dispatch_true.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["runtime_dispatch_enabled"] = False
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    output_json = tmp_path / "runner.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output_json),
        check=False,
    )
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert any("runtime dispatch invalid fixture" in item for item in report["errors"])
