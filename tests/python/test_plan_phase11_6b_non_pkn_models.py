import json

import pytest

from tools import plan_phase11_6b_non_pkn_models as plan


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        plan.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "preferred-track" in capsys.readouterr().out


def test_default_plan_records_non_pkn_roadmap():
    summary = plan.build_plan()

    assert summary["status"] == "NON_PKN_MODEL_ROADMAP_RECORDED"
    assert summary["gate_inputs"]["active_first_well_model"] == "PENNY_SHAPED"
    assert summary["recommended_next_phase"] == "PHASE11_6C_PENNY_SHAPED_FORMULATION_AUDIT"


def test_tracks_include_required_non_pkn_routes():
    summary = plan.build_plan()
    tracks = {item["track"] for item in summary["tracks"]}

    assert "penny_shaped" in tracks
    assert "kgd_circular_elliptical" in tracks
    assert "zamora_compositional_fluid" in tracks
    assert "legacy_output_provenance" in tracks


def test_invalid_preferred_track_falls_back_to_penny():
    summary = plan.build_plan("unknown")

    assert summary["preferred_track"] == "penny_shaped"


def test_cli_writes_json_and_markdown(tmp_path):
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"

    rc = plan.main(["--output-json", str(output_json), "--output-md", str(output_md)])

    assert rc == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["status"] == "NON_PKN_MODEL_ROADMAP_RECORDED"
    assert "penny_shaped" in output_md.read_text(encoding="utf-8")
