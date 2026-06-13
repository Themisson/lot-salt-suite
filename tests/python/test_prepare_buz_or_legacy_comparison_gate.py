import json
import subprocess
import sys
from pathlib import Path

from tools.prepare_buz_or_legacy_comparison_gate import GATE_STATUS, build_gate


SCRIPT = Path("tools/prepare_buz_or_legacy_comparison_gate.py")


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
    assert "Prepare BUZ/legacy comparison gate" in result.stdout


def test_gate_is_prepared() -> None:
    gate = build_gate()
    assert gate["gate_status"] == GATE_STATUS
    assert gate["recommended_first_comparison"] == "ANALYTIC_OR_BUZ67D_PKN_DIAGNOSTIC"
    assert gate["recommended_next_phase"] == "PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON"


def test_buz29_penny_remains_blocked() -> None:
    gate = build_gate()
    assert gate["buz29_penny_execution_allowed"] is False
    candidate = {row["case_id"]: row for row in gate["candidate_cases"]}
    assert candidate["buz29_penny"]["allowed"] is False


def test_physical_and_legacy_equivalence_remain_blocked() -> None:
    gate = build_gate()
    assert gate["physical_validation_allowed"] is False
    assert gate["legacy_equivalence_allowed"] is False
    assert gate["runtime_dispatch_enabled"] is False
    assert gate["pkn_behavior_change_allowed"] is False
    assert gate["penny_shaped_runtime_enabled"] is False


def test_required_fields_are_listed() -> None:
    gate = build_gate()
    fields = set(gate["fields_to_align_before_comparison"])
    assert "wellbore_pressure_Pa" in fields
    assert "sigma_theta_current_compression_positive_Pa" in fields
    assert "sign_convention" in fields
    assert "pressure_semantics" in fields


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "gate.json"
    output_md = tmp_path / "gate.md"
    result = run_script("--output-json", str(output_json), "--output-md", str(output_md))
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["gate_status"] == GATE_STATUS
    assert payload["buz29_penny_execution_allowed"] is False
    assert "BUZ_OR_LEGACY_COMPARISON_GATE_PREPARED" in output_md.read_text(
        encoding="utf-8"
    )
