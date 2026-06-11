from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import run_lot_pkn_study as study


FIXTURE_INDEX = Path("tests/fixtures/comparison/study_runner_index_fixture.yaml")


def parse_args(items: list[str]):
    return study.build_parser().parse_args(items)


def test_help() -> None:
    help_text = study.build_parser().format_help()
    assert "--study-id" in help_text
    assert "--skip-report" in help_text


def test_dry_run_writes_manifest_and_commands(tmp_path: Path) -> None:
    output_dir = tmp_path / "study"
    manifest = study.execute(
        parse_args(
            [
                "--study-id",
                "fixture_active",
                "--studies-index",
                str(FIXTURE_INDEX),
                "--output-dir",
                str(output_dir),
                "--dry-run",
                "--lot-sim",
                "custom-lot-sim",
            ]
        )
    )
    saved = json.loads((output_dir / "study_manifest.json").read_text(encoding="utf-8"))
    commands = (output_dir / "run_commands.txt").read_text(encoding="utf-8")

    assert manifest["dry_run"] is True
    assert saved["status"] == "CANONICAL_LOT_PKN_STUDY_COMMAND_ADDED"
    assert saved["report_status"] == "SKIPPED_BY_DRY_RUN"
    assert "custom-lot-sim" in commands
    assert "tools/run_lot_pkn_sensitivity_study.py" in commands
    assert "tools/report_lot_pkn_sensitivity_matrix.py" in commands


def test_unknown_study_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="study_id not found"):
        study.execute(
            parse_args(
                [
                    "--study-id",
                    "unknown",
                    "--studies-index",
                    str(FIXTURE_INDEX),
                    "--output-dir",
                    str(tmp_path),
                    "--dry-run",
                ]
            )
        )


def test_manifest_in_dry_run_records_paths(tmp_path: Path) -> None:
    output_dir = tmp_path / "manifest"
    manifest = study.execute(
        parse_args(
            [
                "--study-id",
                "fixture_active",
                "--studies-index",
                str(FIXTURE_INDEX),
                "--output-dir",
                str(output_dir),
                "--dry-run",
            ]
        )
    )

    assert manifest["summary_path"].endswith("summary.csv")
    assert manifest["metadata_path"].endswith("metadata.json")
    assert manifest["report_json_path"].endswith("sensitivity_report.json")
    assert manifest["matrix_schema_version"] == 1


def test_skip_report_omits_report_command(tmp_path: Path) -> None:
    output_dir = tmp_path / "skip_report"
    manifest = study.execute(
        parse_args(
            [
                "--study-id",
                "fixture_active",
                "--studies-index",
                str(FIXTURE_INDEX),
                "--output-dir",
                str(output_dir),
                "--dry-run",
                "--skip-report",
            ]
        )
    )
    commands = (output_dir / "run_commands.txt").read_text(encoding="utf-8")

    assert manifest["skip_report"] is True
    assert manifest["report_status"] == "SKIPPED_BY_USER"
    assert "tools/report_lot_pkn_sensitivity_matrix.py" not in commands


def test_allow_inactive_is_forwarded(tmp_path: Path) -> None:
    manifest = study.execute(
        parse_args(
            [
                "--study-id",
                "fixture_inactive",
                "--studies-index",
                str(FIXTURE_INDEX),
                "--output-dir",
                str(tmp_path),
                "--dry-run",
                "--allow-inactive",
            ]
        )
    )

    assert manifest["dry_run"] is True
    assert manifest["runner_status"] == "GENERIC_LOT_PKN_SENSITIVITY_RUNNER_ADDED"


def test_lot_sim_customized_in_commands(tmp_path: Path) -> None:
    output_dir = tmp_path / "custom"
    study.execute(
        parse_args(
            [
                "--study-id",
                "fixture_active",
                "--studies-index",
                str(FIXTURE_INDEX),
                "--output-dir",
                str(output_dir),
                "--dry-run",
                "--lot-sim",
                "build/Debug/lot-sim.exe",
            ]
        )
    )
    commands = (output_dir / "run_commands.txt").read_text(encoding="utf-8")

    assert "build/Debug/lot-sim.exe" in commands
