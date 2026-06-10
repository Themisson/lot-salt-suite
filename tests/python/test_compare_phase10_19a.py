from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools import compare_phase10_19a


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_compare_phase10_19a_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_19a.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-csv" in help_text
    assert "--output-dir" in help_text
    assert "--modern-10-18e-csv" in help_text


def test_compare_phase10_19a_writes_summary_and_metadata(tmp_path: Path) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    output_dir = tmp_path / "comparison"

    _write_csv(
        legacy_csv,
        [
            {
                "time_s": 0.0,
                "injected_volume_m3": 0.0,
                "pw_Pa": 26.0e6,
            },
            {
                "time_s": 510.0,
                "injected_volume_m3": 1.0,
                "pw_Pa": 67.0e6,
            },
        ],
    )
    _write_csv(
        modern_csv,
        [
            {
                "time_s": 0.0,
                "injected_volume_m3": 0.0,
                "wellbore_pressure_Pa": 26.0e6,
                "fracture_initiated": 0,
                "fracture_initiation_pressure_Pa": 0.0,
                "fracture_initiation_sigma_theta_Pa": 0.0,
                "fracture_initiation_margin_Pa": 0.0,
                "fracture_volume_m3": 0.0,
                "leakoff_volume_m3": 0.0,
                "balance_injected_volume_increment_m3": 0.0,
                "balance_fracture_volume_increment_m3": 0.0,
                "balance_leakoff_volume_increment_m3": 0.0,
                "balance_effective_volume_increment_m3": 0.0,
            },
            {
                "time_s": 510.0,
                "injected_volume_m3": 1.0,
                "wellbore_pressure_Pa": 68.0e6,
                "fracture_initiated": 1,
                "fracture_initiation_pressure_Pa": 68.0e6,
                "fracture_initiation_sigma_theta_Pa": 67.0e6,
                "fracture_initiation_margin_Pa": 1.0e6,
                "fracture_volume_m3": 0.1,
                "leakoff_volume_m3": 0.01,
                "balance_injected_volume_increment_m3": 1.0,
                "balance_fracture_volume_increment_m3": 0.1,
                "balance_leakoff_volume_increment_m3": 0.01,
                "balance_effective_volume_increment_m3": 0.89,
            },
        ],
    )

    metadata = compare_phase10_19a.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=output_dir,
            modern_10_18b_csv=None,
            modern_10_18c_csv=None,
            modern_10_18e_csv=None,
        )
    )

    assert metadata["phase"] == "10.19A"
    assert metadata["physical_validation"] is False
    assert metadata["classification"] == "SIGMA_THETA_STATIC_EFFECTIVE"
    assert (output_dir / "phase10_19a_summary.csv").exists()
    metadata_path = output_dir / "phase10_19a_metadata.json"
    assert metadata_path.exists()
    saved = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert saved["metrics"]["fracture_initiation_time_s"] == 510.0
    assert saved["metrics"]["fracture_initiation_margin_Pa"] == 1.0e6


def test_compare_phase10_19a_classifies_early_opening(tmp_path: Path) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    _write_csv(legacy_csv, [{"time_s": 510.0, "pw_Pa": 69.0e6}])
    _write_csv(
        modern_csv,
        [
            {
                "time_s": 30.0,
                "wellbore_pressure_Pa": 26.0e6,
                "fracture_initiated": 1,
                "fracture_initiation_pressure_Pa": 70.0e6,
                "fracture_initiation_sigma_theta_Pa": 67.0e6,
                "fracture_initiation_margin_Pa": 3.0e6,
                "fracture_volume_m3": 0.1,
                "leakoff_volume_m3": 0.0,
                "balance_fracture_volume_increment_m3": 0.1,
                "balance_leakoff_volume_increment_m3": 0.0,
            }
        ],
    )

    metadata = compare_phase10_19a.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=tmp_path / "out",
            modern_10_18b_csv=None,
            modern_10_18c_csv=None,
            modern_10_18e_csv=None,
        )
    )

    assert metadata["classification"] == "SIGMA_THETA_STATIC_OPENED_TOO_EARLY"
