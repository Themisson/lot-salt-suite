import json
import subprocess
import sys
from pathlib import Path

from tools.decide_controlled_physical_comparison_readiness import (
    ANALYTIC_ONLY_STATUS,
    BLOCKED_REFERENCE_STATUS,
    READY_STATUS,
    build_decision,
)


SCRIPT = Path("tools/decide_controlled_physical_comparison_readiness.py")


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
    assert "controlled BUZ/legacy comparison gate" in result.stdout


def test_ready_for_buz_or_legacy_gate() -> None:
    decision = build_decision(reference_within_tolerance=True, pkn_regression_ok=True)
    assert decision["readiness_status"] == READY_STATUS
    assert decision["ready_for_buz_or_legacy_gate"] is True
    assert decision["recommended_next_phase"] == "PHASE_PREPARE_BUZ_OR_LEGACY_COMPARISON_GATE"


def test_physical_validation_and_legacy_equivalence_remain_disallowed() -> None:
    decision = build_decision(reference_within_tolerance=True, pkn_regression_ok=True)
    assert decision["ready_for_physical_validation"] is False
    assert decision["ready_for_physical_dispatch"] is False
    assert decision["legacy_equivalence_allowed"] is False
    assert decision["runtime_dispatch_enabled"] is False
    assert decision["buz29_execution_allowed"] is False
    assert decision["pkn_behavior_change_allowed"] is False


def test_pkn_regression_failure_stays_analytic_only() -> None:
    decision = build_decision(reference_within_tolerance=True, pkn_regression_ok=False)
    assert decision["readiness_status"] == ANALYTIC_ONLY_STATUS
    assert decision["ready_for_buz_or_legacy_gate"] is False


def test_reference_failure_blocks_gate() -> None:
    decision = build_decision(reference_within_tolerance=False, pkn_regression_ok=True)
    assert decision["readiness_status"] == BLOCKED_REFERENCE_STATUS
    assert decision["ready_for_buz_or_legacy_gate"] is False


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "readiness.json"
    output_md = tmp_path / "readiness.md"
    result = run_script("--output-json", str(output_json), "--output-md", str(output_md))
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["readiness_status"] == READY_STATUS
    assert payload["ready_for_physical_validation"] is False
    assert "READY_FOR_BUZ_OR_LEGACY_COMPARISON_GATE" in output_md.read_text(
        encoding="utf-8"
    )
