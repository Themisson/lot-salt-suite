from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "comparison" / "phase11_10e"
JSON_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_expected.json"
CSV_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_expected.csv"
METADATA_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_metadata.json"

sys.path.insert(0, str(ROOT))

from tools.spec_phase11_10f_penny_diagnostic_writer import (  # noqa: E402
    NEXT_IMPLEMENT,
    SPECIFIED_STATUS,
    build_parser,
    build_writer_spec,
    main,
    write_markdown,
)


def copy_fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    json_path = tmp_path / "penny.json"
    csv_path = tmp_path / "penny.csv"
    metadata_path = tmp_path / "metadata.json"
    json_path.write_text(JSON_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    csv_path.write_text(CSV_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    metadata_path.write_text(METADATA_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, csv_path, metadata_path


def test_help_mentions_penny_diagnostic_writer() -> None:
    help_text = build_parser().format_help()
    assert "PennyShaped diagnostic writer" in help_text
    assert "--fixture-json" in help_text
    assert "--fixture-csv" in help_text
    assert "--fixture-metadata" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "spec.json"
    exit_code = main(
        [
            "--fixture-json",
            str(JSON_FIXTURE),
            "--fixture-csv",
            str(CSV_FIXTURE),
            "--fixture-metadata",
            str(METADATA_FIXTURE),
            "--output-json",
            str(output_json),
        ]
    )
    assert exit_code == 0
    spec = json.loads(output_json.read_text(encoding="utf-8"))
    assert spec["phase"] == "11.10F"
    assert spec["writer_spec_status"] == SPECIFIED_STATUS


def test_generates_markdown(tmp_path: Path) -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    output_md = tmp_path / "spec.md"
    write_markdown(spec, output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "PennyShaped Diagnostic Writer Specification" in text
    assert "Required Outputs" in text
    assert "Conversion Rules" in text


def test_writer_spec_status() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert spec["writer_spec_status"] == SPECIFIED_STATUS


def test_implementation_allowed_false() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert spec["implementation_allowed"] is False


def test_runtime_execution_allowed_false() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert spec["runtime_execution_allowed"] is False


def test_requires_cpp_implementation_future_true() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert spec["requires_cpp_implementation_future"] is True


def test_fixture_contract_valid_true() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert spec["fixture_contract_valid"] is True


def test_required_outputs_present() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert "fracture_volume_proxy_1rad_m3" in spec["required_outputs"]
    assert "fracture_volume_equivalent_2pi_m3" in spec["required_outputs"]
    assert "solid_volume_equivalent_2pi_m3" in spec["required_outputs"]


def test_required_metadata_present() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert "required_caveats" in spec["required_metadata"]
    assert "forbidden_interpretations" in spec["required_metadata"]


def test_required_caveats_present() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI" in spec["required_caveats"]
    assert "IMPLEMENTATION_NOT_ALLOWED_IN_11_10F" in spec["required_caveats"]
    assert "RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F" in spec["required_caveats"]


def test_conversion_rules_present() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    rules = "\n".join(spec["conversion_rules"])
    assert "fracture_volume_equivalent_2pi_m3" in rules
    assert "solid_volume_equivalent_2pi_m3" in rules
    assert "volume_multiplier remains empirical" in rules


def test_forbidden_interpretations_present() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    forbidden = "\n".join(spec["forbidden_interpretations"])
    assert "Do not treat volume_multiplier as 2pi" in forbidden
    assert "Do not declare BUZ29-PENNY physical validation" in forbidden


def test_recommended_next_phase_is_implementation_opt_in() -> None:
    spec = build_writer_spec(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert spec["recommended_next_phase"] == NEXT_IMPLEMENT


def test_missing_json_fixture_errors(tmp_path: Path) -> None:
    _json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    with pytest.raises(FileNotFoundError):
        build_writer_spec(tmp_path / "missing.json", csv_path, metadata_path)


def test_missing_csv_fixture_errors(tmp_path: Path) -> None:
    json_path, _csv_path, metadata_path = copy_fixtures(tmp_path)
    with pytest.raises(FileNotFoundError):
        build_writer_spec(json_path, tmp_path / "missing.csv", metadata_path)


def test_missing_metadata_fixture_errors(tmp_path: Path) -> None:
    json_path, csv_path, _metadata_path = copy_fixtures(tmp_path)
    with pytest.raises(FileNotFoundError):
        build_writer_spec(json_path, csv_path, tmp_path / "missing_metadata.json")
