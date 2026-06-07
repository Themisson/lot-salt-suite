import argparse
import json
from pathlib import Path

from tools.compare_phase10_18a import run_comparison


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_phase10_18a_compares_volumetric_balance_against_legacy_and_direct(tmp_path: Path):
    legacy_csv = tmp_path / "legacy.csv"
    volumetric_csv = tmp_path / "volumetric.csv"
    direct_csv = tmp_path / "direct.csv"
    output_dir = tmp_path / "out"

    write_text(
        legacy_csv,
        """
time_s,injected_volume_m3,pw_Pa
0,0.0,1000
30,0.1,2000
60,0.2,3000
""",
    )
    write_text(
        volumetric_csv,
        """
time_s,injected_volume_m3,net_pressure_Pa,wellbore_pressure_Pa,balance_delta_pressure_Pa,balance_effective_volume_increment_m3,balance_injected_volume_increment_m3,balance_fracture_volume_increment_m3,balance_leakoff_volume_increment_m3
0,0.0,10,0,0,0,0,0,0
30,0.1,20,1800,1800,0.1,0.1,0,0
60,0.2,30,2900,1100,0.1,0.1,0,0
""",
    )
    write_text(
        direct_csv,
        """
time_s,injected_volume_m3,net_pressure_Pa,wellbore_pressure_Pa
0,0.0,10,0
30,0.1,20,0
60,0.2,30,0
""",
    )

    metadata = run_comparison(
        argparse.Namespace(
            legacy_csv=str(legacy_csv),
            modern_volumetric_csv=str(volumetric_csv),
            modern_direct_csv=str(direct_csv),
            output_dir=str(output_dir),
        )
    )

    assert metadata["phase"] == "10.18A"
    assert metadata["status"] == "PHASE10_18A_VOLUMETRIC_BALANCE_DIAGNOSTIC_COMPLETE"
    assert metadata["classification"] == "VOLUMETRIC_BALANCE_CLOSER_TO_LEGACY"
    assert metadata["physical_validation"] is False
    assert metadata["numeric_equivalence"] is False
    assert metadata["legacy"]["max_pressure_Pa"] == 3000.0
    assert metadata["volumetric_balance"]["max_pressure_Pa"] == 2900.0
    assert metadata["pkn_direct"]["max_pressure_Pa"] == 30.0
    assert metadata["differences"]["legacy_vs_volumetric_max_pressure"]["absolute_Pa"] == 100.0
    assert "balance_delta_pressure_Pa" in metadata["balance_components"]["available"]
    assert (output_dir / "phase10_18a_summary.csv").exists()
    assert (output_dir / "phase10_18a_metadata.json").exists()
    assert (output_dir / "injected_volume_vs_pressure_volumetric.png").exists()
    assert (output_dir / "pressure_vs_time_volumetric.png").exists()
    assert (output_dir / "volume_balance_components.png").exists()

    saved = json.loads((output_dir / "phase10_18a_metadata.json").read_text(encoding="utf-8"))
    assert saved["classification"] == metadata["classification"]
