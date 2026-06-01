from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "postprocess" / "scripts" / "lot_pkn_report.py"
FIXTURE = ROOT / "tests" / "fixtures" / "lot_pkn_modern"


def load_module():
    spec = importlib.util.spec_from_file_location("lot_pkn_report", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LotPknPostprocessTest(unittest.TestCase):
    def test_generates_required_pngs_and_html(self) -> None:
        module = load_module()
        output_dir = ROOT / "tmp" / "test_lot_pkn_report"

        generated = module.generate_report(
            FIXTURE / "timeseries.csv",
            FIXTURE / "result.json",
            output_dir,
        )

        generated_names = {path.name for path in generated}
        self.assertEqual(
            generated_names,
            {
                "pressure_vs_time.png",
                "pressure_vs_volume.png",
                "length_vs_time.png",
                "width_vs_time.png",
                "leakoff_vs_time.png",
                "report.html",
            },
        )
        for path in generated:
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

        html = (output_dir / "report.html").read_text(encoding="utf-8")
        self.assertIn("Modern synthetic LOT/PKN output - no legacy regression", html)
        self.assertIn("No numerical regression against legacy was performed", html)
        self.assertIn("R09 still blocks regressions involving idQ == 4", html)

    def test_missing_required_column_raises_clear_error(self) -> None:
        module = load_module()
        bad_csv = ROOT / "tmp" / "bad_lot_pkn_missing_column.csv"
        bad_csv.parent.mkdir(parents=True, exist_ok=True)
        bad_csv.write_text("time_s,net_pressure_Pa\n0,0\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "missing required column"):
            module.load_timeseries(bad_csv)

    def test_nan_values_are_rejected(self) -> None:
        module = load_module()
        bad_csv = ROOT / "tmp" / "bad_lot_pkn_nan.csv"
        bad_csv.parent.mkdir(parents=True, exist_ok=True)
        bad_csv.write_text(
            "time_s,injected_volume_m3,fracture_length_m,fracture_width_m,"
            "fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa\n"
            "0,0,0,0,0,0,nan\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "NaN"):
            module.load_timeseries(bad_csv)


if __name__ == "__main__":
    unittest.main()
