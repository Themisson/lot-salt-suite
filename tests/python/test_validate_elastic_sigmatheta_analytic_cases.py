from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.validate_elastic_sigmatheta_analytic_cases import (
    VALID_STATUS,
    main,
    validate,
)


CASES_PATH = Path(
    "tests/fixtures/comparison/phase_elastic_sigmatheta_analytic/"
    "elastic_sigmatheta_analytic_cases.json"
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/validate_elastic_sigmatheta_analytic_cases.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "elastic sigma-theta analytic fixture cases" in capsys.readouterr().out


def test_validation_status_is_valid() -> None:
    report = validate(CASES_PATH)
    assert report["validation_status"] == VALID_STATUS
    assert report["case_count"] == 5
    assert report["errors"] == []


def test_formula_and_sign_convention_are_verified() -> None:
    report = validate(CASES_PATH)
    assert report["formula_verified"] is True
    assert report["sign_convention_verified"] is True
    assert report["threshold_behavior_verified"] is True


def test_safety_flags_are_closed() -> None:
    report = validate(CASES_PATH)
    assert report["semi_physical"] is True
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False
    assert report["runtime_dispatch_enabled"] is False
    assert report["buz29_execution_allowed"] is False
    assert report["pkn_behavior_changed"] is False
    assert report["penny_shaped_runtime_enabled"] is False


def test_exact_threshold_is_reached() -> None:
    report = validate(CASES_PATH)
    threshold = next(
        case for case in report["case_results"] if case["id"] == "exact_threshold_reached"
    )
    assert threshold["computed"]["fracture_margin_Pa"] == 0.0
    assert threshold["computed"]["gate_status"] == "Reached"
    assert threshold["computed"]["fracture_initiated"] is True


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "analytic.json"
    output_md = tmp_path / "analytic.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/validate_elastic_sigmatheta_analytic_cases.py",
            "--cases",
            str(CASES_PATH),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["validation_status"] == VALID_STATUS
    assert data["formula_verified"] is True
    assert "ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID" in output_md.read_text(
        encoding="utf-8"
    )


def test_missing_cases_file_is_inconclusive(tmp_path: Path) -> None:
    report = validate(tmp_path / "missing.json")
    assert report["validation_status"] != VALID_STATUS
    assert report["case_count"] == 0
    assert report["errors"]
