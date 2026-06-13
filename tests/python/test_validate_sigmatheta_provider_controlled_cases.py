from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.validate_sigmatheta_provider_controlled_cases import (
    VALID_STATUS,
    main,
    validate,
)


FIXTURES_DIR = Path("tests/fixtures/comparison/phase_sigmatheta_provider")


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/validate_sigmatheta_provider_controlled_cases.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "diagnostic sigma-theta provider wiring" in capsys.readouterr().out


def test_fixtures_are_valid() -> None:
    report = validate(FIXTURES_DIR)
    assert report["validation_status"] == VALID_STATUS
    assert report["fixture_count"] == 7
    assert report["errors"] == []


def test_ready_not_reached_case_is_valid() -> None:
    report = validate(FIXTURES_DIR)
    assert report["ready_not_reached_case_valid"] is True


def test_pkn_reached_case_is_valid() -> None:
    report = validate(FIXTURES_DIR)
    assert report["pkn_reached_case_valid"] is True


def test_penny_reached_case_remains_diagnostic() -> None:
    report = validate(FIXTURES_DIR)
    assert report["penny_reached_diagnostic_case_valid"] is True
    assert report["penny_shaped_runtime_enabled"] is False


def test_unknown_source_invalid_is_covered() -> None:
    report = validate(FIXTURES_DIR)
    assert report["unknown_source_invalid"] is True


def test_physical_validation_claim_is_invalid() -> None:
    report = validate(FIXTURES_DIR)
    assert report["physically_validated_true_invalid"] is True


def test_legacy_equivalence_claim_is_invalid() -> None:
    report = validate(FIXTURES_DIR)
    assert report["legacy_equivalent_true_invalid"] is True


def test_safety_flags_are_false() -> None:
    report = validate(FIXTURES_DIR)
    assert report["runtime_dispatch_enabled"] is False
    assert report["buz29_execution_allowed"] is False
    assert report["pkn_behavior_changed"] is False
    assert report["penny_shaped_runtime_enabled"] is False


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "provider_cases.json"
    output_md = tmp_path / "provider_cases.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/validate_sigmatheta_provider_controlled_cases.py",
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
    assert data["validation_status"] == VALID_STATUS
    assert "SIGMATHETA_PROVIDER_CONTROLLED_CASES_VALID" in output_md.read_text(
        encoding="utf-8"
    )


def test_missing_fixture_is_partial(tmp_path: Path) -> None:
    report = validate(tmp_path)
    assert report["validation_status"] != VALID_STATUS
    assert report["fixture_count"] == 0
    assert report["errors"]

