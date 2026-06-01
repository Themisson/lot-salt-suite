from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from saltpost.io import load_result  # noqa: E402
from saltpost.plots import (  # noqa: E402
    plot_field_map,
    plot_radial_profile,
    plot_wall_displacement,
    plot_wall_profile,
)


def write_case(base: Path, name: str, element: str, is_2d: bool) -> Path:
    case_dir = base / name
    case_dir.mkdir()
    case_dir.joinpath("metadata.json").write_text(
        json.dumps({
            "case_name": name,
            "element_type": element,
            "n_dofs": 12 if is_2d else 6,
        }),
        encoding="utf-8",
    )
    pd.DataFrame({
        "t_h": [0.0, 1.0, 2.0],
        "closure_pct": [0.0, 1.0, 2.0],
        "wall_disp_m": [0.0, -0.01, -0.02],
        "u_wall_m": [0.0, 0.01, 0.02],
    }).to_csv(case_dir / "closure.csv", index=False)

    rows = []
    z_values = [0.0, 1.0] if is_2d else [0.0]
    node_id = 0
    for t_h in [0.0, 1.0, 2.0]:
        for z in z_values:
            for r in [1.0, 2.0, 3.0]:
                rows.append({
                    "t_h": t_h,
                    "node_id": node_id,
                    "r_m": r,
                    "z_m": z,
                    "u_r_m": -0.01 * t_h / r,
                    "u_z_m": 0.0,
                })
                node_id += 1
    pd.DataFrame(rows).to_csv(case_dir / "displacements_profile.csv", index=False)

    wall = [
        {"t_h": t_h, "node_id": i, "z_m": z, "u_r_m": -0.01 * t_h * (1.0 + z)}
        for t_h in [0.0, 1.0, 2.0]
        for i, z in enumerate(z_values)
    ]
    pd.DataFrame(wall).to_csv(case_dir / "wall_profile.csv", index=False)
    return case_dir


class DisplacementPlotTests(unittest.TestCase):
    def test_displacement_plots_for_l3_and_q8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out_dir = base / "plots"
            l3 = load_result(write_case(base, "modelo_A_L3", "axisym_1d_L3", False))
            q8 = load_result(write_case(base, "modelo_A_Q8", "axisym_2d_Q8", True))

            plot_wall_displacement([l3, q8], out_dir, "element")
            plot_radial_profile(l3, out_dir)
            plot_radial_profile(q8, out_dir)
            plot_wall_profile(q8, out_dir)
            plot_field_map(q8, out_dir, 2.0)

            expected = [
                "deslocamento_parede_vs_tempo.png",
                "modelo_A_L3_perfil_radial_ur.png",
                "modelo_A_Q8_perfil_radial_ur.png",
                "modelo_A_Q8_perfil_parede_ur.png",
                "modelo_A_Q8_mapa_ur.png",
            ]
            for name in expected:
                self.assertTrue((out_dir / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
