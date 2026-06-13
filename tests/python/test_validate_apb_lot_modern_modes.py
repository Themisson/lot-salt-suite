import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/validate_apb_lot_modern_modes.py")
FIXTURES = Path("tests/fixtures/comparison/phase_apb_lot_modern_modes")


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


def test_valid_fixture_directory(tmp_path: Path) -> None:
    output = tmp_path / "validation.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["validation_status"] == "APB_LOT_MODERN_MODES_VALID"
    assert payload["json_output_valid"] is True
    assert payload["legacy_modes_preserved"] is True
    assert payload["pkn_behavior_changed"] is False


def test_missing_fixture_is_partial(tmp_path: Path) -> None:
    partial = tmp_path / "fixtures"
    partial.mkdir()
    (partial / "modern_json_volume_balance_pre_iterative.yaml").write_text("x: y\n")
    output = tmp_path / "validation.json"
    result = run_script("--fixtures-dir", str(partial), "--output-json", str(output), check=False)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert payload["validation_status"] == "APB_LOT_MODERN_MODES_PARTIAL"
