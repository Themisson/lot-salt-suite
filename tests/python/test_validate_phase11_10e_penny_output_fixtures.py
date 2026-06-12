from __future__ import annotations

import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "comparison" / "phase11_10e"
JSON_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_expected.json"
CSV_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_expected.csv"
METADATA_FIXTURE = FIXTURE_DIR / "penny_diagnostic_output_metadata.json"

sys.path.insert(0, str(ROOT))

from tools.validate_phase11_10e_penny_output_fixtures import (  # noqa: E402
    VALID_STATUS,
    build_parser,
    main,
    validate_fixtures,
    write_markdown,
)


def copy_fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    json_path = tmp_path / "fixture.json"
    csv_path = tmp_path / "fixture.csv"
    metadata_path = tmp_path / "metadata.json"
    json_path.write_text(JSON_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    csv_path.write_text(CSV_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    metadata_path.write_text(METADATA_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, csv_path, metadata_path


def mutate_json(path: Path, key: str, value: object) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data[key] = value
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mutate_metadata(path: Path, key: str, value: object) -> None:
    mutate_json(path, key, value)


def test_cli_help() -> None:
    help_text = build_parser().format_help()
    assert "Validate Phase 11.10E PennyShaped diagnostic output fixtures" in help_text


def test_fixture_json_is_valid() -> None:
    result = validate_fixtures(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert result["fixture_status"] == VALID_STATUS
    assert result["json_fixture_valid"] is True


def test_fixture_csv_is_valid() -> None:
    result = validate_fixtures(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert result["csv_fixture_valid"] is True


def test_fixture_metadata_is_valid() -> None:
    result = validate_fixtures(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    assert result["metadata_fixture_valid"] is True


def test_fracture_volume_2pi_conversion_is_checked() -> None:
    data = json.loads(JSON_FIXTURE.read_text(encoding="utf-8"))
    assert math.isclose(
        data["fracture_volume_equivalent_2pi_m3"],
        data["fracture_volume_proxy_1rad_m3"] * math.tau,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


def test_solid_volume_2pi_conversion_is_checked() -> None:
    data = json.loads(JSON_FIXTURE.read_text(encoding="utf-8"))
    assert math.isclose(
        data["solid_volume_equivalent_2pi_m3"],
        data["solid_volume_1rad_m3"] * math.tau,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


def test_volume_multiplier_is_not_2pi() -> None:
    data = json.loads(JSON_FIXTURE.read_text(encoding="utf-8"))
    assert data["volume_multiplier_is_2pi"] is False
    assert not math.isclose(data["volume_multiplier"], math.tau, rel_tol=1e-12, abs_tol=1e-12)


def test_validator_rejects_volume_multiplier_equal_to_2pi(tmp_path: Path) -> None:
    json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    mutate_json(json_path, "volume_multiplier", math.tau)
    result = validate_fixtures(json_path, csv_path, metadata_path)
    assert result["fixture_status"] != VALID_STATUS
    assert any("volume_multiplier must not be interpreted as 2pi" in error for error in result["errors"])


def test_validator_rejects_missing_2pi_source(tmp_path: Path) -> None:
    json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    mutate_json(json_path, "fracture_volume_equivalent_2pi_source", "")
    result = validate_fixtures(json_path, csv_path, metadata_path)
    assert result["fixture_status"] != VALID_STATUS
    assert any("fracture_volume_equivalent_2pi_source is required" in error for error in result["errors"])


def test_validator_rejects_missing_required_caveat(tmp_path: Path) -> None:
    json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    data["required_caveats"] = [
        caveat for caveat in data["required_caveats"] if caveat != "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI"
    ]
    metadata_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    result = validate_fixtures(json_path, csv_path, metadata_path)
    assert result["fixture_status"] != VALID_STATUS
    assert any("metadata missing required caveat: VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI" in error for error in result["errors"])


def test_validator_requires_physically_validated_false(tmp_path: Path) -> None:
    json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    mutate_json(json_path, "physically_validated", True)
    result = validate_fixtures(json_path, csv_path, metadata_path)
    assert result["fixture_status"] != VALID_STATUS
    assert any("physically_validated must be false" in error for error in result["errors"])


def test_validator_requires_legacy_equivalent_false(tmp_path: Path) -> None:
    json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    mutate_json(json_path, "legacy_equivalent", True)
    result = validate_fixtures(json_path, csv_path, metadata_path)
    assert result["fixture_status"] != VALID_STATUS
    assert any("legacy_equivalent must be false" in error for error in result["errors"])


def test_validator_requires_active_simulation_case_false(tmp_path: Path) -> None:
    json_path, csv_path, metadata_path = copy_fixtures(tmp_path)
    mutate_json(json_path, "active_simulation_case", True)
    result = validate_fixtures(json_path, csv_path, metadata_path)
    assert result["fixture_status"] != VALID_STATUS
    assert any("active_simulation_case must be false" in error for error in result["errors"])


def test_cli_writes_validation_json(tmp_path: Path) -> None:
    output_json = tmp_path / "validation.json"
    exit_code = main(
        [
            "--json-fixture",
            str(JSON_FIXTURE),
            "--csv-fixture",
            str(CSV_FIXTURE),
            "--metadata",
            str(METADATA_FIXTURE),
            "--output-json",
            str(output_json),
        ]
    )
    assert exit_code == 0
    result = json.loads(output_json.read_text(encoding="utf-8"))
    assert result["fixture_status"] == VALID_STATUS


def test_write_markdown_validation_report(tmp_path: Path) -> None:
    result = validate_fixtures(JSON_FIXTURE, CSV_FIXTURE, METADATA_FIXTURE)
    output_md = tmp_path / "validation.md"
    write_markdown(result, output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "PennyShaped Diagnostic Output Fixture Validation" in text
    assert f"fixture_status: `{VALID_STATUS}`" in text
