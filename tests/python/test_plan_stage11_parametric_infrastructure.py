import json

import pytest

from tools import plan_stage11_parametric_infrastructure as stage11


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        stage11.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "output-json" in capsys.readouterr().out


def test_generates_json(tmp_path):
    output_json = tmp_path / "stage11.json"
    output_md = tmp_path / "stage11.md"

    assert stage11.main(["--output-json", str(output_json), "--output-md", str(output_md)]) == 0

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["stage"] == 11
    assert data["primary_goal"] == "PARAMETRIC_INFRASTRUCTURE"


def test_generates_markdown(tmp_path):
    output_json = tmp_path / "stage11.json"
    output_md = tmp_path / "stage11.md"

    stage11.main(["--output-json", str(output_json), "--output-md", str(output_md)])

    markdown = output_md.read_text(encoding="utf-8")
    assert "Stage 11 parametric infrastructure plan" in markdown
    assert "STAGE11_1B_MULTI_STUDY_MATRIX_INDEX" in markdown


def test_plan_contains_required_phases():
    phases = {item["phase"] for item in stage11.build_plan()["planned_phases"]}

    assert "11.1B" in phases
    assert "11.2A" in phases
    assert "11.2B" in phases


def test_plan_keeps_solver_work_out_of_scope():
    blocked = " ".join(stage11.build_plan()["blocked_items"])

    assert "sigmaTheta runtime" in blocked
    assert "APBSalt1D" in blocked
