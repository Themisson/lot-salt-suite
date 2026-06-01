from __future__ import annotations

import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "post"))

from saltpost.compare import align_series, comparison_table  # noqa: E402
from saltpost.io import load_result  # noqa: E402
from saltpost.units import auto_displacement_unit  # noqa: E402
from saltpost.registry import discover_results  # noqa: E402
from saltpost.registry import label_for  # noqa: E402
from saltpost.style import get_color, get_marker  # noqa: E402
from displacement_viewer import generate_html  # noqa: E402


def write_result(base: Path, name: str, element: str, dofs: int, values: list[float]) -> Path:
    case_dir = base / name
    case_dir.mkdir()
    (case_dir / "metadata.json").write_text(
        json.dumps({
            "case_name": name,
            "element_type": element,
            "n_dofs": dofs,
            "time_scheme": "explicit",
            "wall_time_s": 1.25,
        }),
        encoding="utf-8",
    )
    pd.DataFrame({
        "t_h": [0.0, 1.0, 2.0],
        "closure_pct": values,
        "wall_disp_m": [0.0, -0.01, -0.02],
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
    pd.DataFrame({
        "t_h": [0.0, 1.0],
        "node_id": [0, 0],
        "z_m": [0.0, 0.0],
        "u_r_m": [0.0, -0.01],
    }).to_csv(case_dir / "wall_profile.csv", index=False)
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


class SaltPostTests(unittest.TestCase):
    def test_io_loads_closure_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = write_result(Path(tmp), "modelo_A_Q8", "axisym_2d_Q8", 42, [0.0, 1.0, 2.0])
            result = load_result(case_dir)

            self.assertEqual(result.case_name, "modelo_A_Q8")
            self.assertEqual(result.element_type, "axisym_2d_Q8")
            self.assertEqual(result.n_dofs, 42)
            self.assertEqual(result.final_closure, 2.0)
            self.assertIsNotNone(result.closure)
            self.assertIsNotNone(result.displacement_profile)
            self.assertIsNotNone(result.wall_profile)
            self.assertIsNotNone(result.damage_wall)
            self.assertIsNotNone(result.damage_events)
            self.assertEqual(list(result.closure["t_h"]), [0.0, 1.0, 2.0])
            self.assertIn("u_wall_m", result.closure.columns)
            self.assertEqual(result.inner_radius_m, 1.0)

    def test_compare_aligns_series_and_computes_relative_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ref_dir = write_result(base, "ref", "axisym_1d_L3", 11, [0.0, 1.0, 2.0])
            other_dir = write_result(base, "other", "axisym_2d_Q8", 22, [0.0, 1.5, 3.0])
            ref = load_result(ref_dir)
            other = load_result(other_dir)

            aligned = align_series(ref.closure, other.closure)
            self.assertEqual(list(aligned["t_h"]), [0.0, 1.0, 2.0])
            self.assertEqual(aligned["relative_error"].iloc[1], 0.5)

            table = comparison_table([ref, other], ref)
            self.assertEqual(list(table["case"]), ["ref", "other"])
            self.assertEqual(table.loc[1, "error_vs_ref"], 0.5)

    def test_registry_discovers_result_folders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_result(base, "modelo_A_L3", "axisym_1d_L3", 11, [0.0, 1.0, 2.0])
            write_result(base, "modelo_A_Q8", "axisym_2d_Q8", 22, [0.0, 1.1, 2.2])
            (base / "not_a_result").mkdir()

            results = discover_results(str(base / "modelo_A_*"))
            self.assertEqual([r.case_name for r in results], ["modelo_A_L3", "modelo_A_Q8"])

    def test_auto_displacement_units(self) -> None:
        self.assertEqual(auto_displacement_unit(5.0e-4), (1.0e6, "μm"))
        self.assertEqual(auto_displacement_unit(5.0e-3), (1.0e3, "mm"))
        self.assertEqual(auto_displacement_unit(5.0e-1), (1.0e2, "cm"))
        self.assertEqual(auto_displacement_unit(2.0), (1.0, "m"))

    def test_case_color_and_marker_when_elements_match(self) -> None:
        color_a = get_color(0, "axisym_1d_L3", all_elements_same=True)
        color_b = get_color(1, "axisym_1d_L3", all_elements_same=True)
        marker_a = get_marker(0, "axisym_1d_L3", all_elements_same=True)
        marker_b = get_marker(1, "axisym_1d_L3", all_elements_same=True)

        self.assertNotEqual(color_a, color_b)
        self.assertNotEqual(marker_a, marker_b)

    def test_element_color_when_elements_differ(self) -> None:
        self.assertEqual(get_color(0, "axisym_1d_L3", all_elements_same=False), "#1f77b4")
        self.assertEqual(get_color(1, "axisym_2d_Q8", all_elements_same=False), "#d62728")

    def test_labels_include_case_and_element_when_grouped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = write_result(Path(tmp), "modelo_A", "axisym_1d_L3", 11, [0.0, 1.0, 2.0])
            result = load_result(case_dir)

            self.assertIn("modelo_A", label_for(result, "element"))
            self.assertIn("axisym_1d_L3", label_for(result, "element"))

    def test_displacement_viewer_generates_valid_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = write_result(Path(tmp), "modelo_A_Q8", "axisym_2d_Q8", 42, [0.0, 1.0, 2.0])
            out = generate_html(case_dir)

            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            HTMLParser().feed(text)
            self.assertIn("Deslocamento radial na parede", text)
            self.assertIn("payload", text)


if __name__ == "__main__":
    unittest.main()
