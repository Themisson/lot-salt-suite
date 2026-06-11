#!/usr/bin/env python3
"""Run a complete LOT/PKN sensitivity study by study_id."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
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


def git_info() -> dict:
    commit = git_value(["rev-parse", "--short", "HEAD"])
    branch = git_value(["branch", "--show-current"])
    dirty_text = git_value(["status", "--porcelain"])
    available = commit is not None or branch is not None or dirty_text is not None
    caveats = []
    if not available:
        caveats.append("Git metadata was not available.")
    return {
        "available": available,
        "commit": commit,
        "branch": branch,
        "is_dirty": None if dirty_text is None else bool(dirty_text),
        "caveats": caveats,
    }


def environment_info() -> dict:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "cwd": str(Path.cwd()),
    }


def lot_sim_info(path: str) -> dict:
    candidate = Path(path)
    resolved = candidate if candidate.is_absolute() else Path.cwd() / candidate
    return {
        "path": path,
        "resolved_path": str(resolved),
        "exists": resolved.exists(),
    }


def command_text(command: list[str]) -> str:
    return " ".join(command)


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


def build_canonical_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "tools/run_lot_pkn_study.py",
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
    if args.skip_report:
        command.append("--skip-report")
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


def build_verify_command(output_dir: Path) -> list[str]:
    return [
        sys.executable,
        "tools/verify_lot_pkn_study_results.py",
        "--result-dir",
        str(output_dir),
    ]


def write_commands(path: Path, commands: list[list[str]]) -> None:
    labels = ["canonical study runner", "study runner", "sensitivity runner", "reporter", "future verifier"]
    lines = [f"# {label}\n{command_text(command)}" for label, command in zip(labels, commands)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_summary_status(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {row.get("scenario_id", ""): "completed" for row in csv.DictReader(handle) if row.get("scenario_id")}


def collect_scenarios(runner_metadata: dict, summary_path: Path, dry_run: bool) -> list[dict]:
    summary_status = read_summary_status(summary_path)
    scenarios = []
    for action in runner_metadata.get("actions") or []:
        scenario_id = str(action.get("scenario_id", ""))
        if not scenario_id:
            continue
        status = summary_status.get(scenario_id)
        if status is None:
            status = "dry_run" if dry_run else "planned"
        scenarios.append(
            {
                "id": scenario_id,
                "status": status,
                "case_path": action.get("run", [None, None, None, None])[3] if len(action.get("run", [])) > 3 else None,
                "materialized_case_path": action.get("materialized_case_path"),
                "metadata": action.get("metadata") or {},
            }
        )
    return scenarios


def matrix_details(matrix_path: Path) -> dict:
    spec = study_runner.matrix_runner.load_matrix(matrix_path)
    return {
        "matrix_id": spec.matrix_id,
        "matrix_schema_version": spec.schema_version,
        "base_case": spec.base_case,
    }


def study_status(args: argparse.Namespace, summary_path: Path) -> str:
    if args.dry_run:
        return "dry_run"
    if args.skip_run or args.only_summary:
        return "partial"
    return "completed" if summary_path.exists() else "partial"


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
    canonical_command = build_canonical_command(args)
    study_command = build_study_command(args)
    verify_command = build_verify_command(output_dir)

    if not args.skip_report and not args.dry_run:
        report_payload = reporter.summarize(summary_path, metadata_path)
        report_json.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        reporter.write_markdown(report_md, report_payload)
        report_status = "GENERATED"
    elif args.skip_report:
        report_status = "SKIPPED_BY_USER"

    study_metadata = read_json_if_exists(Path(study_payload["study_metadata"]))
    sensitivity_command = study_metadata.get("runner_invocation") or []

    commands = [canonical_command, study_command]
    if sensitivity_command:
        commands.append(sensitivity_command)
    if not args.skip_report:
        commands.append(report_command)
    commands.append(verify_command)

    matrix_info = matrix_details(Path(study_payload["matrix_path"]))
    outputs = {
        "summary_csv": str(summary_path),
        "metadata_json": str(metadata_path),
        "report_json": str(report_json) if not args.skip_report else None,
        "report_md": str(report_md) if not args.skip_report else None,
        "run_commands_txt": str(output_dir / "run_commands.txt"),
    }
    git = git_info()
    caveats = list(git.get("caveats") or [])
    if args.dry_run:
        caveats.append("Dry-run manifest records planned outputs; simulation outputs are not expected.")
    if args.skip_report:
        caveats.append("Report generation was skipped by user request.")

    manifest = {
        "schema_version": 1,
        "study_id": args.study_id,
        "study_status": study_status(args, summary_path),
        "matrix_path": study_payload["matrix_path"],
        "matrix_id": matrix_info["matrix_id"],
        "matrix_schema_version": matrix_info["matrix_schema_version"],
        "base_case": matrix_info["base_case"],
        "studies_index": str(args.studies_index),
        "output_dir": str(output_dir),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command_text(canonical_command),
        "commands": {
            "study_runner": command_text(study_command),
            "sensitivity_runner": command_text(sensitivity_command) if sensitivity_command else None,
            "reporter": command_text(report_command) if not args.skip_report else None,
            "verifier": command_text(verify_command),
        },
        "environment": environment_info(),
        "git": git,
        "lot_sim": lot_sim_info(args.lot_sim),
        "outputs": outputs,
        "scenarios": collect_scenarios(runner_metadata, summary_path, args.dry_run),
        "caveats": caveats,
        "status": "CANONICAL_LOT_PKN_STUDY_COMMAND_ADDED",
        "dry_run": bool(args.dry_run),
        "skip_run": bool(args.skip_run),
        "only_summary": bool(args.only_summary),
        "skip_report": bool(args.skip_report),
        "report_status": report_status,
        "study_metadata_path": study_payload["study_metadata"],
        "runner_status": runner_metadata.get("status"),
        "report_classification": report_payload.get("classification") if report_payload else None,
        "summary_path": str(summary_path),
        "metadata_path": str(metadata_path),
        "report_json_path": str(report_json) if not args.skip_report else None,
        "report_md_path": str(report_md) if not args.skip_report else None,
        "git_commit": git.get("commit"),
        "git_branch": git.get("branch"),
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
