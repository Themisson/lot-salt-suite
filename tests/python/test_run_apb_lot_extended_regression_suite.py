import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/run_apb_lot_extended_regression_suite.py")
MANIFEST = Path(
    "tests/fixtures/comparison/phase_apb_lot_extended_regression/"
    "apb_lot_extended_regression_manifest.json"
)


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=check,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_help() -> None:
    assert run_script("--help").returncode == 0


def test_generates_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "regression.json"
    output_md = tmp_path / "regression.md"
    run_script("--manifest", str(MANIFEST), "--output-json", str(output_json), "--output-md", str(output_md))
    assert output_json.exists()
    assert output_md.exists()


def test_regression_status_present(tmp_path: Path) -> None:
    output_json = tmp_path / "regression.json"
    run_script("--manifest", str(MANIFEST), "--output-json", str(output_json))
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["regression_status"] == "APB_LOT_EXTENDED_REGRESSION_PASSED"


def test_modern_modes_valid(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["modern_modes_valid"] is True


def test_legacy_modes_valid(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["legacy_modes_valid"] is True


def test_invalid_modes_rejected(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["invalid_modes_rejected"] is True


def test_json_output_contract_valid(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["json_output_contract_valid"] is True


def test_output_name_rule_valid(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["output_name_rule_valid"] is True


def test_explicit_output_path_valid(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["explicit_output_path_valid"] is True


def test_legacy_modes_preserved(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["legacy_modes_preserved"] is True


def test_pkn_behavior_not_changed(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["pkn_behavior_changed"] is False


def test_buz29_penny_not_executed(tmp_path: Path) -> None:
    payload = run_payload(tmp_path)
    assert payload["buz29_penny_executed"] is False


def run_payload(tmp_path: Path) -> dict:
    output_json = tmp_path / "regression.json"
    run_script("--manifest", str(MANIFEST), "--output-json", str(output_json))
    return json.loads(output_json.read_text(encoding="utf-8"))
