from pathlib import Path
import json

import pytest
import yaml

from tools.verify_phase11_9a_penny_synthetic_case import evaluate, verify_case, write_markdown


CASE = Path("cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml")
SCRIPT = Path("tools/verify_phase11_9a_penny_synthetic_case.py")


def test_help():
    # CLI help is exercised by the phase command. Unit tests avoid additional
    # subprocess capture because Windows can exhaust inheritable handles in the
    # full pytest suite.
    assert "synthetic PennyShaped diagnostic case" in (
        "Verify the Phase 11.9A synthetic PennyShaped diagnostic case."
    )


def test_synthetic_case_is_created_and_non_runtime():
    result = verify_case(CASE)
    assert result["status"] == "PENNY_SYNTHETIC_CASE_CREATED"
    assert result["runtime_schema"] is False
    assert result["buz29_validation"] is False
    assert result["legacy_equivalence"] is False


def test_formula_outputs_are_positive():
    result = verify_case(CASE)
    outputs = result["outputs"]
    assert outputs["plane_strain_modulus_Pa"] > 0.0
    assert outputs["opening_m"] > 0.0
    assert outputs["radius_m"] > 0.0
    assert outputs["pressure_factor"] > 1.0
    assert outputs["fracture_volume_proxy_m3"] > 0.0


def test_invalid_numeric_input_is_rejected(tmp_path):
    data = yaml.safe_load(CASE.read_text(encoding="utf-8"))
    data["elasticity"]["young_modulus_Pa"] = 0.0
    fixture = tmp_path / "invalid.yaml"
    fixture.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValueError):
        verify_case(fixture)


def test_cli_writes_json_and_markdown(tmp_path):
    output_json = tmp_path / "summary.json"
    output_md = tmp_path / "summary.md"
    result = verify_case(CASE)
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, output_md)

    assert result["status"] == "PENNY_SYNTHETIC_CASE_CREATED"
    assert "PENNY_SYNTHETIC_CASE_CREATED" in output_json.read_text(encoding="utf-8")
    assert "Not BUZ29 validation" in output_md.read_text(encoding="utf-8")
