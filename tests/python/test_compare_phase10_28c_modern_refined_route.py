import csv

import pytest

from tools import compare_phase10_28c_modern_refined_route as compare


def write_timeseries(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sample_rows(open_time="30", sink_value="0.1"):
    return [
        {
            "time_s": "0",
            "wellbore_pressure_Pa": "1000",
            "fracture_initiated": "false",
            "fracture_sink_applied_m3": "0",
            "injected_volume_m3": "0.0",
            "fracture_volume_m3": "0.0",
            "leakoff_volume_m3": "0.0",
        },
        {
            "time_s": open_time,
            "wellbore_pressure_Pa": "2000",
            "fracture_initiated": "true",
            "fracture_sink_applied_m3": sink_value,
            "injected_volume_m3": "1.0",
            "fracture_volume_m3": "0.2",
            "leakoff_volume_m3": "0.1",
        },
    ]


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        compare.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "sensitivity-root" in capsys.readouterr().out


def test_route_additional_well(tmp_path):
    modern_csv = tmp_path / "additional" / "timeseries.csv"
    write_timeseries(modern_csv, sample_rows())

    metadata = compare.compare_additional(modern_csv, tmp_path / "out")

    assert metadata["classification"] == compare.CLASS_ADDITIONAL_NO_LEGACY
    assert metadata["metrics"][0]["max_pressure_Pa"] == 2000.0


def test_route_sensitivity(tmp_path):
    root = tmp_path / "sensitivity"
    for scenario in [
        "buz67d_modern_refined_sens_baseline",
        "buz67d_modern_refined_sens_cgeom_075",
        "buz67d_modern_refined_sens_cgeom_125",
        "buz67d_modern_refined_sens_same_step",
    ]:
        write_timeseries(root / scenario / "timeseries.csv", sample_rows())

    metadata = compare.compare_sensitivity(root, tmp_path / "out")

    assert metadata["classification"] == compare.CLASS_SENSITIVITY_OK
    assert len(metadata["metrics"]) == 4


def test_classification_additional_case_run_ok_constant_exists():
    assert compare.CLASS_ADDITIONAL_OK == "PHASE10_28C_ADDITIONAL_CASE_RUN_OK"


def test_classification_sensitivity_matrix_run_ok(tmp_path):
    root = tmp_path / "sensitivity"
    write_timeseries(root / "buz67d_modern_refined_sens_baseline" / "timeseries.csv", sample_rows())

    metadata = compare.compare_sensitivity(root, tmp_path / "out")

    assert metadata["classification"] == compare.CLASS_SENSITIVITY_INCONCLUSIVE


def test_missing_outputs_fail(tmp_path):
    with pytest.raises(FileNotFoundError):
        compare.compare_sensitivity(tmp_path / "missing", tmp_path / "out")
