import csv
import json

import pytest

from tools import verify_phase10_30b_sensitivity_run as verifier


def write_summary(path, scenario_ids=None):
    scenario_ids = scenario_ids or sorted(verifier.REQUIRED_SCENARIOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted(verifier.ESSENTIAL_COLUMNS))
        writer.writeheader()
        for scenario_id in scenario_ids:
            writer.writerow(
                {
                    "scenario_id": scenario_id,
                    "case": f"{scenario_id}.yaml",
                    "timeseries_csv": f"{scenario_id}/timeseries.csv",
                    "max_pressure_Pa": "1.0",
                    "fracture_initiation_time_s": "510",
                    "first_sink_positive_time_s": "540",
                    "sink_delay_s": "30",
                    "final_pressure_Pa": "1.0",
                }
            )


def write_metadata(path, scenario_count=10, matrix_id="buz67d_modern_refined_cgeom_sensitivity", failed=False):
    path.write_text(
        json.dumps(
            {
                "matrix_id": matrix_id,
                "scenario_count": scenario_count,
                "actions": [{"scenario_id": "cgeom_075_next_step", "status": "failed"}] if failed else [],
            }
        ),
        encoding="utf-8",
    )


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        verifier.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "summary" in capsys.readouterr().out


def test_complete_summary_is_ok(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata)

    result = verifier.verify(summary, metadata)

    assert result["classification"] == "VERSIONED_SENSITIVITY_RUN_OK"
    assert result["baseline_present"] is True
    assert result["cgeom_075_present"] is True
    assert result["same_step_present"] is True


def test_partial_summary_is_classified(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary, ["cgeom_075_next_step", "cgeom_100_next_step"])
    write_metadata(metadata, scenario_count=10)

    result = verifier.verify(summary, metadata)

    assert result["classification"] == "VERSIONED_SENSITIVITY_RUN_PARTIAL"
    assert result["required_scenarios_present"] is False


def test_metadata_without_matrix_id_is_rejected(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata, matrix_id="")

    with pytest.raises(ValueError, match="matrix_id"):
        verifier.verify(summary, metadata)


def test_failed_action_is_failed(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    write_summary(summary)
    write_metadata(metadata, failed=True)

    result = verifier.verify(summary, metadata)

    assert result["classification"] == "VERSIONED_SENSITIVITY_RUN_FAILED"


def test_missing_essential_column_is_rejected(tmp_path):
    summary = tmp_path / "summary.csv"
    metadata = tmp_path / "metadata.json"
    summary.write_text("scenario_id\ncgeom_075_next_step\n", encoding="utf-8")
    write_metadata(metadata)

    with pytest.raises(ValueError, match="missing required columns"):
        verifier.verify(summary, metadata)
