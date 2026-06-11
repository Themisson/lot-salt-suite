from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import run_lot_pkn_sensitivity_study as study_runner


FIXTURE_INDEX = Path("tests/fixtures/comparison/study_runner_index_fixture.yaml")


def test_help() -> None:
    help_text = study_runner.build_parser().format_help()
    assert "--study-id" in help_text
    assert "--allow-inactive" in help_text


def test_valid_study_dry_run_writes_metadata(tmp_path: Path) -> None:
    output_dir = tmp_path / "study"
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "fixture_active",
            "--studies-index",
            str(FIXTURE_INDEX),
            "--output-dir",
            str(output_dir),
            "--dry-run",
            "--lot-sim",
            "fixture-lot-sim",
        ]
    )
    payload = study_runner.execute(args)
    metadata = json.loads((output_dir / "study_metadata.json").read_text(encoding="utf-8"))
    runner_metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))

    assert payload["status"] == "SENSITIVITY_STUDY_ID_EXECUTION_ADDED"
    assert metadata["study_id"] == "fixture_active"
    assert metadata["dry_run"] is True
    assert metadata["runner_metadata"]["dry_run"] is True
    assert runner_metadata["matrix_id"] == "fixture_matrix"
    assert "fixture-lot-sim" in metadata["runner_invocation"]


def test_missing_study_id_is_rejected(tmp_path: Path) -> None:
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "does_not_exist",
            "--studies-index",
            str(FIXTURE_INDEX),
            "--output-dir",
            str(tmp_path),
            "--dry-run",
        ]
    )
    with pytest.raises(ValueError, match="study_id not found"):
        study_runner.execute(args)


def test_missing_studies_index_is_rejected(tmp_path: Path) -> None:
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "fixture_active",
            "--studies-index",
            str(tmp_path / "missing.yaml"),
            "--output-dir",
            str(tmp_path),
            "--dry-run",
        ]
    )
    with pytest.raises(FileNotFoundError):
        study_runner.execute(args)


def test_missing_matrix_is_rejected(tmp_path: Path) -> None:
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "fixture_missing_matrix",
            "--studies-index",
            str(FIXTURE_INDEX),
            "--output-dir",
            str(tmp_path),
            "--dry-run",
        ]
    )
    with pytest.raises(FileNotFoundError):
        study_runner.execute(args)


def test_inactive_study_is_blocked_by_default(tmp_path: Path) -> None:
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "fixture_inactive",
            "--studies-index",
            str(FIXTURE_INDEX),
            "--output-dir",
            str(tmp_path),
            "--dry-run",
        ]
    )
    with pytest.raises(ValueError, match="allow-inactive"):
        study_runner.execute(args)


def test_allow_inactive_runs_fixture(tmp_path: Path) -> None:
    output_dir = tmp_path / "inactive"
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "fixture_inactive",
            "--studies-index",
            str(FIXTURE_INDEX),
            "--output-dir",
            str(output_dir),
            "--dry-run",
            "--allow-inactive",
        ]
    )
    payload = study_runner.execute(args)
    metadata = json.loads((output_dir / "study_metadata.json").read_text(encoding="utf-8"))

    assert payload["status"] == "SENSITIVITY_STUDY_ID_EXECUTION_ADDED"
    assert metadata["status"] == "inactive"
    assert metadata["allow_inactive"] is True


def test_dry_run_is_forwarded_to_runner(tmp_path: Path) -> None:
    args = study_runner.build_parser().parse_args(
        [
            "--study-id",
            "fixture_active",
            "--studies-index",
            str(FIXTURE_INDEX),
            "--output-dir",
            str(tmp_path),
            "--dry-run",
        ]
    )
    payload = study_runner.execute(args)
    assert payload["runner_metadata"]["dry_run"] is True
    assert payload["runner_metadata"]["actions"][0]["scenario_id"] == "cgeom_100"
