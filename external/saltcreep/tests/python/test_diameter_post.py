from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from saltpost.axisym3d import make_axisym_3d  # noqa: E402
from saltpost.cli import main as saltpost_main  # noqa: E402
from saltpost.diameter import M_TO_IN, diameter_at_depth, enrich_wall_profile  # noqa: E402
from saltpost.io import load_result  # noqa: E402
from saltpost.plots import (  # noqa: E402
    plot_diameter_at_depth,
    plot_lithology_column,
    plot_wellbore_diameter_profile,
)


def write_case(base: Path, name: str = "modelo_layers_DM") -> Path:
    case_dir = base / name
    case_dir.mkdir()
    radius = 0.155575
    metadata = {
        "case_name": name,
        "element_type": "axisym_2d_Q8",
        "n_dofs": 18,
        "well_radius_m": radius,
        "well_diameter_in": 2.0 * radius * M_TO_IN,
        "depth_origin_m": 3600.0,
        "layer_thickness_m": 100.0,
        "lithology": {
            "primary": "halita",
            "layers": [
                {"z_top_m": 0.0, "z_bottom_m": 30.0, "material": "halita"},
                {"z_top_m": 30.0, "z_bottom_m": 65.0, "material": "carnalita"},
                {"z_top_m": 65.0, "z_bottom_m": 100.0, "material": "halita"},
            ],
        },
    }
    (case_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    pd.DataFrame({
        "t_h": [0.0, 1.0, 2.0],
        "closure_pct": [0.0, 0.4, 0.8],
        "u_wall_m": [0.0, 0.001, 0.002],
    }).to_csv(case_dir / "closure.csv", index=False)
    wall_rows = []
    profile_rows = []
    node_id = 0
    for t_h in [0.0, 1.0, 2.0]:
        for z in [0.0, 50.0, 100.0]:
            ur = -0.001 * t_h * (1.0 + z / 100.0)
            wall_rows.append({"t_h": t_h, "node_id": node_id, "z_m": z, "u_r_m": ur})
            for r in [radius, 1.0, 2.0]:
                profile_rows.append({
                    "t_h": t_h,
                    "node_id": node_id,
                    "r_m": r,
                    "z_m": z,
                    "u_r_m": ur * radius / r,
                    "u_z_m": 0.0,
                })
                node_id += 1
    pd.DataFrame(wall_rows).to_csv(case_dir / "wall_profile.csv", index=False)
    pd.DataFrame(profile_rows).to_csv(case_dir / "displacements_profile.csv", index=False)
    return case_dir


class DiameterPostTests(unittest.TestCase):
    def test_wall_profile_is_enriched_with_diameter_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = load_result(write_case(Path(tmp)))

            df = enrich_wall_profile(result)

            self.assertIn("diameter_in", df.columns)
            final_mid = df[(df["t_h"] == 2.0) & (df["z_m"] == 50.0)].iloc[0]
            expected = 2.0 * (0.155575 - 0.003) * M_TO_IN
            self.assertAlmostEqual(float(final_mid["diameter_in"]), expected)

    def test_diameter_at_depth_interpolates_wall_series(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = load_result(write_case(Path(tmp)))

            series = diameter_at_depth(result, 3625.0)

            self.assertEqual(list(series["t_h"]), [0.0, 1.0, 2.0])
            self.assertLess(series["diameter_in"].iloc[-1], series["diameter_in"].iloc[0])

    def test_diameter_and_lithology_plots_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = load_result(write_case(base))
            out_dir = base / "plots"

            plot_wellbore_diameter_profile([result], out_dir, 2.0)
            plot_diameter_at_depth([result], out_dir, 3625.0)
            plot_lithology_column(result, out_dir)

            self.assertTrue((out_dir / "diametro_poco_vs_profundidade.png").exists())
            self.assertTrue((out_dir / "diametro_vs_tempo_na_profundidade.png").exists())
            self.assertTrue((out_dir / "modelo_layers_DM_coluna_litologica.png").exists())

    def test_axisym_3d_and_cli_diameter_plot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            case_dir = write_case(base)
            out_dir = base / "out"

            figure = make_axisym_3d(case_dir, out_dir / "axisym.png", time_h=2.0)
            rc = saltpost_main([
                str(case_dir),
                "--plot", "diameter_profile",
                "--time", "2.0",
                "--out-dir", str(out_dir),
            ])

            self.assertEqual(rc, 0)
            self.assertTrue(figure.exists())
            self.assertGreater(figure.stat().st_size, 0)
            self.assertTrue((out_dir / "diametro_poco_vs_profundidade.png").exists())


if __name__ == "__main__":
    unittest.main()
