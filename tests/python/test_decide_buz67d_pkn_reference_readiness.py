import json
import subprocess
import sys
from pathlib import Path

from tools.decide_buz67d_pkn_reference_readiness import (
    BLOCKED_STATUS,
    READY_STATUS,
    decide_readiness,
)


SCRIPT = Path("tools/decide_buz67d_pkn_reference_readiness.py")
CASE = Path("cases/lot_tese_migrated/buz67d_pkn.yaml")


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
    assert "Decide BUZ67D PKN diagnostic reference readiness" in result.stdout


def test_buz67d_pkn_is_ready_for_diagnostic_reference() -> None:
    result = decide_readiness(CASE)
    assert result["readiness_status"] == READY_STATUS
    assert result["buz67d_pkn_validate_ok"] is True
    assert result["buz67d_pkn_run_allowed"] is True
    assert result["buz67d_is_pkn"] is True


def test_safety_flags_remain_closed() -> None:
    result = decide_readiness(CASE)
    assert result["physical_validation_claimed"] is False
    assert result["legacy_equivalence_claimed"] is False
    assert result["buz29_penny_executed"] is False
    assert result["runtime_dispatch_enabled"] is False
    assert result["pkn_behavior_changed"] is False


def test_missing_case_blocks(tmp_path: Path) -> None:
    result = decide_readiness(tmp_path / "missing.yaml")
    assert result["readiness_status"] == BLOCKED_STATUS
    assert result["buz67d_pkn_validate_ok"] is False


def test_non_pkn_case_blocks(tmp_path: Path) -> None:
    case = tmp_path / "buz67d.yaml"
    case.write_text("metadata:\n  name: buz67d\nlot:\n  model: penny\n", encoding="utf-8")
    result = decide_readiness(case)
    assert result["readiness_status"] == BLOCKED_STATUS
    assert result["buz67d_is_pkn"] is False


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "readiness.json"
    output_md = tmp_path / "readiness.md"
    result = run_script("--output-json", str(output_json), "--output-md", str(output_md))
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["readiness_status"] == READY_STATUS
    assert "BUZ67D_PKN_READY_FOR_DIAGNOSTIC_REFERENCE" in output_md.read_text(
        encoding="utf-8"
    )
