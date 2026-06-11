import csv
import json

import pytest

from tools import verify_phase11_3a_v2_sensitivity_run as verifier


def write_summary(path, partial=False):
    rows = [
        {
            "scenario_id": "cgeom_075_next_step",
            "case": "generated/cgeom_075.yaml",
            "timeseries_csv": "runs/cgeom_075/timeseries.csv",
            "max_pressure_Pa": "68102290.56",
            "fracture_initiation_time_s": "510",
            "first_sink_positive_time_s": "540",
            "sink_delay_s": "30",
            "final_pressure_Pa": "68102290.56",
            "materialized_case_path": "generated/cgeom_075.yaml",
        },
        {
            "scenario_id": "cgeom_100_next_step",
            "case": "generated/cgeom_100.yaml",
            "timeseries_csv": "runs/cgeom_100/timeseries.csv",
            "max_pressure_Pa": "67331393.61",
            "fracture_initiation_time_s": "660",
            "first_sink_positive_time_s": "690",
            "sink_delay_s": "30",
            "final_pressure_Pa": "67331393.61",
            "materialized_case_path": "generated/cgeom_100.yaml",
        },
        {
            "scenario_id": "cgeom_125_next_step",
            "case": "generated/cgeom_125.yaml",
            "timeseries_csv": "runs/cgeom_125/timeseries.csv",
            "max_pressure_Pa": "63888110.88",
            "fracture_initiation_time_s": "",
            "first_sink_positive_time_s": "",
            "sink_delay_s": "",
            "final_pressure_Pa": "63888110.88",
            "materialized_case_path": "generated/cgeom_125.yaml",
        },
    ]
    if not partial:
        rows.append(
            {
                "scenario_id": "cgeom_100_same_step",
                "case": "generated/cgeom_100_same_step.yaml",
                "timeseries_csv": "runs/cgeom_100_same_step/timeseries.csv",
                "max_pressure_Pa": "65485976.41",
                "fracture_initiation_time_s": "660",
                "first_sink_positive_time_s": "660",
                "sink_delay_s": "0",
                "final_pressure_Pa": "65485976.41",
                "materialized_case_path": "generated/cgeom_100_same_step.yaml",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_metadata(path, failed=False):
    actions = [
        {"scenario_id": "cgeom_075_next_step", "materialized_case_path": "generated/cgeom_075.yaml"},
        {"scenario_id": "cgeom_100_next_step", "materialized_case_path": "generated/cgeom_100.yaml"},
    ]
    if failed:
        actions[0]["status"] = "failed"
    path.write_text(
        json.dumps(
            {
                "matrix_id": "buz67d_modern_refined_cgeom_sensitivity_v2",
                "schema_version": 2,
                "scenario_count": 4,
                "actions": actions,
            }
        ),
        encoding="utf-8",
    )


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        verifier.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "summary" in capsys.readouterr().out


def test_summary_v2_valid(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    payload = verifier.verify(summary, metadata)

    assert payload["classification"] == "PHASE11_3A_V2_SENSITIVITY_RUN_OK"
    assert payload["v1_v2_classification"] == "V2_REPRODUCES_V1_DIAGNOSTICS"


def test_metadata_with_materialized_case_path(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    payload = verifier.verify(summary, metadata)

    assert payload["materialized_case_paths_present"] is True


def test_cgeom_075_and_baseline_present(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    payload = verifier.verify(summary, metadata)

    scenario_ids = {item["scenario_id"] for item in payload["comparisons"]}
    assert "cgeom_075_next_step" in scenario_ids
    assert "cgeom_100_next_step" in scenario_ids


def test_failed_scenario_classifies_failed(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata, failed=True)

    payload = verifier.verify(summary, metadata)

    assert payload["classification"] == "PHASE11_3A_V2_SENSITIVITY_RUN_FAILED"


def test_partial_when_same_step_missing(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary, partial=True)
    write_metadata(metadata)

    payload = verifier.verify(summary, metadata)

    assert payload["classification"] == "PHASE11_3A_V2_SENSITIVITY_RUN_PARTIAL"
