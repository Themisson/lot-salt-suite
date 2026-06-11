from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pytest

from tools import extract_phase10_22b_termwise_geometric_compliance as phase10_22b


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "comparison" / "phase10_22b_termwise_geometric_fixture.csv"


def _run(tmp_path: Path, trace: Path = FIXTURE) -> dict[str, object]:
    return phase10_22b.run_analysis(
        argparse.Namespace(
            trace=trace,
            output_csv=tmp_path / "series.csv",
            output_json=tmp_path / "summary.json",
            output_dir=tmp_path,
        )
    )


def test_phase10_22b_help_exposes_required_arguments() -> None:
    help_text = phase10_22b.build_parser().format_help()

    assert "--trace" in help_text
    assert "--output-csv" in help_text
    assert "--output-json" in help_text


def test_phase10_22b_computes_accumulated_and_incremental_compliance(tmp_path: Path) -> None:
    _run(tmp_path)
    rows = list(csv.DictReader((tmp_path / "series.csv").open(encoding="utf-8")))

    assert float(rows[0]["C_geom_accumulated_1_Pa"]) == pytest.approx(2.0 / (10.0 * 100.0))
    assert float(rows[1]["C_geom_incremental_1_Pa"]) == pytest.approx(2.0 / (10.0 * 100.0))


def test_phase10_22b_calculates_increments_when_absent(tmp_path: Path) -> None:
    trace = tmp_path / "without_increments.csv"
    rows = list(csv.DictReader(FIXTURE.open(encoding="utf-8")))
    fieldnames = [
        key
        for key in rows[0].keys()
        if key not in {"dV_increment_m3_rad", "dP_increment_Pa", "dMl_term_increment_m3_rad", "dV_leakoff_increment_m3_rad"}
    ]
    with trace.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})

    _run(tmp_path, trace)
    output = list(csv.DictReader((tmp_path / "series.csv").open(encoding="utf-8")))

    assert output[0]["C_geom_incremental_1_Pa"] == ""
    assert float(output[1]["C_geom_incremental_1_Pa"]) == pytest.approx(2.0 / (10.0 * 100.0))


def test_phase10_22b_classifies_near_constant_fixture(tmp_path: Path) -> None:
    summary = _run(tmp_path)

    assert summary["classification"]["C_geom_accumulated"] == "TERMWISE_GEOM_COMPLIANCE_NEAR_CONSTANT"
    assert summary["classification"]["C_geom_incremental"] == "TERMWISE_GEOM_COMPLIANCE_NEAR_CONSTANT"


def test_phase10_22b_classifies_pressure_dependent_series() -> None:
    rows = []
    for index in range(5):
        pressure = 100.0 + index * 100.0
        rows.append(
            {
                "time_s": 30.0 + index * 30.0,
                "pressure_for_correlation_Pa": pressure,
                "C_geom_accumulated_1_Pa": 1.0 + index * 0.2,
            }
        )
    stats = phase10_22b._stats(rows, "C_geom_accumulated_1_Pa")

    assert phase10_22b.classify_series(stats, rows, "C_geom_accumulated_1_Pa") == (
        "TERMWISE_GEOM_COMPLIANCE_PRESSURE_DEPENDENT"
    )


def test_phase10_22b_classifies_noisy_sign_change() -> None:
    rows = []
    for index, value in enumerate([1.0, -1.0, 1.2, -0.9, 1.1]):
        rows.append(
            {
                "time_s": 30.0 + index * 30.0,
                "pressure_for_correlation_Pa": 100.0 + index,
                "C_geom_accumulated_1_Pa": value,
            }
        )
    stats = phase10_22b._stats(rows, "C_geom_accumulated_1_Pa")

    assert phase10_22b.classify_series(stats, rows, "C_geom_accumulated_1_Pa") == (
        "TERMWISE_GEOM_COMPLIANCE_NOISY"
    )


def test_phase10_22b_skips_zero_pressure_denominator(tmp_path: Path) -> None:
    trace = tmp_path / "zero_dp.csv"
    rows = list(csv.DictReader(FIXTURE.open(encoding="utf-8")))
    rows[0]["dP_Pa"] = "0"
    rows[0]["dP_increment_Pa"] = "0"
    with trace.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    _run(tmp_path, trace)
    output = list(csv.DictReader((tmp_path / "series.csv").open(encoding="utf-8")))

    assert output[0]["C_geom_accumulated_1_Pa"] == ""
    assert output[0]["C_geom_incremental_1_Pa"] == ""


def test_phase10_22b_rejects_missing_required_fields(tmp_path: Path) -> None:
    trace = tmp_path / "missing.csv"
    trace.write_text("time_s,dP_Pa\n0,0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required"):
        _run(tmp_path, trace)
