import json

import pytest
import yaml

from tools import validate_phase11_7c_selected_model_yaml_spec as spec


def _valid_fixture() -> dict:
    return {
        "phase": "11.7C",
        "selected_track": "PENNY_SHAPED",
        "fracture_model": {
            "type": "penny_shaped",
            "status": "SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA",
            "elasticity": {
                "young_modulus": {"value": 5710000.0, "unit": "Pa"},
                "poisson_ratio": {"value": 0.36, "unit": "dimensionless"},
            },
            "fluid": {"viscosity": {"value": 180.0, "unit": "Pa_min"}},
            "injection": {"flow_rate": {"value": 0.05, "unit": "m3_min"}},
            "initiation": {
                "elapsed_since_opening": {"value": 1.0, "unit": "min"},
                "wellbore_pressure": {"value": 67000000.0, "unit": "Pa"},
                "sigma_theta_compression_positive": {"value": 66000000.0, "unit": "Pa"},
            },
            "legacy_options": {
                "volume_multiplier": 10.0,
                "pressure_factor": "pw_over_sigma_theta",
            },
            "expected_outputs": [
                "opening_m",
                "radius_m",
                "pressure_factor",
                "fracture_volume_proxy_m3",
            ],
        },
    }


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        spec.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "fixture" in capsys.readouterr().out


def test_valid_fixture_is_accepted():
    result = spec.validate_spec(_valid_fixture())

    assert result["status"] == "SELECTED_MODEL_YAML_SPEC_VALID"
    assert result["selected_track"] == "PENNY_SHAPED"
    assert result["model_type"] == "penny_shaped"
    assert result["recommended_next_phase"] == "PHASE11_8A_MINIMAL_SELECTED_NON_PKN_MODEL"


def test_missing_output_is_partial():
    data = _valid_fixture()
    data["fracture_model"]["expected_outputs"].remove("radius_m")

    result = spec.validate_spec(data)

    assert result["status"] == "SELECTED_MODEL_YAML_SPEC_PARTIAL"
    assert "fracture_model.expected_outputs.radius_m" in result["missing"]


def test_wrong_unit_is_partial():
    data = _valid_fixture()
    data["fracture_model"]["fluid"]["viscosity"]["unit"] = "Pa_s"

    result = spec.validate_spec(data)

    assert result["status"] == "SELECTED_MODEL_YAML_SPEC_PARTIAL"
    assert "fracture_model.fluid.viscosity.unit" in result["mismatches"]


def test_cli_writes_json_and_markdown(tmp_path):
    fixture = tmp_path / "fixture.yaml"
    output_json = tmp_path / "result.json"
    output_md = tmp_path / "result.md"
    fixture.write_text(yaml.safe_dump(_valid_fixture()), encoding="utf-8")

    rc = spec.main(["--fixture", str(fixture), "--output-json", str(output_json), "--output-md", str(output_md)])

    assert rc == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["status"] == "SELECTED_MODEL_YAML_SPEC_VALID"
    markdown = output_md.read_text(encoding="utf-8")
    assert "selected model YAML/IO spec validation" in markdown
