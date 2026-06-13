import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/compare_apb_lot_legacy_vs_modern_modes.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_help() -> None:
    assert run_script("--help").returncode == 0


def test_comparison_json(tmp_path: Path) -> None:
    output = tmp_path / "comparison.json"
    run_script("--output-json", str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["comparison_status"] == "APB_LOT_MODERN_MODE_COMPARISON_RECORDED"
    assert payload["modern_json_output_valid"] is True
    assert payload["legacy_dat_output_available"] is True
    assert payload["pkn_behavior_changed"] is False


def test_comparison_markdown(tmp_path: Path) -> None:
    output = tmp_path / "comparison.md"
    run_script("--output-md", str(output))
    assert "legacy versus modern" in output.read_text(encoding="utf-8")
