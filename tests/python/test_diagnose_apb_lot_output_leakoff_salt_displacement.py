import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/diagnose_apb_lot_output_leakoff_salt_displacement.py")


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
    result = run_script("--help")
    assert "APB/LOT output" in result.stdout


def test_diagnosis_json(tmp_path: Path) -> None:
    output = tmp_path / "diagnosis.json"
    result = run_script("--output-json", str(output))
    assert result.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["phase"] == "APB_LOT_OUTPUT_LEAKOFF_SALT_DISPLACEMENT_DIAGNOSIS"
    assert payload["implementation_allowed_next"] is True
    assert payload["recommended_next_phase"] == "APB_LOT_IMPLEMENT_JSON_OUTPUT_AND_MODES"


def test_diagnosis_markdown(tmp_path: Path) -> None:
    output = tmp_path / "diagnosis.md"
    run_script("--output-md", str(output))
    assert "APB/LOT output" in output.read_text(encoding="utf-8")
