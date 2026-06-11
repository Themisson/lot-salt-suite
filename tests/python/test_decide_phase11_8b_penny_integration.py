import json

import pytest

from tools import decide_phase11_8b_penny_integration as decision


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        decision.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "output-json" in capsys.readouterr().out


def test_decision_selects_diagnostic_adapter():
    data = decision.build_decision()

    assert data["status"] == "PENNY_ADAPTER_OPT_IN_SELECTED"
    assert data["selected_integration_path"] == "diagnostic_adapter"
    assert data["current_core_status"] == "PENNY_SHAPED_MINIMAL_CORE_IMPLEMENTED"
    assert data["recommended_next_phase"] == "PHASE11_8C_PENNY_ADAPTER_SPEC"


def test_decision_contains_required_caveats():
    data = decision.build_decision()
    caveats = " ".join(data["caveats"])

    assert "does not validate BUZ29" in caveats
    assert "does not declare legacy equivalence" in caveats
    assert data["buz29_validation"] is False
    assert data["legacy_equivalence"] is False


def test_cli_writes_json_and_markdown(tmp_path):
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"

    rc = decision.main(["--output-json", str(output_json), "--output-md", str(output_md)])

    assert rc == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["selected_integration_path"] == "diagnostic_adapter"
    markdown = output_md.read_text(encoding="utf-8")
    assert "selected_integration_path" in markdown
    assert "não valida BUZ29" in markdown
