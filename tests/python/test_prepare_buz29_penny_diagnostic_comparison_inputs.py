import json
import subprocess
import sys
from pathlib import Path

from tools.prepare_buz29_penny_diagnostic_comparison_inputs import (
    BLOCKED_STATUS,
    DEFAULT_MANIFEST,
    PREPARED_STATUS,
    prepare_inputs,
)


SCRIPT = Path("tools/prepare_buz29_penny_diagnostic_comparison_inputs.py")


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
    assert "Prepare BUZ29/PENNY diagnostic comparison inputs" in result.stdout


def test_manifest_is_prepared() -> None:
    result = prepare_inputs(DEFAULT_MANIFEST)
    assert result["input_status"] == PREPARED_STATUS
    assert result["required_inputs_count"] == 7
    assert result["available_inputs_sufficient_for_diagnostic_gate"] is True


def test_execution_stays_blocked_and_diagnostic_only() -> None:
    result = prepare_inputs(DEFAULT_MANIFEST)
    assert result["execution_allowed"] is False
    assert result["diagnostic_only"] is True
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["runtime_dispatch_enabled"] is False


def test_required_caveats_are_present() -> None:
    result = prepare_inputs(DEFAULT_MANIFEST)
    caveats = set(result["blocking_caveats"])
    assert "NO_PHYSICAL_VALIDATION" in caveats
    assert "NO_LEGACY_EQUIVALENCE" in caveats
    assert "NO_RUNTIME_DISPATCH" in caveats


def test_missing_input_blocks(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    payload["available_inputs"].remove("sigma_theta_source")
    payload["missing_inputs"] = ["sigma_theta_source"]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    result = prepare_inputs(manifest)
    assert result["input_status"] == BLOCKED_STATUS
    assert result["available_inputs_sufficient_for_diagnostic_gate"] is False


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "inputs.json"
    output_md = tmp_path / "inputs.md"
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
    assert payload["input_status"] == PREPARED_STATUS
    assert "BUZ29_PENNY_DIAGNOSTIC_INPUTS_PREPARED" in output_md.read_text(
        encoding="utf-8"
    )
