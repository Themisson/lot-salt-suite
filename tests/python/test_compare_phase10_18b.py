import argparse
import json
from pathlib import Path

from tools.compare_phase10_18b import run_comparison


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_phase10_18b_exports_full_cycle_diagnostic(tmp_path: Path):
    legacy_csv = tmp_path / "legacy.csv"
    full_cycle_csv = tmp_path / "full_cycle.csv"
    direct_csv = tmp_path / "direct.csv"
    old_vol_csv = tmp_path / "old_vol.csv"
    out = tmp_path / "out"

    write_text(
        legacy_csv,
        """
time_s,injected_volume_m3,pw_Pa
0,0.0,1000
30,0.1,2000
60,0.1,2000
""",
    )
    write_text(
        full_cycle_csv,
        """
time_s,injected_volume_m3,initial_pressure_Pa,wellbore_pressure_Pa
0,0.0,1000,1000
30,0.1,1000,2100
60,0.1,1000,2100
""",
    )
    write_text(
        direct_csv,
        """
time_s,injected_volume_m3,net_pressure_Pa
0,0.0,10
30,0.1,20
""",
    )
    write_text(
        old_vol_csv,
        """
time_s,injected_volume_m3,wellbore_pressure_Pa
0,0.0,0
30,0.1,1100
""",
    )

    metadata = run_comparison(
        argparse.Namespace(
            legacy_csv=str(legacy_csv),
            modern_full_cycle_csv=str(full_cycle_csv),
            modern_direct_csv=str(direct_csv),
            modern_volumetric_10_18a_csv=str(old_vol_csv),
            output_dir=str(out),
        )
    )

    assert metadata["phase"] == "10.18B"
    assert metadata["pre_existing_pressure_gate"] == "PRE_EXISTING_PRESSURE_CONFIRMED_IMPLEMENTATION_ALLOWED"
    assert metadata["shutin_gate"] == "SHUTIN_CONFIRMED_IMPLEMENTATION_ALLOWED"
    assert metadata["modern_full_cycle"]["initial_pressure_Pa"] == 1000.0
    assert metadata["modern_full_cycle"]["max_pressure_Pa"] == 2100.0
    assert metadata["physical_validation"] is False
    assert (out / "phase10_18b_summary.csv").exists()
    assert (out / "phase10_18b_metadata.json").exists()
    assert (out / "pressure_vs_time_full_cycle.png").exists()
    assert (out / "injected_volume_vs_pressure_full_cycle.png").exists()
    assert (out / "injection_rate_vs_time.png").exists()
    assert (out / "pressure_comparison_all_modes.png").exists()

    saved = json.loads((out / "phase10_18b_metadata.json").read_text(encoding="utf-8"))
    assert saved["status"] == metadata["status"]
