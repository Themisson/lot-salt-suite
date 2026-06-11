from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools import compare_phase10_25b


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _legacy_rows() -> list[dict[str, object]]:
    return [
        {"time_s": 0.0, "pw_Pa": 26732215.0, "opened": 0, "sink_positive": 0},
        {"time_s": 510.0, "pw_Pa": 66769500.0, "opened": 1, "sink_positive": 0},
        {"time_s": 540.0, "pw_Pa": 68000000.0, "opened": 1, "sink_positive": 1},
        {
            "time_s": 750.0,
            "pw_Pa": 69035836.1743195,
            "opened": 1,
            "sink_positive": 1,
        },
    ]


def _modern_rows(
    *,
    opening_time_s: float,
    sink_time_s: float,
    max_pressure_Pa: float,
) -> list[dict[str, object]]:
    return [
        {
            "time_s": 0.0,
            "wellbore_pressure_Pa": 26732215.0,
            "fracture_started_this_step": 0,
            "fracture_initiated": 0,
            "fracture_initiation_pressure_Pa": 0.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
        },
        {
            "time_s": opening_time_s,
            "wellbore_pressure_Pa": 66770000.0,
            "fracture_started_this_step": 1,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
        },
        {
            "time_s": sink_time_s,
            "wellbore_pressure_Pa": max_pressure_Pa,
            "fracture_started_this_step": 0,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.01,
            "leakoff_sink_applied_m3": 0.0,
        },
    ]


def _run(tmp_path: Path, modern_rows: list[dict[str, object]]) -> dict[str, object]:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    output_dir = tmp_path / "out"
    _write_csv(legacy_csv, _legacy_rows())
    _write_csv(modern_csv, modern_rows)
    return compare_phase10_25b.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=output_dir,
        )
    )


def test_compare_phase10_25b_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_25b.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-csv" in help_text
    assert "--output-dir" in help_text


def test_compare_phase10_25b_classifies_effective_refined_timeseries(
    tmp_path: Path,
) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=510.0,
            sink_time_s=540.0,
            max_pressure_Pa=69040000.0,
        ),
    )

    assert metadata["classification"] == "SIGMA_THETA_REFINED_TIMESERIES_EFFECTIVE"
    assert metadata["metrics"]["opening_time_error_s"] == 0.0
    assert metadata["metrics"]["modern_sink_delay_s"] == 30.0
    assert metadata["metrics"]["sink_delay_error_s"] == 0.0
    assert abs(metadata["metrics"]["relative_error_max_pressure"]) < 0.10
    assert (tmp_path / "out" / "phase10_25b_summary.csv").exists()
    assert (tmp_path / "out" / "phase10_25b_metadata.json").exists()


def test_compare_phase10_25b_detects_pressure_ok_opening_shifted(
    tmp_path: Path,
) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=660.0,
            sink_time_s=690.0,
            max_pressure_Pa=69040000.0,
        ),
    )

    assert (
        metadata["classification"]
        == "SIGMA_THETA_REFINED_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED"
    )


def test_compare_phase10_25b_detects_opening_ok_pressure_shifted(
    tmp_path: Path,
) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=510.0,
            sink_time_s=540.0,
            max_pressure_Pa=90000000.0,
        ),
    )

    assert (
        metadata["classification"]
        == "SIGMA_THETA_REFINED_TIMESERIES_OPENING_OK_PRESSURE_SHIFTED"
    )


def test_compare_phase10_25b_detects_no_improvement(tmp_path: Path) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=900.0,
            sink_time_s=960.0,
            max_pressure_Pa=90000000.0,
        ),
    )

    assert metadata["classification"] == "SIGMA_THETA_REFINED_TIMESERIES_NO_IMPROVEMENT"


def test_compare_phase10_25b_rejects_missing_inputs(tmp_path: Path) -> None:
    modern_csv = tmp_path / "modern.csv"
    _write_csv(
        modern_csv,
        _modern_rows(
            opening_time_s=510.0,
            sink_time_s=540.0,
            max_pressure_Pa=69040000.0,
        ),
    )

    try:
        compare_phase10_25b.run_comparison(
            argparse.Namespace(
                legacy_csv=tmp_path / "missing.csv",
                modern_csv=modern_csv,
                output_dir=tmp_path / "out",
            )
        )
    except FileNotFoundError:
        return
    raise AssertionError("missing legacy CSV should raise FileNotFoundError")
