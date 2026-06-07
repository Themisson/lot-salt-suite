from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REAL_REDUCED_FIXTURE = ROOT / "tests" / "fixtures" / "legacy_modern_level0" / "buz67d_reduced"

REQUIRED_LEGACY_POINT_COLUMNS = {
    "source_file",
    "source_kind",
    "record_type",
    "annular",
    "time_raw",
    "time_unit_inferred",
    "time_s",
    "layer",
    "dP",
    "dV",
    "dV_leakoff",
    "V_outflow",
}

REQUIRED_MODERN_POINT_COLUMNS = {
    "case_id",
    "scenario_id",
    "scenario_label",
    "step_index",
    "time_s",
    "sample_index",
    "layer_id",
    "gp_id",
    "wall_pressure_Pa",
    "net_pressure_Pa",
    "sigma_theta_compression_positive_Pa",
    "hoop_state",
    "margin_Pa",
    "opened",
    "legacy_algebra_opened",
}

BLOCKED_FIELDS = ("sigmaTheta", "pw", "margin", "opened", "hoop_state", "j2", "von_mises")


def read_csv_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(required_columns - fieldnames)
        if missing:
            raise ValueError(f"{path.name} missing required column(s): {', '.join(missing)}")
        return list(reader)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("fixture rows must not be empty")

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def unique_numeric_values(rows: list[dict[str, str]], column: str) -> list[float]:
    values = {float(row[column]) for row in rows if row[column] != ""}
    return sorted(values)


def compare_legacy_modern_level0(
    legacy_points_csv: Path,
    legacy_summary_csv: Path,
    modern_points_csv: Path,
    modern_summary_csv: Path,
) -> dict[str, object]:
    legacy_points = read_csv_rows(legacy_points_csv, REQUIRED_LEGACY_POINT_COLUMNS)
    _legacy_summary = read_csv_rows(legacy_summary_csv, {"source_file", "n_records"})
    modern_points = read_csv_rows(modern_points_csv, REQUIRED_MODERN_POINT_COLUMNS)
    _modern_summary = read_csv_rows(modern_summary_csv, {"case_id", "n_points"})

    legacy_times = unique_numeric_values(legacy_points, "time_raw")
    modern_times = unique_numeric_values(modern_points, "time_s")
    legacy_layers = {row["layer"] for row in legacy_points if row["layer"] != ""}
    modern_steps = {row["step_index"] for row in modern_points if row["step_index"] != ""}
    samples_per_step: dict[str, int] = {}
    for row in modern_points:
        step = row["step_index"]
        samples_per_step[step] = samples_per_step.get(step, 0) + 1

    metrics = {
        "legacy_n_records": len(legacy_points),
        "legacy_n_times": len(legacy_times),
        "legacy_time_min_raw": min(legacy_times),
        "legacy_time_max_raw": max(legacy_times),
        "legacy_n_layers": len(legacy_layers),
        "modern_n_points": len(modern_points),
        "modern_n_steps": len(modern_steps),
        "modern_time_min_s": min(modern_times),
        "modern_time_max_s": max(modern_times),
        "modern_n_samples_per_step": samples_per_step,
    }

    metric_status = {
        "legacy_n_records": "safe",
        "legacy_n_times": "safe",
        "legacy_time_min_raw": "safe",
        "legacy_time_max_raw": "safe",
        "legacy_n_layers": "safe",
        "modern_n_points": "safe",
        "modern_n_steps": "safe",
        "modern_time_min_s": "safe",
        "modern_time_max_s": "safe",
        "modern_n_samples_per_step": "safe",
        "legacy_modern_time_alignment": "requires_time_unit_normalization",
        "legacy_modern_layer_alignment": "requires_layer_mapping",
        "sigmaTheta": "not_available",
        "pw": "not_available",
        "margin": "not_available",
        "opened": "not_available",
    }

    caveats = [
        "legacy time unit is unknown",
        "legacy Layer is 1-based and not equivalent to wall_gp_*",
        "sigmaTheta is not exported by legacy output",
        "pw is not exported by legacy output",
        "margin is not exported by legacy output",
        "opened is not exported by legacy output",
        "comparison is structural only, not physical validation",
    ]

    return {
        "metrics": metrics,
        "metric_status": metric_status,
        "caveats": caveats,
        "blocked_fields": list(BLOCKED_FIELDS),
        "compared_fields": sorted(metrics.keys()),
    }


def create_level0_fixtures(tmp_path: Path) -> dict[str, Path]:
    legacy_points = tmp_path / "legacy_points.csv"
    write_csv(
        legacy_points,
        [
            {
                "source_file": "8-BUZ-67D-PKN.dat",
                "source_kind": "LOT_Tese",
                "record_type": "dat_row",
                "annular": "A1",
                "time_raw": 0,
                "time_unit_inferred": "unknown",
                "time_s": "",
                "layer": 1,
                "dP": 1000,
                "dV": 0.1,
                "dV_leakoff": 0.01,
                "V_outflow": 0.00,
            },
            {
                "source_file": "8-BUZ-67D-PKN.dat",
                "source_kind": "LOT_Tese",
                "record_type": "dat_row",
                "annular": "A1",
                "time_raw": 1,
                "time_unit_inferred": "unknown",
                "time_s": "",
                "layer": 1,
                "dP": 1100,
                "dV": 0.2,
                "dV_leakoff": 0.02,
                "V_outflow": 0.00,
            },
            {
                "source_file": "8-BUZ-67D-PKN.dat",
                "source_kind": "LOT_Tese",
                "record_type": "dat_row",
                "annular": "A1",
                "time_raw": 0,
                "time_unit_inferred": "unknown",
                "time_s": "",
                "layer": 2,
                "dP": 900,
                "dV": 0.1,
                "dV_leakoff": 0.00,
                "V_outflow": 0.01,
            },
        ],
    )

    legacy_summary = tmp_path / "legacy_summary.csv"
    write_csv(
        legacy_summary,
        [
            {
                "source_file": "8-BUZ-67D-PKN.dat",
                "source_kind": "LOT_Tese",
                "n_records": 3,
                "has_time": "true",
                "has_layer": "true",
                "has_dP": "true",
                "has_dV_leakoff": "true",
                "has_pressure_json": "false",
                "has_pressure_Pa": "false",
                "has_sigmaTheta": "false",
                "has_pw": "false",
                "has_margin": "false",
                "has_opened": "false",
                "comparison_readiness": "limited_indirect",
                "notes": "fixture",
            }
        ],
    )

    modern_points = tmp_path / "modern_points.csv"
    write_csv(
        modern_points,
        [
            {
                "case_id": "buz67d_pkn",
                "scenario_id": "lithostatic_geostatic",
                "scenario_label": "fixture",
                "step_index": 0,
                "time_s": 0,
                "sample_index": 0,
                "layer_id": "wall_gp_0",
                "gp_id": 0,
                "wall_pressure_Pa": 1000,
                "net_pressure_Pa": 100,
                "sigma_theta_compression_positive_Pa": 900,
                "hoop_state": "Compressive",
                "margin_Pa": 100,
                "opened": "true",
                "legacy_algebra_opened": "true",
            },
            {
                "case_id": "buz67d_pkn",
                "scenario_id": "lithostatic_geostatic",
                "scenario_label": "fixture",
                "step_index": 1,
                "time_s": 60,
                "sample_index": 0,
                "layer_id": "wall_gp_0",
                "gp_id": 0,
                "wall_pressure_Pa": 1100,
                "net_pressure_Pa": 120,
                "sigma_theta_compression_positive_Pa": 950,
                "hoop_state": "Compressive",
                "margin_Pa": 150,
                "opened": "true",
                "legacy_algebra_opened": "true",
            },
        ],
    )

    modern_summary = tmp_path / "modern_summary.csv"
    write_csv(
        modern_summary,
        [
            {
                "case_id": "buz67d_pkn",
                "scenario_id": "lithostatic_geostatic",
                "scenario_label": "fixture",
                "n_points": 2,
                "n_compressive": 2,
                "n_neutral": 0,
                "n_tensile": 0,
                "min_sigma_theta_compression_positive_Pa": 900,
                "max_sigma_theta_compression_positive_Pa": 950,
                "min_margin_Pa": 100,
                "max_margin_Pa": 150,
                "any_opened": "true",
                "any_legacy_algebra_opened": "true",
            }
        ],
    )

    return {
        "legacy_points": legacy_points,
        "legacy_summary": legacy_summary,
        "modern_points": modern_points,
        "modern_summary": modern_summary,
    }


class CompareLegacyModernLevel0Test(unittest.TestCase):
    def test_real_reduced_legacy_modern_fixture_comparison(self) -> None:
        result = compare_legacy_modern_level0(
            REAL_REDUCED_FIXTURE / "legacy_points.csv",
            REAL_REDUCED_FIXTURE / "legacy_summary.csv",
            REAL_REDUCED_FIXTURE / "modern_points.csv",
            REAL_REDUCED_FIXTURE / "modern_summary.csv",
        )

        metrics = result["metrics"]
        self.assertEqual(metrics["legacy_n_records"], 4)
        self.assertEqual(metrics["legacy_n_times"], 2)
        self.assertEqual(metrics["legacy_time_min_raw"], 0.0)
        self.assertEqual(metrics["legacy_time_max_raw"], 0.5)
        self.assertEqual(metrics["legacy_n_layers"], 2)
        self.assertEqual(metrics["modern_n_points"], 3)
        self.assertEqual(metrics["modern_n_steps"], 3)
        self.assertEqual(metrics["modern_time_min_s"], 0.0)
        self.assertEqual(metrics["modern_time_max_s"], 60.0)
        self.assertEqual(metrics["modern_n_samples_per_step"], {"0": 1, "1": 1, "2": 1})

        caveats = "\n".join(result["caveats"])
        self.assertIn("structural only", caveats)
        self.assertIn("sigmaTheta is not exported", caveats)
        self.assertIn("pw is not exported", caveats)

    def test_basic_structural_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = create_level0_fixtures(Path(tmp))

            result = compare_legacy_modern_level0(
                paths["legacy_points"],
                paths["legacy_summary"],
                paths["modern_points"],
                paths["modern_summary"],
            )

            metrics = result["metrics"]
            self.assertEqual(metrics["legacy_n_records"], 3)
            self.assertEqual(metrics["legacy_n_times"], 2)
            self.assertEqual(metrics["legacy_time_min_raw"], 0.0)
            self.assertEqual(metrics["legacy_time_max_raw"], 1.0)
            self.assertEqual(metrics["legacy_n_layers"], 2)
            self.assertEqual(metrics["modern_n_points"], 2)
            self.assertEqual(metrics["modern_n_steps"], 2)
            self.assertEqual(metrics["modern_time_min_s"], 0.0)
            self.assertEqual(metrics["modern_time_max_s"], 60.0)
            self.assertEqual(metrics["modern_n_samples_per_step"], {"0": 1, "1": 1})

    def test_metric_statuses_mark_normalization_and_mapping_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = create_level0_fixtures(Path(tmp))

            result = compare_legacy_modern_level0(
                paths["legacy_points"],
                paths["legacy_summary"],
                paths["modern_points"],
                paths["modern_summary"],
            )

            status = result["metric_status"]
            self.assertEqual(status["legacy_time_min_raw"], "safe")
            self.assertEqual(status["legacy_time_max_raw"], "safe")
            self.assertEqual(status["legacy_modern_time_alignment"], "requires_time_unit_normalization")
            self.assertEqual(status["legacy_modern_layer_alignment"], "requires_layer_mapping")

    def test_required_caveats_are_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = create_level0_fixtures(Path(tmp))

            result = compare_legacy_modern_level0(
                paths["legacy_points"],
                paths["legacy_summary"],
                paths["modern_points"],
                paths["modern_summary"],
            )

            caveats = "\n".join(result["caveats"])
            self.assertIn("time unit is unknown", caveats)
            self.assertIn("Layer is 1-based", caveats)
            self.assertIn("sigmaTheta is not exported", caveats)
            self.assertIn("pw is not exported", caveats)
            self.assertIn("margin is not exported", caveats)
            self.assertIn("opened is not exported", caveats)
            self.assertIn("structural only", caveats)

    def test_blocked_fields_are_not_compared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = create_level0_fixtures(Path(tmp))

            result = compare_legacy_modern_level0(
                paths["legacy_points"],
                paths["legacy_summary"],
                paths["modern_points"],
                paths["modern_summary"],
            )

            compared_fields = set(result["compared_fields"])
            for field in BLOCKED_FIELDS:
                self.assertNotIn(field, compared_fields)
            self.assertEqual(result["metric_status"]["sigmaTheta"], "not_available")
            self.assertEqual(result["metric_status"]["pw"], "not_available")
            self.assertEqual(result["metric_status"]["margin"], "not_available")
            self.assertEqual(result["metric_status"]["opened"], "not_available")

    def test_missing_input_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = create_level0_fixtures(Path(tmp))

            with self.assertRaises(FileNotFoundError):
                compare_legacy_modern_level0(
                    Path(tmp) / "missing_legacy_points.csv",
                    paths["legacy_summary"],
                    paths["modern_points"],
                    paths["modern_summary"],
                )

            with self.assertRaises(FileNotFoundError):
                compare_legacy_modern_level0(
                    paths["legacy_points"],
                    paths["legacy_summary"],
                    Path(tmp) / "missing_modern_points.csv",
                    paths["modern_summary"],
                )

    def test_missing_required_time_columns_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = create_level0_fixtures(tmp_path)

            bad_legacy = tmp_path / "bad_legacy_points.csv"
            write_csv(
                bad_legacy,
                [
                    {
                        "source_file": "8-BUZ-67D-PKN.dat",
                        "source_kind": "LOT_Tese",
                        "record_type": "dat_row",
                        "annular": "A1",
                        "time_unit_inferred": "unknown",
                        "time_s": "",
                        "layer": 1,
                        "dP": 1000,
                        "dV": 0.1,
                        "dV_leakoff": 0.01,
                        "V_outflow": 0.0,
                    }
                ],
            )
            with self.assertRaisesRegex(ValueError, "time_raw"):
                compare_legacy_modern_level0(
                    bad_legacy,
                    paths["legacy_summary"],
                    paths["modern_points"],
                    paths["modern_summary"],
                )

            bad_modern = tmp_path / "bad_modern_points.csv"
            write_csv(
                bad_modern,
                [
                    {
                        "case_id": "buz67d_pkn",
                        "scenario_id": "lithostatic_geostatic",
                        "scenario_label": "fixture",
                        "step_index": 0,
                        "sample_index": 0,
                        "layer_id": "wall_gp_0",
                        "gp_id": 0,
                        "wall_pressure_Pa": 1000,
                        "net_pressure_Pa": 100,
                        "sigma_theta_compression_positive_Pa": 900,
                        "hoop_state": "Compressive",
                        "margin_Pa": 100,
                        "opened": "true",
                        "legacy_algebra_opened": "true",
                    }
                ],
            )
            with self.assertRaisesRegex(ValueError, "time_s"):
                compare_legacy_modern_level0(
                    paths["legacy_points"],
                    paths["legacy_summary"],
                    bad_modern,
                    paths["modern_summary"],
                )


if __name__ == "__main__":
    unittest.main()
