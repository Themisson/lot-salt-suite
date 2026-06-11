from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pytest

from tools import analyze_phase10_22a_legacy_balance_terms as phase10_22a


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "comparison" / "phase10_22a_balance_terms_fixture.csv"


def _run(tmp_path: Path, trace: Path = FIXTURE) -> dict[str, object]:
    return phase10_22a.run_analysis(
        argparse.Namespace(
            trace=trace,
            output_csv=tmp_path / "analysis.csv",
            output_json=tmp_path / "summary.json",
            output_dir=tmp_path,
        )
    )


def _write_bad_residual_fixture(path: Path) -> None:
    rows = list(csv.DictReader(FIXTURE.open(encoding="utf-8")))
    rows[1]["dP_Pa"] = "99"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_phase10_22a_help_exposes_required_arguments() -> None:
    help_text = phase10_22a.build_parser().format_help()

    assert "--trace" in help_text
    assert "--output-csv" in help_text
    assert "--output-json" in help_text


def test_phase10_22a_reconstructs_dp_from_fixture(tmp_path: Path) -> None:
    summary = _run(tmp_path)

    assert "LEGACY_BALANCE_RECONSTRUCTION_MATCHES_DP" in summary["classifications"]
    assert summary["residual"]["max_abs_Pa"] == pytest.approx(0.0)


def test_phase10_22a_classifies_large_residual(tmp_path: Path) -> None:
    trace = tmp_path / "bad.csv"
    _write_bad_residual_fixture(trace)

    summary = _run(tmp_path, trace)

    assert "LEGACY_BALANCE_RECONSTRUCTION_MISMATCH" in summary["classifications"]


def test_phase10_22a_detects_accumulated_terms(tmp_path: Path) -> None:
    summary = _run(tmp_path)

    assert summary["accumulation"]["Vq"] == "accumulated_non_decreasing"
    assert summary["accumulation"]["dP"] == "accumulated_non_decreasing"
    assert summary["accumulation"]["dV_leakoff"] == "accumulated_non_decreasing"


def test_phase10_22a_computes_termwise_compliance(tmp_path: Path) -> None:
    _run(tmp_path)
    rows = list(csv.DictReader((tmp_path / "analysis.csv").open(encoding="utf-8")))

    assert rows[1]["termwise_compliance_status"] == "OK"
    assert float(rows[1]["effective_volume_increment_m3_rad"]) == pytest.approx(1.5)
    assert float(rows[1]["C_eff_termwise_1_Pa"]) == pytest.approx(1.5)
    assert float(rows[1]["C_geom_termwise_1_Pa"]) == pytest.approx(0.5)


def test_phase10_22a_reports_missing_optional_fields(tmp_path: Path) -> None:
    summary = _run(tmp_path)

    assert "opened" in summary["fields_missing"]
    assert "LEGACY_BALANCE_TRACE_PARTIAL" in summary["classifications"]


def test_phase10_22a_rejects_missing_required_fields(tmp_path: Path) -> None:
    trace = tmp_path / "missing.csv"
    trace.write_text("time_s,dP_Pa\n0,0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required"):
        _run(tmp_path, trace)
