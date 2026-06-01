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
    plot_creep_rate,
    plot_damage_wall,
    plot_damage_comparison,
    plot_phase_space,
)


def write_damage_case(base: Path, name: str, with_damage: bool) -> Path:
    case_dir = base / name
    case_dir.mkdir()
    case_dir.joinpath("metadata.json").write_text(
        json.dumps({
            "case_name": name,
            "element_type": "axisym_1d_L3",
            "n_dofs": 9,
            "damage_thresholds": [0.1, 0.3, 0.5, 0.8],
            "failure_D_critical": 0.5,
        }),
        encoding="utf-8",
    )
    pd.DataFrame({
        "t_h": [0.0, 1.0, 2.0],
        "closure_pct": [0.0, 1.0, 3.0 if with_damage else 2.0],
        "wall_disp_m": [0.0, -0.01, -0.03 if with_damage else -0.02],
        "u_wall_m": [0.0, 0.01, 0.03 if with_damage else 0.02],
    }).to_csv(case_dir / "closure.csv", index=False)
    if with_damage:
        pd.DataFrame({
            "t_h": [0.0, 1.0, 2.0],
            "D": [0.0, 0.2, 0.6],
            "eps_dot": [1.0e-9, 8.0e-10, 2.0e-8],
            "sigma_ef": [1.0e6, 1.2e6, 2.0e6],
        }).to_csv(case_dir / "damage_wall.csv", index=False)
        pd.DataFrame({
            "t_h": [2.0],
            "r": [1.0],
            "z": [0.0],
            "gp_id": [0],
            "D": [0.6],
            "eps_dot": [2.0e-8],
            "event_type": ["inflection"],
        }).to_csv(case_dir / "damage_events.csv", index=False)
    return case_dir


class DamagePlotTests(unittest.TestCase):
    def test_damage_plots_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out_dir = base / "plots"
            no_damage = load_result(write_damage_case(base, "no_damage", False))
            with_damage = load_result(write_damage_case(base, "with_damage", True))

            plot_damage_wall([with_damage], out_dir)
            plot_creep_rate([with_damage], out_dir)
            plot_phase_space([with_damage], out_dir)
            plot_damage_comparison([no_damage, with_damage], out_dir, None)

            for name in [
                "dano_parede_vs_tempo.png",
                "taxa_fluencia_parede.png",
                "espaco_fase_sigmaef_D.png",
                "closure_vs_tempo.png",
            ]:
                self.assertTrue((out_dir / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
