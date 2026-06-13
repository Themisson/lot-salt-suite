import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.run_first_controlled_reference_comparison import (
    INVALID_STATUS,
    VALID_STATUS,
    run_comparison,
)


SCRIPT = Path("tools/run_first_controlled_reference_comparison.py")
FIXTURE = Path(
    "tests/fixtures/comparison/phase_first_controlled_reference/"
    "axisymmetric_reference_cases.json"
)


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
    assert "first controlled axisymmetric reference comparison" in result.stdout


def test_controlled_reference_is_valid() -> None:
    result = run_comparison(FIXTURE)
    assert result["comparison_status"] == VALID_STATUS
    assert result["reference_type"] == "ANALYTIC_AXISYMMETRIC_CONTROLLED_REFERENCE"
    assert result["case_count"] == 7
    assert result["max_abs_error_Pa"] == pytest.approx(0.0)
    assert result["within_tolerance"] is True


def test_safety_flags_remain_closed() -> None:
    result = run_comparison(FIXTURE)
    assert result["physical_validation_claimed"] is False
    assert result["legacy_equivalence_claimed"] is False
    assert result["runtime_dispatch_enabled"] is False
    assert result["buz29_penny_executed"] is False
    assert result["pkn_behavior_changed"] is False


def test_required_threshold_cases_are_covered() -> None:
    result = run_comparison(FIXTURE)
    reached = {row["id"]: row["actual_fracture_initiated"] for row in result["cases"]}
    assert reached["compressive_not_reached"] is False
    assert reached["zero_hoop_not_reached"] is False
    assert reached["tension_below_strength_not_reached"] is False
    assert reached["tension_above_strength_reached"] is True
    assert reached["exact_threshold_reached"] is True
    assert reached["high_pressure_reached"] is True
    assert reached["low_pressure_compressive_safe"] is False


def test_invalid_reference_is_detected(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["cases"][0]["expected_fracture_margin_Pa"] += 1.0
    bad_fixture = tmp_path / "bad.json"
    bad_fixture.write_text(json.dumps(payload), encoding="utf-8")

    result = run_comparison(bad_fixture)
    assert result["comparison_status"] == INVALID_STATUS
    assert result["within_tolerance"] is False


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "result.json"
    output_md = tmp_path / "result.md"
    result = run_script("--output-json", str(output_json), "--output-md", str(output_md))
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["comparison_status"] == VALID_STATUS
    assert "FIRST_CONTROLLED_REFERENCE_COMPARISON_VALID" in output_md.read_text(
        encoding="utf-8"
    )
