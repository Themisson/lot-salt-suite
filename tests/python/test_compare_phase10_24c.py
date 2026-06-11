from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools import compare_phase10_24c


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _legacy_rows(*, final_pressure_Pa: float = 67982867.8436506) -> list[dict[str, object]]:
    return [
        {
            "time_s": 0.0,
            "pw_Pa": 26732215.0,
            "opened": 0,
            "sink_positive": 0,
            "injected_volume_m3": 0.0,
        },
        {
            "time_s": 510.0,
            "pw_Pa": 66769500.0,
            "opened": 1,
            "sink_positive": 0,
            "injected_volume_m3": 1.0,
        },
        {
            "time_s": 540.0,
            "pw_Pa": 68000000.0,
            "opened": 1,
            "sink_positive": 1,
            "injected_volume_m3": 1.1,
        },
        {
            "time_s": 750.0,
            "pw_Pa": final_pressure_Pa,
            "opened": 1,
            "sink_positive": 1,
            "injected_volume_m3": 1.3,
        },
    ]


def _modern_rows(
    *,
    opening_time_s: float,
    sink_time_s: float,
    max_pressure_Pa: float,
    final_pressure_Pa: float | None = None,
) -> list[dict[str, object]]:
    final = max_pressure_Pa if final_pressure_Pa is None else final_pressure_Pa
    return [
        {
            "time_s": 0.0,
            "wellbore_pressure_Pa": 26732215.0,
            "fracture_started_this_step": 0,
            "fracture_initiated": 0,
            "fracture_initiation_pressure_Pa": 0.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
            "injected_volume_m3": 0.0,
        },
        {
            "time_s": opening_time_s,
            "wellbore_pressure_Pa": 66770000.0,
            "fracture_started_this_step": 1,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
            "injected_volume_m3": 1.0,
        },
        {
            "time_s": sink_time_s,
            "wellbore_pressure_Pa": max_pressure_Pa,
            "fracture_started_this_step": 0,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.01,
            "leakoff_sink_applied_m3": 0.0,
            "injected_volume_m3": 1.1,
        },
        {
            "time_s": 750.0,
            "wellbore_pressure_Pa": final,
            "fracture_started_this_step": 0,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
            "injected_volume_m3": 1.3,
        },
    ]


def _run(tmp_path: Path, modern_rows: list[dict[str, object]]) -> dict[str, object]:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    output_dir = tmp_path / "out"
    _write_csv(legacy_csv, _legacy_rows())
    _write_csv(modern_csv, modern_rows)
    return compare_phase10_24c.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=output_dir,
            modern_combined_static_csv=None,
            modern_next_step_csv=None,
            modern_constant_compliance_csv=None,
        )
    )


def test_compare_phase10_24c_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_24c.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-csv" in help_text
    assert "--output-dir" in help_text
    assert "--modern-combined-static-csv" in help_text
    assert "--modern-next-step-csv" in help_text
    assert "--modern-constant-compliance-csv" in help_text


def test_compare_phase10_24c_calculates_peak_opening_and_sink_errors(
    tmp_path: Path,
) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=660.0,
            sink_time_s=690.0,
            max_pressure_Pa=67331393.612597,
        ),
    )

    metrics = metadata["metrics"]
    assert metrics["opening_time_error_s"] == 150.0
    assert metrics["modern_sink_delay_s"] == 30.0
    assert metrics["sink_delay_error_s"] == 0.0
    assert metrics["pressure_at_opening_error_Pa"] == 500.0
    assert abs(metrics["relative_error_max_pressure"]) < 0.10
    assert (tmp_path / "out" / "phase10_24c_summary.csv").exists()
    assert (tmp_path / "out" / "phase10_24c_metadata.json").exists()


def test_compare_phase10_24c_classifies_effective_and_recommends_salt_runtime(
    tmp_path: Path,
) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=510.0,
            sink_time_s=540.0,
            max_pressure_Pa=69040000.0,
            final_pressure_Pa=67990000.0,
        ),
    )

    assert metadata["classification"] == "SIGMA_THETA_TIMESERIES_DIAGNOSTIC_EFFECTIVE"
    assert metadata["next_model_recommendation"] == "NEXT_MODEL_SALT_WALL_STRESS_RUNTIME"


def test_compare_phase10_24c_classifies_shutin_mismatch(tmp_path: Path) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=510.0,
            sink_time_s=540.0,
            max_pressure_Pa=69040000.0,
            final_pressure_Pa=50000000.0,
        ),
    )

    assert metadata["classification"] == "SIGMA_THETA_TIMESERIES_SHUTIN_MISMATCH"
    assert metadata["next_model_recommendation"] == "NEXT_MODEL_THERMAL_EXPLICIT_REQUIRED"


def test_compare_phase10_24c_classifies_pressure_ok_opening_shifted(
    tmp_path: Path,
) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_time_s=660.0,
            sink_time_s=690.0,
            max_pressure_Pa=67331393.612597,
        ),
    )

    assert (
        metadata["classification"]
        == "SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED"
    )
    assert (
        metadata["next_model_recommendation"]
        == "NEXT_MODEL_SIGMA_THETA_TIMESERIES_NEEDS_BETTER_SOURCE"
    )
