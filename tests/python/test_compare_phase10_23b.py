from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools import compare_phase10_23b


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _legacy_rows() -> list[dict[str, object]]:
    return [
        {"time_s": 0.0, "pw_Pa": 1000.0, "injected_volume_m3": 0.0},
        {"time_s": 510.0, "pw_Pa": 66769500.0, "injected_volume_m3": 1.0},
        {"time_s": 540.0, "pw_Pa": 68000000.0, "injected_volume_m3": 1.1},
        {"time_s": 750.0, "pw_Pa": 69035836.1743195, "injected_volume_m3": 1.3},
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
            "wellbore_pressure_Pa": 1000.0,
            "injected_volume_m3": 0.0,
            "fracture_started_this_step": 0,
            "fracture_initiated": 0,
            "fracture_initiation_pressure_Pa": 0.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
        },
        {
            "time_s": opening_time_s,
            "wellbore_pressure_Pa": 66770000.0,
            "injected_volume_m3": 1.0,
            "fracture_started_this_step": 1,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
        },
        {
            "time_s": sink_time_s,
            "wellbore_pressure_Pa": max_pressure_Pa,
            "injected_volume_m3": 1.1,
            "fracture_started_this_step": 0,
            "fracture_initiated": 1,
            "fracture_initiation_pressure_Pa": 66770000.0,
            "fracture_sink_applied_m3": 0.01,
            "leakoff_sink_applied_m3": 0.0,
        },
    ]


def test_compare_phase10_23b_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_23b.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-csv" in help_text
    assert "--modern-constant-compliance-csv" in help_text
    assert "--modern-elastic-compliance-csv" in help_text
    assert "--modern-next-step-csv" in help_text


def test_compare_phase10_23b_classifies_effective_combined_case(tmp_path: Path) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    output_dir = tmp_path / "out"
    _write_csv(legacy_csv, _legacy_rows())
    _write_csv(
        modern_csv,
        _modern_rows(
            opening_time_s=510.0,
            sink_time_s=540.0,
            max_pressure_Pa=69040000.0,
        ),
    )

    metadata = compare_phase10_23b.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=output_dir,
            modern_constant_compliance_csv=None,
            modern_elastic_compliance_csv=None,
            modern_next_step_csv=None,
        )
    )

    assert metadata["classification"] == "COMBINED_DIAGNOSTIC_EFFECTIVE"
    assert metadata["physical_validation"] is False
    assert metadata["metrics"]["modern_fracture_initiation_time_s"] == 510.0
    assert metadata["metrics"]["modern_first_sink_positive_time_s"] == 540.0
    assert metadata["metrics"]["modern_sink_delay_s"] == 30.0
    assert abs(metadata["metrics"]["relative_error_max_pressure"]) < 0.10
    assert (output_dir / "phase10_23b_summary.csv").exists()
    assert (output_dir / "phase10_23b_metadata.json").exists()


def test_compare_phase10_23b_classifies_partial_when_only_sink_matches(
    tmp_path: Path,
) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    output_dir = tmp_path / "out"
    _write_csv(legacy_csv, _legacy_rows())
    _write_csv(
        modern_csv,
        _modern_rows(
            opening_time_s=690.0,
            sink_time_s=720.0,
            max_pressure_Pa=90000000.0,
        ),
    )

    metadata = compare_phase10_23b.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=output_dir,
            modern_constant_compliance_csv=None,
            modern_elastic_compliance_csv=None,
            modern_next_step_csv=None,
        )
    )

    assert metadata["classification"] == "COMBINED_DIAGNOSTIC_PARTIAL"
    assert metadata["metrics"]["modern_sink_delay_s"] == 30.0
    assert metadata["metrics"]["relative_error_max_pressure"] > 0.10
