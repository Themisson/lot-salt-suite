from __future__ import annotations

import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
from matplotlib.animation import PillowWriter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from saltpost.animations import animate_closure  # noqa: E402
from saltpost.cli import main as saltpost_main  # noqa: E402
from saltpost.export import export_paper_bundle  # noqa: E402
from saltpost.io import load_result  # noqa: E402
from saltpost.report import generate_dashboard  # noqa: E402
from saltpost.studies import discover_study_results, variant_key  # noqa: E402


def write_result(
    base: Path,
    name: str,
    element: str,
    dofs: int,
    values: list[float],
    thermal_enabled: bool = False,
) -> Path:
    case_dir = base / name
    case_dir.mkdir()
    (case_dir / "metadata.json").write_text(
        json.dumps({
            "case_name": name,
            "element_type": element,
            "n_dofs": dofs,
            "time_scheme": "explicit",
            "wall_time_s": 1.25,
            "thermal_enabled": thermal_enabled,
            "creep_flags": {"secondary": True, "primary": False, "tertiary": False},
        }),
        encoding="utf-8",
    )
    pd.DataFrame({
        "t_h": [0.0, 1.0, 2.0],
        "closure_pct": values,
        "u_wall_m": [0.0, 0.01, 0.02],
    }).to_csv(case_dir / "closure.csv", index=False)
    pd.DataFrame({
        "t_h": [0.0, 0.0, 1.0, 1.0],
        "node_id": [0, 1, 0, 1],
        "r_m": [1.0, 2.0, 1.0, 2.0],
        "z_m": [0.0, 0.0, 0.0, 0.0],
        "u_r_m": [0.0, 0.0, -0.01, -0.001],
        "u_z_m": [0.0, 0.0, 0.0, 0.0],
    }).to_csv(case_dir / "displacements_profile.csv", index=False)
    return case_dir


class SaltPostDashboardTests(unittest.TestCase):
    def test_study_discovers_results_and_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_result(base, "modelo_A_L3", "axisym_1d_L3", 11, [0.0, 1.0, 2.0])
            write_result(base, "modelo_A_Q8", "axisym_2d_Q8", 22, [0.0, 1.1, 2.2])
            write_result(base, "modelo_B_Q8", "axisym_2d_Q8", 22, [0.0, 2.0, 4.0])

            results = discover_study_results("modelo_A", "element", base)

            self.assertEqual([r.case_name for r in results], ["modelo_A_L3", "modelo_A_Q8"])
            self.assertEqual([variant_key(r, "element") for r in results],
                             ["axisym_1d_L3", "axisym_2d_Q8"])

    def test_paper_export_creates_manifest_and_latex_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / "closure_vs_tempo.png").write_bytes(b"png")
            (out_dir / "closure_vs_tempo.pdf").write_bytes(b"pdf")
            pd.DataFrame({"case": ["modelo_A"], "closure": [1.23]}).to_csv(
                out_dir / "comparison_table.csv", index=False
            )

            paper_dir = export_paper_bundle(out_dir, "modelo_A", "element")

            self.assertTrue((paper_dir / "paper_manifest.csv").exists())
            self.assertTrue(any(p.name.endswith(".tex") for p in paper_dir.iterdir()))
            self.assertTrue(any(p.name.endswith(".png") for p in paper_dir.iterdir()))
            self.assertTrue(any("modelo_a_by_element" in p.name for p in paper_dir.iterdir()))

    def test_dashboard_generates_valid_html_with_case_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result_dir = write_result(base, "modelo_A_Q8", "axisym_2d_Q8", 22, [0.0, 1.0, 2.0])
            out_dir = base / "comparison"
            out_dir.mkdir()
            (out_dir / "closure_vs_tempo.png").write_bytes(b"png")
            pd.DataFrame({"case": ["modelo_A_Q8"]}).to_csv(out_dir / "comparison_table.csv", index=False)
            report_dir = base / "report"

            html_path = generate_dashboard([load_result(result_dir)], out_dir, report_dir, "modelo_A", "element")

            text = html_path.read_text(encoding="utf-8")
            HTMLParser().feed(text)
            self.assertIn("SaltCreep Dashboard", text)
            self.assertIn("metadata.json", text)
            self.assertIn("closure_vs_tempo.png", text)

    def test_closure_animation_generates_gif(self) -> None:
        if not PillowWriter.isAvailable():
            self.skipTest("Pillow animation writer is not available")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = load_result(write_result(base, "modelo_A_Q8", "axisym_2d_Q8", 22, [0.0, 1.0, 2.0]))

            out = animate_closure(result, base, fps=2)

            self.assertIsNotNone(out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 0)

    def test_cli_study_report_and_paper_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_result(base, "modelo_A_L3", "axisym_1d_L3", 11, [0.0, 1.0, 2.0])
            write_result(base, "modelo_A_Q8", "axisym_2d_Q8", 22, [0.0, 1.2, 2.4])
            out_dir = base / "out"
            report_dir = base / "report"

            rc = saltpost_main([
                "--study", "modelo_A",
                "--vary", "element",
                "--results-root", str(base),
                "--out-dir", str(out_dir),
                "--format", "paper",
                "--report",
                "--report-dir", str(report_dir),
            ])

            self.assertEqual(rc, 0)
            self.assertTrue((out_dir / "paper" / "paper_manifest.csv").exists())
            self.assertTrue((report_dir / "index.html").exists())


if __name__ == "__main__":
    unittest.main()

