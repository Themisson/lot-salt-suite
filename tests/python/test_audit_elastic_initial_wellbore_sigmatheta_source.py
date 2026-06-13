from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.audit_elastic_initial_wellbore_sigmatheta_source import (
    IMPLEMENTED_STATUS,
    audit,
    main,
)


FIXTURES_DIR = Path("tests/fixtures/comparison/phase_elastic_sigmatheta_source")


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/audit_elastic_initial_wellbore_sigmatheta_source.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "elastic initial wellbore sigma-theta source" in capsys.readouterr().out


def test_fixtures_are_valid() -> None:
    report = audit(FIXTURES_DIR)
    assert report["implementation_status"] == IMPLEMENTED_STATUS
    assert report["fixture_count"] == 9
    assert report["errors"] == []


def test_core_status_flags_are_safe() -> None:
    report = audit(FIXTURES_DIR)
    assert report["source"] == "ELASTIC_INITIAL_WELLBORE_STATE"
    assert report["semi_physical"] is True
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False
    assert report["runtime_dispatch_enabled"] is False
    assert report["buz29_execution_allowed"] is False
    assert report["pkn_behavior_changed"] is False
    assert report["penny_shaped_runtime_enabled"] is False


def test_ready_not_reached_case_is_valid() -> None:
    report = audit(FIXTURES_DIR)
    assert report["ready_not_reached_case_valid"] is True


def test_reached_pkn_case_is_valid() -> None:
    report = audit(FIXTURES_DIR)
    assert report["reached_pkn_case_valid"] is True


def test_reached_penny_case_remains_diagnostic() -> None:
    report = audit(FIXTURES_DIR)
    assert report["reached_penny_diagnostic_case_valid"] is True
    assert report["penny_shaped_runtime_enabled"] is False


def test_invalid_physical_validation_is_covered() -> None:
    report = audit(FIXTURES_DIR)
    assert report["physically_validated_true_invalid"] is True


def test_invalid_legacy_equivalence_is_covered() -> None:
    report = audit(FIXTURES_DIR)
    assert report["legacy_equivalent_true_invalid"] is True


def test_ambiguous_provider_and_input_is_covered() -> None:
    report = audit(FIXTURES_DIR)
    assert report["ambiguous_provider_input_invalid"] is True


def test_missing_required_fields_are_covered() -> None:
    report = audit(FIXTURES_DIR)
    assert report["missing_far_field_stress_invalid"] is True
    assert report["missing_wellbore_pressure_invalid"] is True


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "elastic_source.json"
    output_md = tmp_path / "elastic_source.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/audit_elastic_initial_wellbore_sigmatheta_source.py",
            "--fixtures-dir",
            str(FIXTURES_DIR),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["implementation_status"] == IMPLEMENTED_STATUS
    assert data["source"] == "ELASTIC_INITIAL_WELLBORE_STATE"
    assert IMPLEMENTED_STATUS in output_md.read_text(encoding="utf-8")


def test_missing_fixture_directory_is_invalid(tmp_path: Path) -> None:
    report = audit(tmp_path)
    assert report["implementation_status"] != IMPLEMENTED_STATUS
    assert report["fixture_count"] == 0
    assert report["errors"]
