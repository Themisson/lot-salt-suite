import json
import subprocess
import sys
from pathlib import Path

import yaml

from tools.audit_elastic_sigmatheta_upgrade_source import (
    IMPLEMENTED_STATUS,
    SOURCE,
    audit,
)


FIXTURES = Path("tests/fixtures/comparison/phase_elastic_sigmatheta_upgrade")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/audit_elastic_sigmatheta_upgrade_source.py", *args],
        check=False,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_help() -> None:
    completed = run_cli("--help")
    assert completed.returncode == 0
    assert "axisymmetric elastic sigma-theta" in completed.stdout


def test_fixtures_are_valid() -> None:
    result = audit(FIXTURES)
    assert result["implementation_status"] == IMPLEMENTED_STATUS
    assert result["source"] == SOURCE
    assert result["fixture_count"] == 5
    assert result["metadata_valid"] is True


def test_safety_flags_remain_closed() -> None:
    result = audit(FIXTURES)
    assert result["runtime_dispatch_enabled"] is False
    assert result["buz29_execution_allowed"] is False
    assert result["pkn_behavior_changed"] is False
    assert result["penny_shaped_runtime_enabled"] is False
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False


def test_ready_and_reached_cases_are_covered() -> None:
    result = audit(FIXTURES)
    assert result["ready_not_reached_case_valid"] is True
    assert result["reached_pkn_case_valid"] is True
    assert result["reached_penny_diagnostic_case_valid"] is True


def test_invalid_safety_flags_are_covered() -> None:
    result = audit(FIXTURES)
    assert result["physically_validated_true_invalid"] is True
    assert result["legacy_equivalent_true_invalid"] is True


def test_fixture_uses_axisymmetric_source() -> None:
    data = yaml.safe_load(
        (FIXTURES / "axisymmetric_provider_reached_pkn.yaml").read_text(
            encoding="utf-8"
        )
    )
    provider = data["lot"]["fracture"]["sigma_theta_provider"]
    assert provider["source"] == SOURCE


def test_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"
    completed = run_cli(
        "--fixtures-dir",
        str(FIXTURES),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    )
    assert completed.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["implementation_status"] == IMPLEMENTED_STATUS
    assert SOURCE in output_md.read_text(encoding="utf-8")


def test_missing_fixture_directory_is_invalid(tmp_path: Path) -> None:
    result = audit(tmp_path)
    assert result["implementation_status"] == "ELASTIC_SIGMATHETA_UPGRADE_SOURCE_INVALID"
    assert result["fixture_count"] == 0
