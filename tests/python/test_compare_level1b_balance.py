import argparse
import json
from pathlib import Path

from tools.compare_level1b import run_comparison


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_compare_level1b_uses_wellbore_pressure_field_for_balance(tmp_path: Path):
    legacy_csv = tmp_path / "legacy_audit.csv"
    modern_csv = tmp_path / "modern_timeseries.csv"
    modern_json = tmp_path / "result.json"
    output_dir = tmp_path / "out"

    write_text(
        legacy_csv,
        """
time_s,time_min,layer,annular_index,injected_volume_m3,pw_Pa,initial_annular_volume_m3
0,0,1,A1,0,1000,2
60,1,1,A1,0.1,1200,2
""",
    )
    write_text(
        modern_csv,
        """
time_s,injected_volume_m3,net_pressure_Pa,wellbore_pressure_Pa,balance_effective_volume_increment_m3,balance_injected_volume_increment_m3,balance_fracture_volume_increment_m3,balance_leakoff_volume_increment_m3
0,0,10,0,0,0,0,0
60,0.1,20,1100,0.1,0.1,0,0
""",
    )
    modern_json.write_text(
        json.dumps(
            {
                "summary": {
                    "initial_annular_volume_per_radian_m3": 1.0,
                    "initial_annular_volume_m3": 6.283185307179586,
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = run_comparison(
        argparse.Namespace(
            legacy_audit_csv=str(legacy_csv),
            modern_timeseries_csv=str(modern_csv),
            modern_result_json=str(modern_json),
            modern_pressure_field="wellbore_pressure_Pa",
            output_dir=str(output_dir),
            suffix="_balance",
        )
    )

    assert metadata["phase"] == "10.17B"
    assert metadata["comparison_type"] == "volumetric_balance_visual_diagnostic"
    assert metadata["modern"]["pressure_field"] == "wellbore_pressure_Pa"
    assert metadata["modern"]["wellbore_pressure_Pa_range"]["max"] == 1100.0
    assert metadata["volume_balance_diagnostic_plot_generated"] is True
    assert (output_dir / "injected_volume_vs_pressure_balance.csv").exists()
    assert (output_dir / "level1b_metadata.json").exists()
