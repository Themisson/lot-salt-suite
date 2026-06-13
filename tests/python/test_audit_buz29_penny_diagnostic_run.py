import json
import subprocess
import sys
from pathlib import Path

from tools.audit_buz29_penny_diagnostic_run import (
    BLOCKED_STATUS,
    COMPLETED_STATUS,
    DEFAULT_SUMMARY,
    audit_diagnostic_run,
)


SCRIPT = Path("tools/audit_buz29_penny_diagnostic_run.py")


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
    assert "Audit the BUZ29/PENNY diagnostic run attempt" in result.stdout


def test_default_summary_records_blocked_run() -> None:
    result = audit_diagnostic_run(DEFAULT_SUMMARY)
    assert result["run_status"] == BLOCKED_STATUS
    assert result["execution_completed"] is False
    assert "BUZ29_PENNY_DIAGNOSTIC_RUNNER_NOT_AVAILABLE" in result["blocking_reasons"]


def test_safety_flags_remain_closed() -> None:
    result = audit_diagnostic_run(DEFAULT_SUMMARY)
    assert result["diagnostic_only"] is True
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["runtime_dispatch_enabled"] is False
    assert result["penny_shaped_runtime_enabled"] is False
    assert result["pkn_behavior_changed"] is False


def test_completed_fixture_is_accepted(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_SUMMARY.read_text(encoding="utf-8"))
    payload["execution_status"] = "BUZ29_PENNY_DIAGNOSTIC_RUN_COMPLETED"
    payload["execution_completed"] = True
    payload["diagnostic_runner_available"] = True
    payload["adapter_ready"] = True
    payload["blocking_reasons"] = []
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps(payload), encoding="utf-8")
    result = audit_diagnostic_run(summary)
    assert result["run_status"] == COMPLETED_STATUS
    assert result["recommended_next_phase"] == "PHASE_DECIDE_BUZ29_PENNY_DIAGNOSTIC_RUN_READINESS"


def test_runtime_dispatch_true_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_SUMMARY.read_text(encoding="utf-8"))
    payload["runtime_dispatch_enabled"] = True
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps(payload), encoding="utf-8")
    try:
        audit_diagnostic_run(summary)
    except ValueError as exc:
        assert "safety flags" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected safety flag rejection")


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "run.json"
    output_md = tmp_path / "run.md"
    result = run_script(
        "--summary",
        str(DEFAULT_SUMMARY),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    )
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["run_status"] == BLOCKED_STATUS
    assert "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED" in output_md.read_text(
        encoding="utf-8"
    )
