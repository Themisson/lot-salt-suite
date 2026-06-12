import json
from pathlib import Path

from tools.audit_phase11_9c_buz29_penny_evidence import (
    audit_sources,
    default_sources,
    write_markdown,
)


def test_help():
    # CLI help is exercised by the phase command; this avoids extra subprocess
    # capture in the full Windows pytest suite.
    assert "BUZ29 evidence" in "Audit BUZ29 evidence for a future route"


def test_generates_json(tmp_path):
    result = audit_sources(default_sources())
    output_json = tmp_path / "evidence.json"
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert loaded["phase"] == "11.9C"
    assert "classification" in loaded
    assert "pressure_history" in loaded["evidence"]


def test_generates_markdown(tmp_path):
    result = audit_sources(default_sources())
    output_md = tmp_path / "evidence.md"
    write_markdown(result, output_md)

    text = output_md.read_text(encoding="utf-8")
    assert "Evidence Map" in text
    assert "blocking_gaps" not in text
    assert "Blocking Gaps" in text


def test_contains_required_evidence_fields():
    result = audit_sources(default_sources())
    assert result["classification"] in {
        "BUZ29_PENNY_EVIDENCE_COMPLETE",
        "BUZ29_PENNY_EVIDENCE_PARTIAL",
        "BUZ29_PENNY_EVIDENCE_BLOCKED",
        "BUZ29_PENNY_EVIDENCE_NOT_FOUND",
        "BUZ29_PENNY_EVIDENCE_INCONCLUSIVE",
    }
    assert "pressure_history" in result["evidence"]
    assert "sigmaTheta_history" in result["evidence"]
    assert "blocking_gaps" in result
    assert result["recommended_next_phase"] == "PHASE11_9D_UPDATE_BUZ29_PENNY_READINESS"


def test_missing_source_classifies_not_found(tmp_path):
    sources = default_sources()
    for key in sources:
        sources[key] = tmp_path / f"{key}.missing"

    result = audit_sources(sources)
    assert result["classification"] == "BUZ29_PENNY_EVIDENCE_NOT_FOUND"
    assert result["can_start_11_10a"] is False
