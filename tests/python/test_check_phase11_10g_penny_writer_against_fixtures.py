from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "comparison" / "phase11_10e"
JSON_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_expected.json"
CSV_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_expected.csv"

sys.path.insert(0, str(ROOT))

from tools.check_phase11_10g_penny_writer_against_fixtures import (  # noqa: E402
    IMPLEMENTED_STATUS,
    NEXT_PHASE,
    build_parser,
    build_result,
    main,
    write_markdown,
)


def test_help_mentions_writer_fixture_check() -> None:
    help_text = build_parser().format_help()
    assert "PennyShaped diagnostic writer" in help_text
    assert "--fixture-json" in help_text
    assert "--fixture-csv" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "writer_check.json"
    exit_code = main(
        [
            "--fixture-json",
            str(JSON_FIXTURE),
            "--fixture-csv",
            str(CSV_FIXTURE),
            "--output-json",
            str(output_json),
        ]
    )

    assert exit_code == 0
    result = json.loads(output_json.read_text(encoding="utf-8"))
    assert result["phase"] == "11.10G"
    assert result["writer_implementation_status"] == IMPLEMENTED_STATUS


def test_generates_markdown(tmp_path: Path) -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    output_md = tmp_path / "writer_check.md"

    write_markdown(result, output_md)

    text = output_md.read_text(encoding="utf-8")
    assert "PennyShaped Writer Fixture Check" in text
    assert IMPLEMENTED_STATUS in text


def test_fixture_contract_valid_true() -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    assert result["fixture_contract_valid"] is True


def test_writer_implementation_status_present() -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    assert result["writer_implementation_status"] == IMPLEMENTED_STATUS


def test_runtime_execution_allowed_false() -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    assert result["runtime_execution_allowed"] is False


def test_buz29_executed_false() -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    assert result["buz29_executed"] is False


def test_physical_validation_and_legacy_equivalence_false() -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["active_simulation_case"] is False


def test_recommended_next_phase() -> None:
    result = build_result(JSON_FIXTURE, CSV_FIXTURE)
    assert result["recommended_next_phase"] == NEXT_PHASE


def test_missing_fixture_blocks(tmp_path: Path) -> None:
    result = build_result(tmp_path / "missing.json", CSV_FIXTURE)
    assert result["fixture_contract_valid"] is False
    assert result["writer_implementation_status"].endswith("_BLOCKED")
