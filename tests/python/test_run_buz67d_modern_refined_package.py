import csv
import json
from pathlib import Path

import pytest

from tools import run_buz67d_modern_refined_package as package


def write_matrix(path: Path):
    case = path.parent / "case.yaml"
    case.write_text("metadata:\n  name: fixture\n", encoding="utf-8")
    path.write_text(
        "matrix_id: fixture_matrix\n"
        "mode: lot-pkn\n"
        "scenarios:\n"
        f"  - id: cgeom_100_next_step\n    case: {case.as_posix()}\n",
        encoding="utf-8",
    )
    return case


def write_summary(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "case",
                "timeseries_csv",
                "max_pressure_Pa",
                "fracture_initiation_time_s",
                "first_sink_positive_time_s",
                "sink_delay_s",
                "final_pressure_Pa",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "scenario_id": "cgeom_100_next_step",
                "case": "case.yaml",
                "timeseries_csv": "timeseries.csv",
                "max_pressure_Pa": "1000",
                "fracture_initiation_time_s": "510",
                "first_sink_positive_time_s": "540",
                "sink_delay_s": "30",
                "final_pressure_Pa": "1000",
            }
        )


def write_metadata(path: Path):
    path.write_text(json.dumps({"matrix_id": "fixture_matrix", "scenario_count": 1}), encoding="utf-8")


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        package.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "dry-run" in capsys.readouterr().out


def test_dry_run_writes_metadata_and_commands(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)
    args = package.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--dry-run"])

    metadata = package.execute(args)

    assert metadata["status"] == "BUZ67D_MODERN_REFINED_PACKAGE_DRY_RUN"
    assert (tmp_path / "out" / "package_metadata.json").exists()
    assert "run_lot_pkn_sensitivity_matrix.py" in (tmp_path / "out" / "run_commands.txt").read_text(encoding="utf-8")


def test_matrix_must_exist(tmp_path):
    args = package.build_parser().parse_args(["--matrix", str(tmp_path / "missing.yaml"), "--output-dir", str(tmp_path / "out"), "--dry-run"])

    with pytest.raises(FileNotFoundError):
        package.execute(args)


def test_missing_lot_sim_is_rejected_without_dry_run(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)
    args = package.build_parser().parse_args(
        ["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--lot-sim", str(tmp_path / "missing-lot-sim.exe")]
    )

    with pytest.raises(FileNotFoundError, match="lot-sim"):
        package.execute(args)


def test_only_report_uses_existing_fixture_outputs(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)
    summary = tmp_path / "summary.csv"
    metadata_json = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata_json)
    args = package.build_parser().parse_args(
        [
            "--matrix",
            str(matrix),
            "--output-dir",
            str(tmp_path / "out"),
            "--only-report",
            "--existing-summary",
            str(summary),
            "--existing-metadata",
            str(metadata_json),
        ]
    )

    metadata = package.execute(args)

    assert metadata["status"] == "BUZ67D_MODERN_REFINED_PACKAGE_RUN_OK"
    assert (tmp_path / "out" / "sensitivity_report.json").exists()


def test_dry_run_records_minimal_validations(tmp_path):
    matrix = tmp_path / "matrix.yaml"
    write_matrix(matrix)
    args = package.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--dry-run"])

    metadata = package.execute(args)

    assert len(metadata["commands"]["minimal_validations"]) == 3
    assert metadata["commands"]["minimal_validations"][0][1] == "validate"
