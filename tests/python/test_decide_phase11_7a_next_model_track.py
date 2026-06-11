import json

import pytest

from tools import decide_phase11_7a_next_model_track as decide


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        decide.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "output-json" in capsys.readouterr().out


def test_decision_selects_track_and_next_phase():
    summary = decide.build_decision()

    assert summary["status"] == "NEXT_MODEL_TRACK_SELECTED"
    assert summary["selected_track"] == "PENNY_SHAPED"
    assert summary["recommended_next_phase"] == "PHASE11_7B_LEGACY_MATH_AUDIT_SELECTED_MODEL"


def test_decision_contains_caveat_no_physical_validation():
    summary = decide.build_decision()

    assert any("No BUZ29 physical validation" in caveat for caveat in summary["caveats"])


def test_cli_writes_json_and_markdown(tmp_path):
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"

    rc = decide.main(["--output-json", str(output_json), "--output-md", str(output_md)])

    assert rc == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["selected_track"] == "PENNY_SHAPED"
    markdown = output_md.read_text(encoding="utf-8")
    assert "selected_track" in markdown
    assert "recommended_next_phase" in markdown
    assert "não declara validação física" in markdown
