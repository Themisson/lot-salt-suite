from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from benchmark_wall_pressure import (  # noqa: E402
    MeshSpec,
    WallPressureSpec,
    build_specs,
    run_case,
    write_json,
    write_report,
)


class BenchmarkWallPressureTests(unittest.TestCase):
    def test_smoke_matrix_compares_three_pressure_modes(self) -> None:
        specs = build_specs("smoke")
        self.assertEqual(len(specs), 3)
        self.assertEqual(
            {spec.fluid_mode for spec in specs},
            {"constant", "hydrostatic_depth_profile", "csv_time_depth_profile"},
        )
        self.assertTrue(all(spec.mesh.n_axial >= 1 for spec in specs))

    def test_report_generation_from_synthetic_rows(self) -> None:
        out = ROOT / "results" / "_benchmark_wall_pressure_unit_report"
        shutil.rmtree(out, ignore_errors=True)
        rows = [
            {
                "case_name": "bench_constant",
                "fluid_mode": "constant",
                "mesh_label": "small",
                "n_elements_radial": 4,
                "n_elements_axial": 2,
                "mesh_ratio": 20.0,
                "requested_threads": 1,
                "status": "ok",
                "returncode": 0,
                "wall_time_s": 1.0,
                "time_assembly_s": 0.3,
                "time_solve_s": 0.4,
                "time_constitutive_s": 0.1,
                "n_dofs": 90,
                "omp_threads": 1,
                "closure_final": 0.2,
                "p_wall_min_Pa": 48.5e6,
                "p_wall_max_Pa": 48.5e6,
            },
            {
                "case_name": "bench_hydro",
                "fluid_mode": "hydrostatic_depth_profile",
                "mesh_label": "small",
                "n_elements_radial": 4,
                "n_elements_axial": 2,
                "mesh_ratio": 20.0,
                "requested_threads": 1,
                "status": "ok",
                "returncode": 0,
                "wall_time_s": 1.1,
                "time_assembly_s": 0.32,
                "time_solve_s": 0.4,
                "time_constitutive_s": 0.1,
                "n_dofs": 90,
                "omp_threads": 1,
                "closure_final": 0.22,
                "p_wall_min_Pa": 48.0e6,
                "p_wall_max_Pa": 60.0e6,
            },
        ]

        json_path = write_json(rows, "unit", out)
        report_path = write_report(rows, out)

        self.assertTrue(json_path.exists())
        self.assertTrue(report_path.exists())
        self.assertTrue((out / "benchmark_wall_pressure.csv").exists())
        self.assertTrue((out / "wall_pressure_time_vs_dofs.png").exists())
        self.assertTrue((out / "wall_pressure_overhead_vs_dofs.png").exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["n_success"], 2)
        self.assertIn("Benchmark de pressão", report_path.read_text(encoding="utf-8"))
        shutil.rmtree(out, ignore_errors=True)

    def test_run_one_wall_pressure_benchmark_case(self) -> None:
        exe = ROOT / "build" / "saltcreep.exe"
        if not exe.exists():
            self.skipTest("build/saltcreep.exe not found")

        out = ROOT / "results" / "_benchmark_wall_pressure_unit"
        spec = WallPressureSpec(
            fluid_mode="hydrostatic_depth_profile",
            mesh=MeshSpec("unit", 2, 1, 5.0),
            threads=1,
            total_h=0.5,
            dt_h=0.5,
        )
        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(ROOT / "results" / spec.case_name, ignore_errors=True)

        row = run_case(spec, output_dir=out, timeout_s=60)

        self.assertEqual(row["status"], "ok", row.get("stderr_tail", ""))
        self.assertGreater(row["n_dofs"], 0)
        self.assertGreaterEqual(row["wall_time_s"], 0.0)
        self.assertGreater(row["p_wall_max_Pa"], row["p_wall_min_Pa"])
        self.assertTrue((ROOT / "results" / spec.case_name / "wall_pressure_profile.csv").exists())

        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(ROOT / "results" / spec.case_name, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
