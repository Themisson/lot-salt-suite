import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/decide_apb_lot_modern_modes_default.py")


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


def test_default_decision_json(tmp_path: Path) -> None:
    output = tmp_path / "decision.json"
    run_script("--output-json", str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["decision_status"] == "APB_LOT_MODERN_MODES_READY_AS_DEFAULT_FOR_NEW_CASES"
    assert payload["default_output_format_for_new_cases"] == "json"
    assert payload["default_leakoff_coupling_mode"] == "volume_balance"
    assert payload["default_salt_displacement_mode"] == "pre_iterative"
    assert payload["pkn_behavior_changed"] is False


def test_opt_in_only_decision(tmp_path: Path) -> None:
    output = tmp_path / "decision.json"
    run_script("--opt-in-only", "--output-json", str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["decision_status"] == "APB_LOT_MODERN_MODES_READY_OPT_IN_ONLY"


def test_decision_markdown(tmp_path: Path) -> None:
    output = tmp_path / "decision.md"
    run_script("--output-md", str(output))
    assert "default decision" in output.read_text(encoding="utf-8")
