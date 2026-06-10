from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools import compare_phase10_19c


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_compare_phase10_19c_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_19c.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-csv" in help_text
    assert "--output-dir" in help_text
    assert "--modern-10-19a-csv" in help_text


def test_compare_phase10_19c_writes_summary_and_metadata(tmp_path: Path) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    modern_csv = tmp_path / "modern.csv"
    previous_csv = tmp_path / "previous.csv"
    output_dir = tmp_path / "out"

    _write_csv(
        legacy_csv,
        [
            {"time_s": 0.0, "pw_Pa": 26.0e6, "dP": 0.0, "injected_volume_m3": 0.0},
            {"time_s": 30.0, "pw_Pa": 27.8e6, "dP": 1.8e6, "injected_volume_m3": 0.04},
            {"time_s": 60.0, "pw_Pa": 69.0e6, "dP": 42.0e6, "injected_volume_m3": 0.08},
        ],
    )
    _write_csv(
        modern_csv,
        [
            {
                "time_s": 0.0,
                "wellbore_pressure_Pa": 26.0e6,
                "balance_delta_pressure_Pa": 0.0,
                "fracture_initiated": 0,
                "fracture_initiation_pressure_Pa": 0.0,
                "fluid_compressibility_1_Pa": 6.4e-10,
                "geometric_compressibility_1_Pa": 1.8e-8,
                "effective_compressibility_1_Pa": 1.864e-8,
                "injected_volume_m3": 0.0,
            },
            {
                "time_s": 30.0,
                "wellbore_pressure_Pa": 27.8e6,
                "balance_delta_pressure_Pa": 1.8e6,
                "fracture_initiated": 0,
                "fracture_initiation_pressure_Pa": 0.0,
                "fluid_compressibility_1_Pa": 6.4e-10,
                "geometric_compressibility_1_Pa": 1.8e-8,
                "effective_compressibility_1_Pa": 1.864e-8,
                "injected_volume_m3": 0.04,
            },
            {
                "time_s": 60.0,
                "wellbore_pressure_Pa": 61.0e6,
                "balance_delta_pressure_Pa": 33.2e6,
                "fracture_initiated": 1,
                "fracture_initiation_pressure_Pa": 61.0e6,
                "fluid_compressibility_1_Pa": 6.4e-10,
                "geometric_compressibility_1_Pa": 1.8e-8,
                "effective_compressibility_1_Pa": 1.864e-8,
                "injected_volume_m3": 0.08,
            },
        ],
    )
    _write_csv(
        previous_csv,
        [
            {
                "time_s": 30.0,
                "initial_pressure_Pa": 26.0e6,
                "fracture_initiation_pressure_Pa": 82.0e6,
                "balance_delta_pressure_Pa": 0.0,
                "wellbore_pressure_Pa": 26.0e6,
            }
        ],
    )

    metadata = compare_phase10_19c.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_csv=modern_csv,
            output_dir=output_dir,
            modern_10_18b_csv=None,
            modern_10_19a_csv=previous_csv,
        )
    )

    assert metadata["phase"] == "10.19C"
    assert metadata["physical_validation"] is False
    assert metadata["metrics"]["modern_first_dP_no_compliance_Pa"] == 56.0e6
    assert metadata["metrics"]["modern_first_dP_with_compliance_Pa"] == 1.8e6
    assert metadata["classification"] in {
        "COMPLIANCE_EFFECTIVE",
        "COMPLIANCE_MATCHES_FIRST_STEP_BUT_NOT_CURVE",
    }
    assert (output_dir / "phase10_19c_summary.csv").exists()
    saved = json.loads((output_dir / "phase10_19c_metadata.json").read_text())
    assert saved["numeric_equivalence"] is False
