from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from saltpost.vtk import has_pyvista, load_vtu  # noqa: E402


class VtuOutputTests(unittest.TestCase):
    def test_solver_writes_vtu_with_expected_point_arrays(self) -> None:
        exe = ROOT / "build" / "saltcreep.exe"
        if not exe.exists():
            self.skipTest("build/saltcreep.exe not found")

        case_name = "vtu_smoke"
        result_dir = ROOT / "results" / case_name
        work_dir = ROOT / "results" / "_vtu_smoke_case"
        case_path = work_dir / "case.yaml"

        shutil.rmtree(result_dir, ignore_errors=True)
        shutil.rmtree(work_dir, ignore_errors=True)
        work_dir.mkdir(parents=True)
        case_path.write_text(
            """
name: vtu_smoke
geometry:
  well_radius_m: 1.0
  outer_radius_factor: 3.0
depths:
  burial_m: 0
lithology:
  primary: halita
fluid:
  pressure_Pa: 1.0e6
stress:
  k0: 1.0
material:
  E_Pa: 25.0e9
  nu: 0.30
element:
  type: axisym_1d_L3
mesh:
  n_elements_radial: 2
  ratio: 1.0
creep:
  elastic_only: false
  secondary: false
thermal:
  mode: constant
  T_K: 300.0
time:
  total_h: 2
  dt_h: 1
output:
  every_n_steps: 1
  vtu: true
  vtu_every_n_steps: 1
""",
            encoding="utf-8",
        )

        subprocess.run([str(exe), str(case_path)], cwd=ROOT, check=True)

        vtu_path = result_dir / "vtu_smoke_0000.vtu"
        pvd_path = result_dir / "vtu_smoke.pvd"
        self.assertTrue(vtu_path.exists())
        self.assertTrue(pvd_path.exists())
        closure = pd.read_csv(result_dir / "closure.csv")
        self.assertIn("u_wall_m", closure.columns)
        self.assertTrue((result_dir / "displacements_profile.csv").exists())
        self.assertTrue((result_dir / "wall_profile.csv").exists())
        self.assertAlmostEqual(
            float(closure["u_wall_m"].iloc[-1]),
            float(closure["closure_pct"].iloc[-1]) / 100.0 * 1.0,
            places=10,
        )
        pvd_tree = ET.parse(pvd_path)
        self.assertEqual(len(pvd_tree.getroot().findall(".//DataSet")), 3)

        expected = {"u", "u_r", "u_z", "sigma", "eps_v", "damage_D", "temperature_K"}
        if has_pyvista():
            grid = load_vtu(vtu_path)
            self.assertEqual(grid.n_points, 5)
            self.assertTrue(expected.issubset(set(grid.point_data.keys())))
            for name in expected:
                self.assertEqual(len(grid.point_data[name]), grid.n_points)
        else:
            tree = ET.parse(vtu_path)
            piece = tree.getroot().find(".//Piece")
            self.assertIsNotNone(piece)
            self.assertEqual(int(piece.attrib["NumberOfPoints"]), 5)
            arrays = {
                data.attrib.get("Name")
                for data in tree.getroot().findall(".//PointData/DataArray")
            }
            self.assertTrue(expected.issubset(arrays))

        shutil.rmtree(work_dir, ignore_errors=True)
        shutil.rmtree(result_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
