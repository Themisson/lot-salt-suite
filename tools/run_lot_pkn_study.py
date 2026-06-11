#!/usr/bin/env python3
"""Run a complete LOT/PKN sensitivity study by study_id."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import report_lot_pkn_sensitivity_matrix as reporter
from tools import run_lot_pkn_sensitivity_study as study_runner


DEFAULT_STUDIES_INDEX = Path("cases/validation/sensitivity/studies_index.yaml")


def git_value(args: list[str]) -> str | None:
    try:
        result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    except Exception:
        return None
    value = result.stdout.strip()
    return value or None


def build_study_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "tools/run_lot_pkn_sensitivity_study.py",
        "--study-id",
        args.study_id,
        "--studies-index",
        str(args.studies_index),
        "--output-dir",
        str(args.output_dir),
        "--lot-sim",
        args.lot_sim,
    ]
    if args.dry_run:
        command.append("--dry-run")
    if args.skip_run:
        command.append("--skip-run")
    if args.only_summary:
        command.append("--only-summary")
    if args.allow_inactive:
        command.append("--allow-inactive")
    return command


def build_report_command(summary_path: Path, metadata_path: Path, report_json: Path, report_md: Path) -> list[str]:
    return [
        sys.executable,
        "tools/report_lot_pkn_sensitivity_matrix.py",
        "--summary",
        str(summary_path),
        "--metadata",
        str(metadata_path),
        "--output-json",
        str(report_json),
        "--output-md",
        str(report_md),
    ]


def write_commands(path: Path, commands: list[list[str]]) -> None:
    lines = [" ".join(command) for command in commands]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execute(args: argparse.Namespace) -> dict:
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    study_args = argparse.Namespace(
        study_id=args.study_id,
        studies_index=args.studies_index,
        output_dir=output_dir,
        dry_run=args.dry_run,
        skip_run=args.skip_run,
        only_summary=args.only_summary,
        lot_sim=args.lot_sim,
        allow_inactive=args.allow_inactive,
    )
    study_payload = study_runner.execute(study_args)
    runner_metadata = study_payload["runner_metadata"]

    summary_path = output_dir / "summary.csv"
    metadata_path = output_dir / "metadata.json"
    report_json = output_dir / "sensitivity_report.json"
    report_md = output_dir / "sensitivity_report.md"
    report_payload: dict | None = None
    report_status = "SKIPPED_BY_DRY_RUN" if args.dry_run else "SKIPPED"
    report_command = build_report_command(summary_path, metadata_path, report_json, report_md)

    if not args.skip_report and not args.dry_run:
        report_payload = reporter.summarize(summary_path, metadata_path)
        report_json.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        reporter.write_markdown(report_md, report_payload)
        report_status = "GENERATED"
    elif args.skip_report:
        report_status = "SKIPPED_BY_USER"

    commands = [build_study_command(args)]
    if not args.skip_report:
        commands.append(report_command)

    manifest = {
        "study_id": args.study_id,
        "matrix_path": study_payload["matrix_path"],
        "matrix_schema_version": runner_metadata.get("schema_version"),
        "output_dir": str(output_dir),
        "summary_path": str(summary_path),
        "metadata_path": str(metadata_path),
        "report_json_path": str(report_json) if not args.skip_report else None,
        "report_md_path": str(report_md) if not args.skip_report else None,
        "commands": commands,
        "status": "CANONICAL_LOT_PKN_STUDY_COMMAND_ADDED",
        "dry_run": bool(args.dry_run),
        "skip_run": bool(args.skip_run),
        "only_summary": bool(args.only_summary),
        "skip_report": bool(args.skip_report),
        "report_status": report_status,
        "study_metadata_path": study_payload["study_metadata"],
        "runner_status": runner_metadata.get("status"),
        "report_classification": report_payload.get("classification") if report_payload else None,
        "git_commit": git_value(["rev-parse", "--short", "HEAD"]),
        "git_branch": git_value(["branch", "--show-current"]),
    }
    write_manifest(output_dir / "study_manifest.json", manifest)
    write_commands(output_dir / "run_commands.txt", commands)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--studies-index", type=Path, default=DEFAULT_STUDIES_INDEX)
    parser.add_argument("--lot-sim", default=study_runner.matrix_runner.default_lot_sim())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--only-summary", action="store_true")
    parser.add_argument("--skip-report", action="store_true")
    parser.add_argument("--allow-inactive", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = execute(args)
    print(f"STUDY_ID={manifest['study_id']}")
    print(f"MANIFEST={Path(manifest['output_dir']) / 'study_manifest.json'}")
    print(f"STATUS={manifest['status']}")
    print(f"REPORT_STATUS={manifest['report_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
