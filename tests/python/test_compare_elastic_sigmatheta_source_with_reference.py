import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.compare_elastic_sigmatheta_source_with_reference import (
    INVALID_STATUS,
    VALID_STATUS,
    compare_reference,
)


SCRIPT = Path("tools/compare_elastic_sigmatheta_source_with_reference.py")
FIXTURE = Path(
    "tests/fixtures/comparison/phase_elastic_sigmatheta_reference/"
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
    assert "Compare the axisymmetric elastic sigma-theta source" in result.stdout


def test_reference_fixture_is_valid() -> None:
    result = compare_reference(FIXTURE, tolerance_pa=1.0e-9)
    assert result["comparison_status"] == VALID_STATUS
    assert result["within_tolerance"] is True
    assert result["max_abs_error_Pa"] == pytest.approx(0.0)


def test_reference_does_not_claim_physical_validation() -> None:
    result = compare_reference(FIXTURE, tolerance_pa=1.0e-9)
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["legacy_trace_used_as_physical_validation"] is False
    assert result["runtime_dispatch_enabled"] is False
    assert result["buz29_execution_allowed"] is False


def test_threshold_behavior_matches_reference() -> None:
    result = compare_reference(FIXTURE, tolerance_pa=1.0e-9)
    reached = {row["case_id"]: row["actual_reached"] for row in result["cases"]}
    assert reached["compressive_not_reached"] is False
    assert reached["zero_threshold_reached"] is True
    assert reached["tension_below_strength_not_reached"] is False
    assert reached["tension_above_strength_reached"] is True


def test_invalid_reference_is_detected(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["cases"][0]["expected_sigma_theta_current_compression_positive_Pa"] += 1.0
    bad_fixture = tmp_path / "bad_reference.json"
    bad_fixture.write_text(json.dumps(payload), encoding="utf-8")

    result = compare_reference(bad_fixture, tolerance_pa=1.0e-9)
    assert result["comparison_status"] == INVALID_STATUS
    assert result["within_tolerance"] is False


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "comparison.json"
    output_md = tmp_path / "comparison.md"
    result = run_script("--output-json", str(output_json), "--output-md", str(output_md))
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["comparison_status"] == VALID_STATUS
    assert "ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_VALID" in output_md.read_text(
        encoding="utf-8"
    )
