from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from benchmark_suite import (  # noqa: E402
    BenchmarkSpec,
    STANDARD_CASES,
    build_matrix,
    run_case,
    write_json,
    write_report,
)


class BenchmarkSuiteTests(unittest.TestCase):
    def test_smoke_matrix_has_one_valid_case(self) -> None:
        specs = build_matrix("smoke")
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].element, "axisym_1d_L3")
        self.assertEqual(specs[0].model, "DM")

    def test_report_generation_from_synthetic_rows(self) -> None:
        out = ROOT / "results" / "_benchmark_suite_unit_report"
        shutil.rmtree(out, ignore_errors=True)
        rows = [
            {
                "case_name": "bench_a",
                "base_case": "modelo_A",
                "element": "axisym_1d_L3",
                "model": "DM",
                "envelope": "",
                "thermal_mode": "none",
                "requested_threads": 1,
                "status": "ok",
                "returncode": 0,
                "wall_time_s": 1.0,
                "time_assembly_s": 0.2,
                "time_solve_s": 0.3,
                "time_constitutive_s": 0.4,
                "closure_final": 0.1,
                "n_dofs": 11,
                "omp_threads": 1,
            },
            {
                "case_name": "bench_b",
                "base_case": "modelo_A",
                "element": "axisym_1d_L3",
                "model": "DM",
                "envelope": "",
                "thermal_mode": "none",
                "requested_threads": 2,
                "status": "ok",
                "returncode": 0,
                "wall_time_s": 0.6,
                "time_assembly_s": 0.15,
                "time_solve_s": 0.2,
                "time_constitutive_s": 0.2,
                "closure_final": 0.1,
                "n_dofs": 11,
                "omp_threads": 2,
            },
        ]

        json_path = write_json(rows, "unit", out)
        report_path = write_report(rows, out)

        self.assertTrue(json_path.exists())
        self.assertTrue(report_path.exists())
        self.assertTrue((out / "benchmark_time_vs_dofs.png").exists())
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["n_success"], 2)
        self.assertIn("Tabela 4", report_path.read_text(encoding="utf-8"))
        shutil.rmtree(out, ignore_errors=True)

    def test_run_one_benchmark_case_writes_metadata_and_valid_closure(self) -> None:
        exe = ROOT / "build" / "saltcreep.exe"
        if not exe.exists():
            self.skipTest("build/saltcreep.exe not found")

        out = ROOT / "results" / "_benchmark_suite_unit"
        base = STANDARD_CASES[0]
        tiny_base = type(base)(
            name="modelo_A_unit",
            lithology=base.lithology,
            water_depth_m=base.water_depth_m,
            burial_m=base.burial_m,
            salt_above_m=base.salt_above_m,
            fluid_ppg=base.fluid_ppg,
            k0=base.k0,
            total_h=1.0,
            dt_h=1.0,
            closure_min_pct=-10.0,
            closure_max_pct=10.0,
        )
        spec = BenchmarkSpec(
            base_case=tiny_base,
            element="axisym_1d_L3",
            model="DM",
            envelope=None,
            thermal_mode="none",
            threads=1,
            n_radial=2,
            n_axial=1,
            ratio=1.0,
        )

        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(ROOT / "results" / spec.case_name, ignore_errors=True)
        row = run_case(spec, output_dir=out, timeout_s=30)

        self.assertEqual(row["status"], "ok", row.get("stderr_tail", ""))
        for field in [
            "wall_time_s",
            "time_assembly_s",
            "time_solve_s",
            "time_constitutive_s",
            "closure_final",
            "n_dofs",
            "omp_threads",
        ]:
            self.assertIn(field, row)
        self.assertGreater(row["n_dofs"], 0)
        self.assertGreaterEqual(row["wall_time_s"], 0.0)
        self.assertGreaterEqual(row["closure_final"], tiny_base.closure_min_pct)
        self.assertLessEqual(row["closure_final"], tiny_base.closure_max_pct)

        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(ROOT / "results" / spec.case_name, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
