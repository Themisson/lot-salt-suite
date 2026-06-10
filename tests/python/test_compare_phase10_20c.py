from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools import compare_phase10_20c


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_compare_phase10_20c_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_20c.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-elastic-csv" in help_text
    assert "--modern-no-compliance-csv" in help_text
    assert "--modern-constant-compliance-csv" in help_text
    assert "--modern-sigma-theta-static-csv" in help_text


def test_compare_phase10_20c_classifies_undercompliant_elastic_model(
    tmp_path: Path,
) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    elastic_csv = tmp_path / "elastic.csv"
    no_compliance_csv = tmp_path / "no.csv"
    constant_csv = tmp_path / "constant.csv"
    output_dir = tmp_path / "out"

    _write_csv(
        legacy_csv,
        [
            {"time_s": 0.0, "pw_Pa": 1000.0, "dP": 0.0, "injected_volume_m3": 0.0},
            {"time_s": 30.0, "pw_Pa": 1100.0, "dP": 100.0, "injected_volume_m3": 0.1},
            {"time_s": 60.0, "pw_Pa": 2000.0, "dP": 1000.0, "injected_volume_m3": 0.2},
        ],
    )
    _write_csv(
        elastic_csv,
        [
            {
                "time_s": 0.0,
                "wellbore_pressure_Pa": 1000.0,
                "balance_delta_pressure_Pa": 0.0,
                "fracture_initiated": 0,
                "fracture_initiation_pressure_Pa": 0.0,
                "geometric_compressibility_1_Pa": 1.7e-10,
                "effective_compressibility_1_Pa": 8.1e-10,
                "injected_volume_m3": 0.0,
            },
            {
                "time_s": 30.0,
                "wellbore_pressure_Pa": 2000.0,
                "balance_delta_pressure_Pa": 1000.0,
                "fracture_initiated": 1,
                "fracture_initiation_pressure_Pa": 2000.0,
                "geometric_compressibility_1_Pa": 1.7e-10,
                "effective_compressibility_1_Pa": 8.1e-10,
                "injected_volume_m3": 0.1,
            },
        ],
    )
    _write_csv(
        no_compliance_csv,
        [
            {
                "time_s": 30.0,
                "wellbore_pressure_Pa": 5000.0,
                "balance_delta_pressure_Pa": 4000.0,
                "injected_volume_m3": 0.1,
            }
        ],
    )
    _write_csv(
        constant_csv,
        [
            {
                "time_s": 30.0,
                "wellbore_pressure_Pa": 1102.0,
                "balance_delta_pressure_Pa": 102.0,
                "geometric_compressibility_1_Pa": 1.85e-8,
                "injected_volume_m3": 0.1,
            }
        ],
    )

    metadata = compare_phase10_20c.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_elastic_csv=elastic_csv,
            output_dir=output_dir,
            modern_no_compliance_csv=no_compliance_csv,
            modern_constant_compliance_csv=constant_csv,
            modern_sigma_theta_static_csv=None,
        )
    )

    assert metadata["phase"] == "10.20C"
    assert metadata["physical_validation"] is False
    assert metadata["numeric_equivalence"] is False
    assert metadata["runtime_default_changed"] is False
    assert metadata["classification"] == "ELASTIC_COMPLIANCE_UNDERCOMPLIANT"
    assert metadata["metrics"]["legacy_first_dP_Pa"] == 100.0
    assert metadata["metrics"]["modern_first_dP_no_compliance_Pa"] == 4000.0
    assert metadata["metrics"]["modern_first_dP_constant_compliance_Pa"] == 102.0
    assert metadata["metrics"]["modern_first_dP_elastic_compliance_Pa"] == 1000.0
    assert metadata["metrics"]["C_geom_constant_10_19C"] == 1.85e-8
    assert metadata["metrics"]["C_geom_elastic_10_20C"] == 1.7e-10
    assert "Diagnostic only" in " ".join(metadata["caveats"])
    assert (output_dir / "phase10_20c_summary.csv").exists()
    saved = json.loads((output_dir / "phase10_20c_metadata.json").read_text())
    assert saved["classification"] == "ELASTIC_COMPLIANCE_UNDERCOMPLIANT"
