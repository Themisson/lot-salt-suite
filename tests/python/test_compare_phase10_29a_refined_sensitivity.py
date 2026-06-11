import csv

import pytest

from tools import compare_phase10_29a_refined_sensitivity as compare


def write_timeseries(path, pressure, opened_time=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "time_s": "0",
            "wellbore_pressure_Pa": "1000",
            "fracture_initiated": "false",
            "fracture_sink_applied_m3": "0",
            "fracture_volume_m3": "0",
            "leakoff_volume_m3": "0",
        },
        {
            "time_s": str(opened_time if opened_time is not None else 30),
            "wellbore_pressure_Pa": str(pressure),
            "fracture_initiated": "true" if opened_time is not None else "false",
            "fracture_sink_applied_m3": "0.1" if opened_time is not None else "0",
            "fracture_volume_m3": "1.0",
            "leakoff_volume_m3": "0.0",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        compare.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "sensitivity-root" in capsys.readouterr().out


def test_reads_synthetic_matrix_and_classifies_completed(tmp_path):
    root = tmp_path / "sens"
    write_timeseries(root / "buz67d_modern_refined_sens_cgeom_070" / "timeseries.csv", 70_000_000, 540)
    write_timeseries(root / "buz67d_modern_refined_sens_cgeom_075" / "timeseries.csv", 68_000_000, 510)
    write_timeseries(root / "buz67d_modern_refined_sens_baseline" / "timeseries.csv", 67_000_000, 660)

    metadata = compare.compare(root, tmp_path / "out")

    assert compare.CLASS_COMPLETED in metadata["classification"]
    assert metadata["best_factor_by_opening_time"] == 0.75


def test_best_factor_by_max_pressure(tmp_path):
    root = tmp_path / "sens"
    write_timeseries(root / "buz67d_modern_refined_sens_cgeom_070" / "timeseries.csv", 60_000_000, 540)
    write_timeseries(root / "buz67d_modern_refined_sens_cgeom_075" / "timeseries.csv", compare.LEGACY_MAX_PRESSURE_PA, 510)
    write_timeseries(root / "buz67d_modern_refined_sens_baseline" / "timeseries.csv", 67_000_000, 660)

    metadata = compare.compare(root, tmp_path / "out")

    assert metadata["best_factor_by_max_pressure"] == 0.75


def test_combined_score_prefers_balanced_case(tmp_path):
    root = tmp_path / "sens"
    write_timeseries(root / "buz67d_modern_refined_sens_cgeom_065" / "timeseries.csv", compare.LEGACY_MAX_PRESSURE_PA, 600)
    write_timeseries(root / "buz67d_modern_refined_sens_cgeom_075" / "timeseries.csv", 68_000_000, 510)
    write_timeseries(root / "buz67d_modern_refined_sens_baseline" / "timeseries.csv", 67_000_000, 660)

    metadata = compare.compare(root, tmp_path / "out")

    assert metadata["best_factor_by_combined_score"] == 0.75


def test_missing_scenarios_are_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        compare.compare(tmp_path / "missing", tmp_path / "out")
