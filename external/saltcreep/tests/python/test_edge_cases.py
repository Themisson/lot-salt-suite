from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def saltcreep_exe() -> Path:
    return ROOT / "build" / ("saltcreep.exe")


class SolverEdgeCaseTests(unittest.TestCase):
    def run_case(self, case_name: str, yaml_text: str) -> Path:
        exe = saltcreep_exe()
        if not exe.exists():
            self.skipTest("build/saltcreep.exe not found")

        work_dir = ROOT / "results" / f"_{case_name}_case"
        result_dir = ROOT / "results" / case_name
        shutil.rmtree(work_dir, ignore_errors=True)
        shutil.rmtree(result_dir, ignore_errors=True)
        work_dir.mkdir(parents=True)
        case_path = work_dir / "case.yaml"
        case_path.write_text(yaml_text, encoding="utf-8")

        subprocess.run([str(exe), str(case_path)], cwd=ROOT, check=True)
        self.addCleanup(lambda: shutil.rmtree(work_dir, ignore_errors=True))
        self.addCleanup(lambda: shutil.rmtree(result_dir, ignore_errors=True))
        return result_dir

    def test_adaptive_zero_levels_runs_without_refinement(self) -> None:
        result_dir = self.run_case(
            "edge_adaptive_zero",
            """
name: edge_adaptive_zero
geometry:
  well_radius_m: 0.155575
  outer_radius_factor: 10
depths:
  water_depth_m: 100
  burial_m: 500
lithology:
  primary: halita
fluid:
  weight_lb_per_gal: 10
stress:
  k0: 1.0
element:
  type: axisym_2d_Q4
mesh:
  n_elements_radial: 2
  n_elements_axial: 1
  ratio: 1
  adaptive: true
  max_refinement_levels: 0
creep:
  elastic_only: true
thermal:
  enabled: false
  mode: profile
time:
  total_h: 1
  dt_h: 1
output:
  every_n_steps: 1
  vtu: false
""",
        )

        metadata = json.loads((result_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["mesh_adaptive"])
        self.assertEqual(metadata["adaptive_iterations"], 0)
        self.assertEqual(metadata["final_n_elements"], 2)

    def test_tiny_dt_whole_case_stays_finite(self) -> None:
        result_dir = self.run_case(
            "edge_tiny_dt",
            """
name: edge_tiny_dt
geometry:
  well_radius_m: 1.0
  outer_radius_factor: 3
depths:
  water_depth_m: 0
  burial_m: 1000
lithology:
  primary: halita
fluid:
  pressure_Pa: 1.0e6
stress:
  k0: 1.0
element:
  type: axisym_1d_L3
mesh:
  n_elements_radial: 1
  ratio: 1
creep:
  elastic_only: false
  secondary: true
thermal:
  enabled: false
  mode: constant
  T_K: 359.15
time:
  total_h: 0.000003
  dt_h: 0.000001
  scheme: explicit
output:
  every_n_steps: 1
  vtu: false
""",
        )

        closure = pd.read_csv(result_dir / "closure.csv")
        self.assertFalse(closure.empty)
        self.assertTrue(closure["closure_pct"].notna().all())
        self.assertTrue(abs(float(closure["closure_pct"].iloc[-1])) < 10.0)


if __name__ == "__main__":
    unittest.main()
