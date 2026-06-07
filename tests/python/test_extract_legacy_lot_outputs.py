from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "extract_legacy_lot_outputs.py"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_legacy_lot_outputs", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ExtractLegacyLotOutputsTest(unittest.TestCase):
    def test_lot_tese_dat_extracts_key_blocks(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture = tmp_path / "legacy.dat"
            fixture.write_text(
                "\n".join(
                    [
                        "Annulars",
                        "2",
                        "3",
                        "",
                        "Time",
                        "0 0.5 1.0",
                        "Layer",
                        "1",
                        "dP",
                        "1",
                        "10 20 30",
                        "Layer",
                        "1",
                        "dV_leakoff",
                        "1",
                        "0 0.1 0.2",
                        "V_outflow",
                        "1",
                        "0 0.3 0.4",
                        "Momento da quebra: 0.5",
                    ]
                ),
                encoding="utf-8",
            )

            output_dir = tmp_path / "out"
            module.run([fixture], output_dir)
            points = read_csv(output_dir / "legacy_points.csv")
            summary = read_csv(output_dir / "legacy_summary.csv")[0]

            record_types = {row["record_type"] for row in points}
            self.assertIn("dP", record_types)
            self.assertIn("dV_leakoff", record_types)
            self.assertIn("V_outflow", record_types)
            self.assertIn("0.5", {row["time_raw"] for row in points})
            self.assertIn("1", {row["layer"] for row in points})
            self.assertEqual(summary["has_sigmaTheta"], "False")
            self.assertEqual(summary["has_pw"], "False")
            self.assertEqual(summary["has_margin"], "False")
            self.assertEqual(summary["has_opened"], "False")
            self.assertEqual(summary["comparison_readiness"], "limited_indirect")

    def test_lot_tese_dat_records_momento_da_quebra(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture = tmp_path / "breakdown_only.dat"
            fixture.write_text(
                "\n".join(
                    [
                        "Time",
                        "0 1",
                        "Layer",
                        "1",
                        "dP",
                        "1",
                        "1 2",
                        "Momento da quebra",
                        "1",
                    ]
                ),
                encoding="utf-8",
            )

            output_dir = tmp_path / "out"
            module.run([fixture], output_dir)
            points = read_csv(output_dir / "legacy_points.csv")
            self.assertTrue(points)
            self.assertEqual({row["momento_da_quebra_raw"] for row in points}, {"1"})

    def test_lot_apb_v5_json_converts_pressure_psi_to_pa(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture = tmp_path / "legacy.json"
            fixture.write_text(
                json.dumps(
                    {
                        "annuli": {
                            "0": {
                                "md": [100.0],
                                "results_by_time": [
                                    {
                                        "time": 12.0,
                                        "pressure": {
                                            "start": [1.0],
                                            "final": [2.0],
                                            "diff": [3.0],
                                            "APB": 4.0,
                                        },
                                        "volume": {
                                            "start": 10.0,
                                            "final": 11.0,
                                            "diff": 1.0,
                                        },
                                        "vented_bbl": 0.0,
                                        "leakage_bbl": 0.0,
                                        "leakage_mass": 0.0,
                                    }
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            output_dir = tmp_path / "out"
            module.run([fixture], output_dir)
            points = read_csv(output_dir / "legacy_points.csv")
            summary = read_csv(output_dir / "legacy_summary.csv")[0]
            self.assertEqual(len(points), 1)
            self.assertAlmostEqual(float(points[0]["pressure_start_Pa"]), module.PSI_TO_PA)
            self.assertAlmostEqual(float(points[0]["pressure_final_Pa"]), 2.0 * module.PSI_TO_PA)
            self.assertEqual(summary["has_pressure_Pa"], "True")
            self.assertEqual(summary["comparison_readiness"], "pressure_only")

    def test_lot_apb_v5_json_accepts_top_level_list_with_direct_annulus_results(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture = tmp_path / "legacy_list.json"
            fixture.write_text(
                json.dumps(
                    [
                        {
                            "annuli": {
                                "0": {
                                    "md": [100.0, 101.0],
                                    "pressure": {
                                        "start": [10.0, 11.0],
                                        "final": [12.0, 13.0],
                                        "diff": [2.0, 2.0],
                                        "APB": 2.0,
                                    },
                                    "volume": {"start": 1.0, "final": 2.0, "diff": 1.0},
                                }
                            }
                        }
                    ]
                ),
                encoding="utf-8",
            )

            output_dir = tmp_path / "out"
            module.run([fixture], output_dir)
            points = read_csv(output_dir / "legacy_points.csv")
            self.assertEqual(len(points), 2)
            self.assertAlmostEqual(float(points[1]["pressure_final_Pa"]), 13.0 * module.PSI_TO_PA)
            self.assertEqual(points[0]["time_raw"], "0")

    def test_directory_input_writes_points_summary_and_metadata(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "inputs"
            input_dir.mkdir()
            (input_dir / "legacy.dat").write_text(
                "\n".join(["Time", "0", "Layer", "1", "dP", "1", "5"]),
                encoding="utf-8",
            )
            (input_dir / "legacy.json").write_text(
                json.dumps(
                    {
                        "annuli": {
                            "A": {
                                "results_by_time": [
                                    {
                                        "time": 0,
                                        "pressure": {"start": 1, "final": 1, "diff": 0, "APB": 0},
                                    }
                                ]
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            output_dir = tmp_path / "out"
            module.run([input_dir], output_dir)

            self.assertTrue((output_dir / "legacy_points.csv").exists())
            self.assertTrue((output_dir / "legacy_summary.csv").exists())
            self.assertTrue((output_dir / "legacy_metadata.json").exists())
            metadata = json.loads((output_dir / "legacy_metadata.json").read_text(encoding="utf-8"))
            missing = set(metadata["field_groups"]["missing_without_instrumentation"])
            self.assertGreaterEqual(missing, {"pw", "sigmaTheta", "margin", "opened"})


if __name__ == "__main__":
    unittest.main()
