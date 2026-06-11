import json

import pytest

from tools import audit_phase11_7b_selected_model_math as audit


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        audit.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "output-json" in capsys.readouterr().out


def test_audit_contains_selected_track_and_readiness():
    summary = audit.build_audit()

    assert summary["selected_track"] == "PENNY_SHAPED"
    assert summary["status"] == "SELECTED_MODEL_MATH_AUDITED"
    assert summary["implementation_readiness"] == "MINIMAL_IMPLEMENTATION_READY_DIAGNOSTIC_ONLY"
    assert summary["recommended_next_phase"] == "PHASE11_7C_SELECTED_MODEL_YAML_IO_SPEC"


def test_audit_extracts_penny_equations():
    summary = audit.build_audit()
    equations = {item["name"]: item["expression"] for item in summary["equations"]}

    assert "opening_legacy_penny_shaped" in equations
    assert "radius_legacy_penny_shaped" in equations
    assert "leakoff_volume_proxy" in equations
    assert "3.65" in equations["opening_legacy_penny_shaped"]
    assert "0.572" in equations["radius_legacy_penny_shaped"]


def test_cli_writes_json_and_markdown(tmp_path):
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"

    rc = audit.main(["--output-json", str(output_json), "--output-md", str(output_md)])

    assert rc == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["selected_track"] == "PENNY_SHAPED"
    markdown = output_md.read_text(encoding="utf-8")
    assert "implementation_readiness" in markdown
    assert "recommended_next_phase" in markdown
    assert "status" in markdown
