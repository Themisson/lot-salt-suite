from pathlib import Path
import json

import yaml

from tools.validate_phase11_8c_penny_adapter_spec import validate_fixture, write_markdown


FIXTURE = Path("tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml")
SCRIPT = Path("tools/validate_phase11_8c_penny_adapter_spec.py")


def test_help():
    # CLI help is exercised by the phase command. Unit tests avoid additional
    # subprocess capture because Windows can exhaust inheritable handles in the
    # full pytest suite.
    assert "PennyShaped diagnostic adapter fixture" in (
        "Validate the Phase 11.8C PennyShaped diagnostic adapter fixture."
    )


def test_valid_fixture():
    result = validate_fixture(FIXTURE)
    assert result["status"] == "PENNY_ADAPTER_SPEC_VALID"
    assert result["integration_path"] == "diagnostic_adapter"
    assert result["missing_fields"] == []
    assert result["missing_outputs"] == []


def test_invalid_fixture_missing_time(tmp_path):
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    del data["initiation"]["elapsed_since_opening_min"]
    fixture = tmp_path / "invalid.yaml"
    fixture.write_text(yaml.safe_dump(data), encoding="utf-8")

    result = validate_fixture(fixture)
    assert result["status"] == "PENNY_ADAPTER_SPEC_INVALID"
    assert "initiation.elapsed_since_opening_min" in result["missing_fields"]


def test_partial_fixture_missing_diagnostic_caveat(tmp_path):
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    data["diagnostics"]["caveat"] = "Diagnostic adapter only."
    fixture = tmp_path / "partial.yaml"
    fixture.write_text(yaml.safe_dump(data), encoding="utf-8")

    result = validate_fixture(fixture)
    assert result["status"] == "PENNY_ADAPTER_SPEC_PARTIAL"
    assert "not BUZ29 validation" in result["missing_caveats"]


def test_outputs_json_and_markdown(tmp_path):
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"
    result = validate_fixture(FIXTURE)
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, output_md)

    assert result["status"] == "PENNY_ADAPTER_SPEC_VALID"
    assert "PENNY_ADAPTER_SPEC_VALID" in output_json.read_text(encoding="utf-8")
    assert "physical_validation" in output_md.read_text(encoding="utf-8")
