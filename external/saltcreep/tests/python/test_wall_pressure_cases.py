from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PPG_TO_KG_M3 = 119.826
GRAVITY = 9.80665


def saltcreep_exe() -> Path:
    return ROOT / "build" / "saltcreep.exe"


def expected_pressure(ppg: float, depth_m: float) -> float:
    return ppg * PPG_TO_KG_M3 * GRAVITY * depth_m


class WallPressureCaseTests(unittest.TestCase):
    def run_existing_case(self, relative_case: str, result_name: str) -> Path:
        exe = saltcreep_exe()
        if not exe.exists():
            self.skipTest("build/saltcreep.exe not found")

        result_dir = ROOT / "results" / result_name
        shutil.rmtree(result_dir, ignore_errors=True)
        subprocess.run([str(exe), str(ROOT / relative_case)], cwd=ROOT, check=True)
        self.addCleanup(lambda: shutil.rmtree(result_dir, ignore_errors=True))
        return result_dir

    def test_apb_1d_and_2d_hydrostatic_pressure_profiles(self) -> None:
        result_1d = self.run_existing_case(
            "cases/apb/mud_gradient_1d_8p5ppg.yaml",
            "mud_gradient_1d_8p5ppg",
        )
        result_2d = self.run_existing_case(
            "cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml",
            "mud_gradient_2d_Q8_8p5ppg",
        )

        profile_1d = pd.read_csv(result_1d / "wall_pressure_profile.csv")
        self.assertEqual(profile_1d["depth_m"].nunique(), 1)
        self.assertAlmostEqual(
            float(profile_1d["p_wall_Pa"].iloc[0]),
            expected_pressure(8.5, 4100.0),
            delta=1.0e-6,
        )

        profile_2d = pd.read_csv(result_2d / "wall_pressure_profile.csv")
        initial = profile_2d[profile_2d["t_h"] == 0.0]
        self.assertGreater(initial["depth_m"].nunique(), 2)
        top = initial.loc[initial["depth_m"].idxmin()]
        bottom = initial.loc[initial["depth_m"].idxmax()]
        self.assertAlmostEqual(
            float(top["p_wall_Pa"]),
            expected_pressure(8.5, 4100.0),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(bottom["p_wall_Pa"]),
            expected_pressure(8.5, 5100.0),
            delta=1.0e-6,
        )
        self.assertTrue((initial["T_wall_K"] == 370.88).all())

    def test_operational_csv_cases_run_with_finite_closure(self) -> None:
        result_1d = self.run_existing_case(
            "cases/apb/apb_1d_schedule_mud_temperature.yaml",
            "apb_1d_schedule_mud_temperature",
        )
        result_2d = self.run_existing_case(
            "cases/apb/apb_2d_layered_schedule_Q8.yaml",
            "apb_2d_layered_schedule_Q8",
        )

        closure_1d = pd.read_csv(result_1d / "closure.csv")
        closure_2d = pd.read_csv(result_2d / "closure.csv")
        self.assertTrue(closure_1d["closure_pct"].notna().all())
        self.assertTrue(closure_2d["closure_pct"].notna().all())
        self.assertGreater(float(closure_1d["closure_pct"].iloc[-1]), 0.0)
        self.assertGreater(float(closure_2d["closure_pct"].iloc[-1]), 0.0)

        pressure_1d = pd.read_csv(result_1d / "wall_pressure_profile.csv")
        self.assertAlmostEqual(float(pressure_1d["p_wall_Pa"].iloc[0]), 48178757.3589, delta=1.0e-3)
        self.assertAlmostEqual(float(pressure_1d["T_wall_K"].iloc[0]), 365.0)
        self.assertAlmostEqual(float(pressure_1d["p_wall_Pa"].iloc[-1]), 44324456.7702, delta=1.0e-3)
        self.assertAlmostEqual(float(pressure_1d["T_wall_K"].iloc[-1]), 370.0)

        pressure_2d = pd.read_csv(result_2d / "wall_pressure_profile.csv")
        initial_2d = pressure_2d[pressure_2d["t_h"] == 0.0]
        self.assertGreater(initial_2d["z_m"].nunique(), 2)
        self.assertAlmostEqual(
            float(initial_2d.loc[initial_2d["z_m"].idxmin(), "p_wall_Pa"]),
            48178757.3589,
            delta=1.0e-3,
        )
        self.assertAlmostEqual(
            float(initial_2d.loc[initial_2d["z_m"].idxmax(), "T_wall_K"]),
            375.0,
        )


if __name__ == "__main__":
    unittest.main()
