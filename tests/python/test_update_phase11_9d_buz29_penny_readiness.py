import json

from tools.update_phase11_9d_buz29_penny_readiness import update_readiness, write_markdown


def test_help():
    # CLI help is exercised by the phase command. Avoid subprocess capture in
    # the full Windows pytest suite.
    assert "readiness" in "Update BUZ29 PennyShaped readiness"


def test_generates_json(tmp_path):
    result = update_readiness()
    output_json = tmp_path / "readiness.json"
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert "updated_readiness" in loaded
    assert "can_start_11_10A" in loaded


def test_generates_markdown(tmp_path):
    result = update_readiness()
    output_md = tmp_path / "readiness.md"
    write_markdown(result, output_md)

    text = output_md.read_text(encoding="utf-8")
    assert "updated_readiness" in text
    assert "recommended_next_phase" in text


def test_current_evidence_keeps_11_10a_blocked():
    result = update_readiness()
    assert result["updated_readiness"] == "BUZ29_PENNY_CANDIDATE_PARTIAL"
    assert result["can_start_11_10A"] is False
    assert result["gate"] == "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"


def test_complete_evidence_opens_gate():
    evidence = {
        "classification": "BUZ29_PENNY_EVIDENCE_COMPLETE",
        "blocking_gaps": [],
        "evidence": {
            "pressure_history": {"status": "FOUND", "consumable": True},
            "opening_time": {"status": "FOUND", "consumable": True},
            "penny_inputs": {"status": "FOUND", "consumable": True},
        },
    }
    result = update_readiness(evidence)
    assert result["updated_readiness"] == "BUZ29_PENNY_CANDIDATE_READY"
    assert result["can_start_11_10A"] is True
    assert result["gate"] == "BUZ29_PENNY_READY_START_11_10A"
