import csv
import json

import pytest

from tools import report_lot_pkn_sensitivity_matrix as reporter


FIELDNAMES = [
    "scenario_id",
    "case",
    "timeseries_csv",
    "max_pressure_Pa",
    "fracture_initiation_time_s",
    "first_sink_positive_time_s",
    "sink_delay_s",
    "final_pressure_Pa",
]


def write_summary(path):
    rows = [
        ("cgeom_075_next_step", 68102290.0, 510.0),
        ("cgeom_100_next_step", 67331393.0, 660.0),
        ("cgeom_060_next_step", 68856439.0, 420.0),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for scenario_id, pressure, opening in rows:
            writer.writerow(
                {
                    "scenario_id": scenario_id,
                    "case": f"{scenario_id}.yaml",
                    "timeseries_csv": f"{scenario_id}/timeseries.csv",
                    "max_pressure_Pa": pressure,
                    "fracture_initiation_time_s": opening,
                    "first_sink_positive_time_s": opening + 30.0,
                    "sink_delay_s": 30.0,
                    "final_pressure_Pa": pressure,
                }
            )


def write_metadata(path):
    path.write_text(
        json.dumps({"matrix_id": "buz67d_modern_refined_cgeom_sensitivity", "scenario_count": 3}),
        encoding="utf-8",
    )


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        reporter.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "legacy-opening-time-s" in capsys.readouterr().out


def test_generates_baseline_relative_report(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    report = reporter.summarize(summary, metadata)

    assert report["source"] == "BASELINE_RELATIVE"
    assert report["best_scenario_by_combined_score"] == "cgeom_100_next_step"


def test_generates_legacy_target_report(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    report = reporter.summarize(summary, metadata, legacy_opening_time_s=510.0, legacy_max_pressure_Pa=69035836.0)

    assert report["source"] == "LEGACY_TARGETS"
    assert report["best_factor_by_opening_time"] == 0.75


def test_best_factor_by_max_pressure(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    report = reporter.summarize(summary, metadata, legacy_opening_time_s=510.0, legacy_max_pressure_Pa=69035836.0)

    assert report["best_factor_by_max_pressure"] == 0.60


def test_best_factor_by_combined_score(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    report = reporter.summarize(summary, metadata, legacy_opening_time_s=510.0, legacy_max_pressure_Pa=69035836.0)

    assert report["best_factor_by_combined_score"] == 0.75


def test_cli_writes_json_and_markdown(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"
    write_summary(summary)
    write_metadata(metadata)

    code = reporter.main(
        [
            "--summary",
            str(summary),
            "--metadata",
            str(metadata),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--legacy-opening-time-s",
            "510",
            "--legacy-max-pressure-Pa",
            "69035836",
        ]
    )

    assert code == 0
    assert "SENSITIVITY_REPORT_GENERATED" in output_json.read_text(encoding="utf-8")
    assert "Ranking" in output_md.read_text(encoding="utf-8")


def test_missing_summary_columns_are_rejected(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    summary.write_text("scenario_id\ncgeom_075_next_step\n", encoding="utf-8")
    write_metadata(metadata)

    with pytest.raises(ValueError, match="missing required columns"):
        reporter.summarize(summary, metadata)


def test_missing_metadata_matrix_id_is_rejected(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    metadata.write_text(json.dumps({"scenario_count": 3}), encoding="utf-8")

    with pytest.raises(ValueError, match="matrix_id"):
        reporter.summarize(summary, metadata)
