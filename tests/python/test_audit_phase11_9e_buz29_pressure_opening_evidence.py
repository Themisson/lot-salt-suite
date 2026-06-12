import json
from pathlib import Path

from tools.audit_phase11_9e_buz29_pressure_opening_evidence import (
    audit_sources,
    summarize_legacy_dat,
    write_markdown,
)


def write_fixture_dat(path: Path, *, include_dp=True, include_opening=True) -> None:
    lines = [
        "Annulars",
        "1",
        "4",
        "",
        "Time",
        "0 0.1 0.2 0.3",
        "",
        "Layer",
        "1",
    ]
    if include_dp:
        lines.extend(["dP", "1", "0 1000 2000 3000"])
    lines.extend(
        [
            "",
            "Layer",
            "1",
            "dV_leakoff",
            "1",
            "0 0 0.01 0.02",
            "",
            "V_outflow",
            "1",
            "0 0 0.01 0.02",
            "",
            "Elapsed time: 0.1 [seg]",
        ]
    )
    if include_opening:
        lines.append("Momento da quebra: 0.2")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sources(tmp_path: Path, *, include_dat=True, include_dp=True, include_opening=True):
    source = tmp_path / "BUZ29-VISCO-first-well.cpp"
    dat = tmp_path / "7-BUZ-29D-RJS10_PENNY-SHAPED.dat"
    visualizer = tmp_path / "PressureDataVisualizer29D-RAA.py"
    source.write_text(
        'std::string initPressure = "70.0";\n'
        'vfluids[0]->setLeakoffProps("pa_min", 3., "penny-shaped");\n',
        encoding="utf-8",
    )
    visualizer.write_text("dPa = dP * 0.000145038\n", encoding="utf-8")
    if include_dat:
        write_fixture_dat(dat, include_dp=include_dp, include_opening=include_opening)
    return {
        "buz29_source": source,
        "legacy_penny_dat": dat,
        "pressure_visualizer": visualizer,
        "doc_57": tmp_path / "doc57.md",
        "doc_58": tmp_path / "doc58.md",
        "doc_68": tmp_path / "doc68.md",
        "doc_70": tmp_path / "doc70.md",
        "doc_71": tmp_path / "doc71.md",
        "tool_11_9c": tmp_path / "tool9c.py",
        "tool_11_9d": tmp_path / "tool9d.py",
    }


def test_help():
    # CLI help is exercised by the phase command. Avoid subprocess capture in
    # the full Windows pytest suite.
    assert "BUZ29 pressure and opening evidence" in (
        "Audit BUZ29 pressure and opening evidence for the PennyShaped diagnostic track."
    )


def test_summarize_legacy_dat_reads_time_dp_and_opening(tmp_path):
    dat = tmp_path / "fixture.dat"
    write_fixture_dat(dat)
    summary = summarize_legacy_dat(dat)
    assert summary.has_time is True
    assert summary.has_dp is True
    assert summary.opening_time_min == 0.2
    assert summary.first_positive_dv_leakoff_time_min == 0.2


def test_generates_json_and_markdown(tmp_path):
    sources = write_sources(tmp_path)
    result = audit_sources(sources)

    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, output_md)

    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    text = output_md.read_text(encoding="utf-8")
    assert loaded["pressure_history_status"] == "PRESSURE_HISTORY_FOUND_CONSUMABLE"
    assert loaded["opening_time_status"] == "OPENING_TIME_FOUND_CONSUMABLE"
    assert loaded["classification"] == "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE"
    assert loaded["can_reopen_11_10A_gate"] is True
    assert "Evidências" in text
    assert "can_reopen_11_10A_gate" in text


def test_complete_with_pressure_and_opening_consumable(tmp_path):
    result = audit_sources(write_sources(tmp_path))
    assert result["classification"] == "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE"
    assert result["pressure_history_consumable"] is True
    assert result["opening_time_consumable"] is True
    assert result["recommended_next_phase"] == (
        "PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING"
    )


def test_partial_with_only_pressure_consumable(tmp_path):
    result = audit_sources(write_sources(tmp_path, include_opening=False))
    assert result["pressure_history_status"] == "PRESSURE_HISTORY_FOUND_CONSUMABLE"
    assert result["opening_time_status"] == "OPENING_TIME_PARTIAL"
    assert result["classification"] == "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_PARTIAL"
    assert result["can_reopen_11_10A_gate"] is False


def test_missing_without_dat(tmp_path):
    result = audit_sources(write_sources(tmp_path, include_dat=False))
    assert result["pressure_history_status"] == "PRESSURE_HISTORY_MISSING"
    assert result["opening_time_status"] == "OPENING_TIME_MISSING"
    assert result["classification"] == "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_MISSING"


def test_blocked_when_legacy_instrumentation_required(tmp_path):
    result = audit_sources(write_sources(tmp_path), requires_legacy_instrumentation=True)
    assert result["classification"] == "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_BLOCKED"
    assert result["can_reopen_11_10A_gate"] is False
    assert "requires_controlled_legacy_instrumentation" in result["blocking_gaps"]
