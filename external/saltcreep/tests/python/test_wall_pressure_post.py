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
    plot_wall_pressure_map,
    plot_wall_pressure_profile,
    plot_wall_pressure_time,
)


def write_pressure_case(base: Path) -> Path:
    case_dir = base / "mud_gradient_2d_Q8_8p5ppg"
    case_dir.mkdir()
    case_dir.joinpath("metadata.json").write_text(
        json.dumps({
            "case_name": case_dir.name,
            "element_type": "axisym_2d_Q8",
            "n_dofs": 42,
            "depth_origin_m": 4100.0,
        }),
        encoding="utf-8",
    )
    rows = []
    for t_h in [0.0, 1.0, 2.0]:
        for node_id, z_m in enumerate([0.0, 500.0, 1000.0]):
            rows.append({
                "t_h": t_h,
                "node_id": node_id,
                "z_m": z_m,
                "depth_m": 4100.0 + z_m,
                "p_wall_Pa": 4.0e7 + 1.0e5 * t_h + 1.0e4 * z_m,
                "T_wall_K": 370.0 + 0.5 * t_h,
            })
    pd.DataFrame(rows).to_csv(case_dir / "wall_pressure_profile.csv", index=False)
    return case_dir


class WallPressurePostTests(unittest.TestCase):
    def test_wall_pressure_plots_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out_dir = base / "plots"
            result = load_result(write_pressure_case(base))

            self.assertIsNotNone(result.wall_pressure_profile)
            plot_wall_pressure_profile(result, out_dir)
            plot_wall_pressure_time(result, out_dir)
            plot_wall_pressure_map(result, out_dir)

            expected = [
                "mud_gradient_2d_Q8_8p5ppg_perfil_pressao_parede.png",
                "mud_gradient_2d_Q8_8p5ppg_pressao_parede_vs_tempo.png",
                "mud_gradient_2d_Q8_8p5ppg_mapa_pressao_parede.png",
            ]
            for name in expected:
                self.assertTrue((out_dir / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
