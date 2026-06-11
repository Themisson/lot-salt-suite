import csv

import pytest

from tools import run_lot_pkn_sensitivity_matrix as runner


def write_matrix(path, timeseries_a=None):
    timeseries_text = str(timeseries_a).replace("\\", "/") if timeseries_a else None
    extra = f'\n    timeseries: "{timeseries_text}"' if timeseries_text else ""
    path.write_text(
        "matrix_id: test_matrix\n"
        "base_case: base.yaml\n"
        "mode: lot-pkn\n"
        "scenarios:\n"
        f"  - id: s0\n    case: case0.yaml{extra}\n"
        "  - id: s1\n    case: case1.yaml\n",
        encoding="utf-8",
    )


def write_timeseries(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"time_s": "0", "wellbore_pressure_Pa": "1000", "fracture_initiated": "false", "fracture_sink_applied_m3": "0"},
        {"time_s": "30", "wellbore_pressure_Pa": "2000", "fracture_initiated": "true", "fracture_sink_applied_m3": "0.1"},
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        runner.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "dry-run" in capsys.readouterr().out


def test_parse_matrix_yaml(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)

    spec = runner.load_matrix(matrix)

    assert spec.matrix_id == "test_matrix"
    assert len(spec.scenarios) == 2


def test_dry_run_writes_metadata(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)
    args = runner.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--dry-run"])

    metadata = runner.execute(args)

    assert metadata["dry_run"] is True
    assert metadata["scenario_count"] == 2


def test_only_summary_with_synthetic_data(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    ts0 = tmp_path / "s0.csv"
    write_timeseries(ts0)
    write_matrix(matrix, ts0)
    write_timeseries(tmp_path / "out" / "runs" / "s1" / "timeseries.csv")
    args = runner.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--only-summary"])

    metadata = runner.execute(args)

    assert metadata["summary_csv"] is not None
    rows = runner.read_csv(tmp_path / "out" / "summary.csv")
    assert len(rows) == 2


def test_missing_case_in_matrix_is_rejected(tmp_path):
    matrix = tmp_path / "bad.yaml"
    matrix.write_text("matrix_id: bad\nscenarios:\n  - id: s0\n", encoding="utf-8")

    with pytest.raises(ValueError):
        runner.load_matrix(matrix)


def test_custom_lot_sim_is_recorded(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)
    args = runner.build_parser().parse_args(
        ["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--dry-run", "--lot-sim", "custom-lot-sim"]
    )

    metadata = runner.execute(args)

    assert metadata["actions"][0]["validate"][0] == "custom-lot-sim"
