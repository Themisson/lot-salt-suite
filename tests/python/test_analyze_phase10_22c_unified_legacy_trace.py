from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "analyze_phase10_22c_unified_legacy_trace.py"
FIXTURE = ROOT / "tests" / "fixtures" / "comparison" / "phase10_22c_unified_trace_fixture.csv"

sys.path.insert(0, str(ROOT / "tools"))
from analyze_phase10_22c_unified_legacy_trace import analyze, read_trace  # noqa: E402


def test_help_command() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        check=True,
    )

    assert completed.returncode == 0


def test_detects_first_opening_sink_and_delay() -> None:
    rows, _, missing = read_trace(FIXTURE)
    _, summary = analyze(rows, missing)

    assert summary["trace_classification"] == "UNIFIED_TRACE_COMPLETE"
    assert summary["opening_classification"] == "OPENING_CRITERION_CONFIRMED"
    assert summary["sink_classification"] == "SINK_TIMING_CONFIRMED"
    assert summary["phase_dependence_classification"] == "PHASE_DEPENDENCE_EXPLAINED_BY_SINK"
    assert summary["first_opened_time_s"] == 90.0
    assert summary["first_sink_positive_time_s"] == 90.0
    assert summary["sink_delay_s"] == 0.0
    assert summary["first_margin_Pa"] == 100000.0


def test_classifies_unexplained_phase_dependence_when_sink_is_missing(tmp_path: Path) -> None:
    modified = tmp_path / "no_sink.csv"
    rows = list(csv.DictReader(FIXTURE.read_text(encoding="utf-8").splitlines()))
    for row in rows:
        row["sink_positive"] = "0"
        row["sink_started_this_step"] = "0"
        row["dV_leakoff_m3_rad"] = "0"
        row["dV_leakoff_increment_m3_rad"] = "0"
    with modified.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    parsed, _, missing = read_trace(modified)
    _, summary = analyze(parsed, missing)

    assert summary["opening_classification"] == "OPENING_CRITERION_CONFIRMED"
    assert summary["sink_classification"] == "SINK_TIMING_MISSING"
    assert summary["phase_dependence_classification"] == "PHASE_DEPENDENCE_UNEXPLAINED"
    assert summary["sink_delay_s"] is None


def test_missing_required_fields_are_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "missing_margin.csv"
    rows = list(csv.DictReader(FIXTURE.read_text(encoding="utf-8").splitlines()))
    fieldnames = [field for field in rows[0] if field != "margin_Pa"]
    with bad.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="margin_Pa"):
        read_trace(bad)


def test_cli_writes_summary_and_enriched_csv(tmp_path: Path) -> None:
    output_csv = tmp_path / "analysis.csv"
    output_json = tmp_path / "summary.json"
    plot_dir = tmp_path / "plots"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--trace",
            str(FIXTURE),
            "--output-csv",
            str(output_csv),
            "--output-json",
            str(output_json),
            "--output-dir",
            str(plot_dir),
        ],
        check=True,
    )

    assert output_csv.exists()
    assert output_json.exists()
    assert (plot_dir / "pressure_sigmaTheta_margin_vs_time.png").exists()
    assert "C_geom_accumulated_1_Pa" in output_csv.read_text(encoding="utf-8")
