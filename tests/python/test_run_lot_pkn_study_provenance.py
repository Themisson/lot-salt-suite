from __future__ import annotations

import json
from pathlib import Path

from tools import run_lot_pkn_study as study


FIXTURE_INDEX = Path("tests/fixtures/comparison/study_runner_index_fixture.yaml")


def parse_args(items: list[str]):
    return study.build_parser().parse_args(items)


def run_dry_manifest(tmp_path: Path, extra: list[str] | None = None) -> dict:
    output_dir = tmp_path / "study"
    args = [
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
    if extra:
        args.extend(extra)
    study.execute(parse_args(args))
    return json.loads((output_dir / "study_manifest.json").read_text(encoding="utf-8"))


def test_help_still_mentions_study_id() -> None:
    help_text = study.build_parser().format_help()

    assert "--study-id" in help_text
    assert "--output-dir" in help_text


def test_dry_run_manifest_has_schema_version(tmp_path: Path) -> None:
    manifest = run_dry_manifest(tmp_path)

    assert manifest["schema_version"] == 1
    assert manifest["study_status"] == "dry_run"
    assert manifest["study_id"] == "fixture_active"


def test_manifest_records_matrix_and_base_case(tmp_path: Path) -> None:
    manifest = run_dry_manifest(tmp_path)

    assert manifest["matrix_path"].endswith("fixture_matrix.yaml")
    assert manifest["matrix_id"] == "fixture_matrix"
    assert manifest["matrix_schema_version"] == 1
    assert manifest["base_case"] is None


def test_manifest_records_environment_git_and_lot_sim(tmp_path: Path) -> None:
    manifest = run_dry_manifest(tmp_path)

    assert manifest["environment"]["python_version"]
    assert manifest["environment"]["platform"]
    assert "available" in manifest["git"]
    assert manifest["lot_sim"]["path"] == "custom-lot-sim"
    assert manifest["lot_sim"]["exists"] is False


def test_manifest_records_outputs_and_run_commands(tmp_path: Path) -> None:
    output_dir = tmp_path / "study"
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
            ]
        )
    )
    manifest = json.loads((output_dir / "study_manifest.json").read_text(encoding="utf-8"))
    commands = (output_dir / "run_commands.txt").read_text(encoding="utf-8")

    assert manifest["outputs"]["run_commands_txt"].endswith("run_commands.txt")
    assert manifest["outputs"]["summary_csv"].endswith("summary.csv")
    assert "tools/verify_lot_pkn_study_results.py" in commands


def test_manifest_records_scenarios_in_dry_run(tmp_path: Path) -> None:
    manifest = run_dry_manifest(tmp_path)

    assert manifest["scenarios"]
    assert manifest["scenarios"][0]["id"] == "cgeom_100"
    assert manifest["scenarios"][0]["status"] == "dry_run"


def test_manifest_does_not_fail_without_git(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(study, "git_value", lambda _args: None)

    manifest = run_dry_manifest(tmp_path)

    assert manifest["git"]["available"] is False
    assert "Git metadata was not available." in manifest["caveats"]
