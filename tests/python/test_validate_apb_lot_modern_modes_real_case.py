import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/validate_apb_lot_modern_modes_real_case.py")
FIXTURES = Path("tests/fixtures/comparison/phase_apb_lot_real_case")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=check,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_payload(tmp_path: Path) -> dict:
    output_json = tmp_path / "real_case_validation.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output_json))
    return json.loads(output_json.read_text(encoding="utf-8"))


def test_help() -> None:
    assert run_script("--help").returncode == 0


def test_generates_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "validation.json"
    output_md = tmp_path / "validation.md"
    run_script(
        "--fixtures-dir",
        str(FIXTURES),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    )
    assert output_json.exists()
    assert output_md.exists()


def test_validation_status_present(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["validation_status"]


def test_pkn_behavior_not_changed(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["pkn_behavior_changed"] is False


def test_buz29_penny_not_executed(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["buz29_penny_executed"] is False


def test_missing_runner_is_blocked(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["validation_status"] == "APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER"
    assert payload["real_case_runner_available"] is False
    assert payload["blocked_by_missing_runtime_integration"] is True


def test_writer_is_not_integrated_with_runtime(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["writer_available"] is True
    assert payload["writer_integrated_with_runtime"] is False


def test_contract_fixtures_cover_modern_and_legacy_modes(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["modern_fixture_available"] is True
    assert payload["legacy_fixture_available"] is True
    assert payload["legacy_modes_preserved"] is True
