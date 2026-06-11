from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools import verify_lot_pkn_study_results as verifier


FIXTURE_ROOT = Path("tests/fixtures/comparison")


def args_for(result_dir: Path, **kwargs):
    defaults = {
        "result_dir": result_dir,
        "manifest": "study_manifest.json",
        "json": False,
        "output_json": None,
        "output_md": None,
        "allow_dry_run": False,
        "require_report": False,
        "strict": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_help() -> None:
    help_text = verifier.build_parser().format_help()

    assert "--result-dir" in help_text
    assert "--allow-dry-run" in help_text


def test_manifest_complete_ok() -> None:
    report = verifier.verify(args_for(FIXTURE_ROOT / "study_results_ok", require_report=True))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_OK"
    assert report["study_id"] == "fixture_study"
    assert report["errors"] == []


def test_dry_run_without_allow_is_partial() -> None:
    report = verifier.verify(args_for(FIXTURE_ROOT / "study_results_dry_run"))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_PARTIAL"
    assert report["errors"]


def test_dry_run_with_allow_is_ok() -> None:
    report = verifier.verify(args_for(FIXTURE_ROOT / "study_results_dry_run", allow_dry_run=True))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_DRY_RUN_OK"
    assert report["errors"] == []


def test_summary_absent_is_reported() -> None:
    report = verifier.verify(args_for(FIXTURE_ROOT / "study_results_missing_outputs"))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_MISSING_OUTPUTS"
    assert any("summary_csv" in item for item in report["errors"])


def test_metadata_absent_is_reported(tmp_path: Path) -> None:
    source = FIXTURE_ROOT / "study_results_ok"
    target = tmp_path / "missing_metadata"
    target.mkdir()
    for name in ["study_manifest.json", "summary.csv", "run_commands.txt"]:
        (target / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")

    report = verifier.verify(args_for(target))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_MISSING_OUTPUTS"
    assert any("metadata_json" in item for item in report["errors"])


def test_report_absent_with_require_report_is_reported(tmp_path: Path) -> None:
    source = FIXTURE_ROOT / "study_results_ok"
    target = tmp_path / "missing_report"
    target.mkdir()
    for name in ["study_manifest.json", "summary.csv", "metadata.json", "run_commands.txt"]:
        (target / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")

    report = verifier.verify(args_for(target, require_report=True))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_MISSING_OUTPUTS"
    assert any("report_json" in item for item in report["errors"])


def test_schema_version_invalid(tmp_path: Path) -> None:
    target = tmp_path / "bad_schema"
    target.mkdir()
    manifest = json.loads((FIXTURE_ROOT / "study_results_ok" / "study_manifest.json").read_text(encoding="utf-8"))
    manifest["schema_version"] = 99
    (target / "study_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = verifier.verify(args_for(target))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_INVALID_MANIFEST"


def test_failed_scenario_is_failed_in_strict_mode() -> None:
    report = verifier.verify(args_for(FIXTURE_ROOT / "study_results_failed_scenario", strict=True))

    assert report["classification"] == "LOT_PKN_STUDY_RESULTS_FAILED"


def test_output_json_and_markdown_are_written(tmp_path: Path) -> None:
    output_json = tmp_path / "verification.json"
    output_md = tmp_path / "verification.md"
    exit_code = verifier.main(
        [
            "--result-dir",
            str(FIXTURE_ROOT / "study_results_ok"),
            "--require-report",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )

    assert exit_code == 0
    assert json.loads(output_json.read_text(encoding="utf-8"))["classification"] == "LOT_PKN_STUDY_RESULTS_OK"
    assert "LOT/PKN study results verification" in output_md.read_text(encoding="utf-8")
