import json

import pytest

from tools import summarize_phase10_closure as closure


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        closure.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "output-json" in capsys.readouterr().out


def test_generates_json_and_markdown(tmp_path):
    output_json = tmp_path / "closure.json"
    output_md = tmp_path / "closure.md"

    assert closure.main(["--output-json", str(output_json), "--output-md", str(output_md)]) == 0

    data = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert data["status"] == "PHASE10_CLOSED_READY_FOR_STAGE11"
    assert "BUZ67D_MODERN_REFINED_REPRODUCIBLE_PACKAGE" in data["primary_artifact"]
    assert "STAGE11_PARAMETRIC_INFRASTRUCTURE" in data["stage11_recommendation"]
    assert "PHASE10_CLOSED_READY_FOR_STAGE11" in markdown


def test_summary_contains_required_blockers():
    data = closure.phase10_summary()
    blockers = " ".join(data["blocked_items"])

    assert "APBSalt1D" in blockers
    assert "sigmaTheta" in blockers
    assert "pressure_tabulated" in blockers


def test_summary_keeps_documented_source():
    data = closure.phase10_summary()

    assert data["source"] == "DOCUMENTED_PHASE_SUMMARY"
    assert "results/" in " ".join(data["risk_register"])
