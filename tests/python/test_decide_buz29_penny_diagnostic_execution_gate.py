import json
import subprocess
import sys
from pathlib import Path

from tools.decide_buz29_penny_diagnostic_execution_gate import (
    ALLOWED_STATUS,
    BLOCKED_STATUS,
    DEFAULT_MANIFEST,
    decide_execution_gate,
)


SCRIPT = Path("tools/decide_buz29_penny_diagnostic_execution_gate.py")


def run_script(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def test_help() -> None:
    result = run_script("--help")
    assert result.returncode == 0
    assert "Decide the BUZ29/PENNY diagnostic execution gate" in result.stdout


def test_default_manifest_allows_future_diagnostic_execution() -> None:
    result = decide_execution_gate(DEFAULT_MANIFEST)
    assert result["gate_status"] == ALLOWED_STATUS
    assert result["execution_allowed_next"] is True
    assert result["recommended_next_phase"] == "PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_COMPARISON"


def test_gate_does_not_execute_or_enable_runtime_dispatch() -> None:
    result = decide_execution_gate(DEFAULT_MANIFEST)
    assert result["buz29_penny_executed_now"] is False
    assert result["runtime_dispatch_enabled"] is False
    assert result["pkn_behavior_change_allowed"] is False
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False


def test_physical_validation_flag_blocks(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    payload["physically_validated"] = True
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    result = decide_execution_gate(manifest)
    assert result["gate_status"] == BLOCKED_STATUS
    assert "SAFETY_FLAGS_NOT_DIAGNOSTIC_ONLY" in result["blocked_reasons"]


def test_missing_required_caveat_blocks(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    payload["blocking_caveats"] = ["NO_PHYSICAL_VALIDATION", "NO_RUNTIME_DISPATCH"]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    result = decide_execution_gate(manifest)
    assert result["gate_status"] == BLOCKED_STATUS
    assert "REQUIRED_CAVEATS_MISSING" in result["blocked_reasons"]


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "gate.json"
    output_md = tmp_path / "gate.md"
    result = run_script(
        "--manifest",
        str(DEFAULT_MANIFEST),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    )
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["gate_status"] == ALLOWED_STATUS
    assert "BUZ29_PENNY_DIAGNOSTIC_EXECUTION_ALLOWED_NEXT" in output_md.read_text(
        encoding="utf-8"
    )
