#!/usr/bin/env python3
"""Run a LOT/PKN sensitivity study registered in studies_index.yaml."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import run_lot_pkn_sensitivity_matrix as matrix_runner


DEFAULT_STUDIES_INDEX = Path("cases/validation/sensitivity/studies_index.yaml")


def load_index(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    studies = data.get("studies")
    if not isinstance(studies, list) or not studies:
        raise ValueError("studies_index must contain a non-empty studies list")
    return data


def find_study(index_path: Path, study_id: str) -> dict:
    data = load_index(index_path)
    for study in data["studies"]:
        if str(study.get("id")) == study_id:
            return study
    raise ValueError(f"study_id not found: {study_id}")


def resolve_matrix_path(index_path: Path, matrix: str) -> Path:
    matrix_path = Path(matrix)
    if matrix_path.is_absolute():
        return matrix_path
    cwd_path = Path.cwd() / matrix_path
    if cwd_path.exists():
        return cwd_path
    return index_path.parent / matrix_path


def build_runner_invocation(args: argparse.Namespace, matrix_path: Path) -> list[str]:
    invocation = [
        sys.executable,
        "tools/run_lot_pkn_sensitivity_matrix.py",
        "--matrix",
        str(matrix_path),
        "--output-dir",
        str(args.output_dir),
        "--lot-sim",
        args.lot_sim,
    ]
    if args.dry_run:
        invocation.append("--dry-run")
    if args.skip_run:
        invocation.append("--skip-run")
    if args.only_summary:
        invocation.append("--only-summary")
    return invocation


def write_study_metadata(
    output_dir: Path,
    args: argparse.Namespace,
    study: dict,
    matrix_path: Path,
    runner_invocation: list[str],
    runner_metadata: dict,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "study_id": args.study_id,
        "matrix_path": str(matrix_path),
        "studies_index": str(args.studies_index),
        "status": str(study.get("status", "")),
        "title": str(study.get("title", "")),
        "route": str(study.get("route", "")),
        "tags": list(study.get("tags") or []),
        "command": list(sys.argv),
        "dry_run": bool(args.dry_run),
        "skip_run": bool(args.skip_run),
        "only_summary": bool(args.only_summary),
        "allow_inactive": bool(args.allow_inactive),
        "runner_invocation": runner_invocation,
        "runner_metadata": runner_metadata,
    }
    path = output_dir / "study_metadata.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def execute(args: argparse.Namespace) -> dict:
    study = find_study(args.studies_index, args.study_id)
    status = str(study.get("status", ""))
    if status != "active" and not args.allow_inactive:
        raise ValueError(f"study {args.study_id} has status {status!r}; use --allow-inactive to run it")

    matrix = study.get("matrix")
    if not matrix:
        raise ValueError(f"study {args.study_id} does not declare matrix")
    matrix_path = resolve_matrix_path(args.studies_index, str(matrix))
    if not matrix_path.exists():
        raise FileNotFoundError(matrix_path)

    runner_args = argparse.Namespace(
        matrix=matrix_path,
        output_dir=args.output_dir,
        legacy_csv=None,
        dry_run=args.dry_run,
        skip_run=args.skip_run,
        only_summary=args.only_summary,
        lot_sim=args.lot_sim,
        materialized_dir=None,
        keep_materialized=False,
        force_materialize=False,
    )
    runner_metadata = matrix_runner.execute(runner_args)
    runner_invocation = build_runner_invocation(args, matrix_path)
    study_metadata_path = write_study_metadata(
        args.output_dir,
        args,
        study,
        matrix_path,
        runner_invocation,
        runner_metadata,
    )
    return {
        "study_id": args.study_id,
        "matrix_path": str(matrix_path),
        "study_metadata": str(study_metadata_path),
        "runner_metadata": runner_metadata,
        "status": "SENSITIVITY_STUDY_ID_EXECUTION_ADDED",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--studies-index", type=Path, default=DEFAULT_STUDIES_INDEX)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--only-summary", action="store_true")
    parser.add_argument("--lot-sim", default=matrix_runner.default_lot_sim())
    parser.add_argument("--allow-inactive", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = execute(args)
    print(f"STUDY_ID={payload['study_id']}")
    print(f"MATRIX_PATH={payload['matrix_path']}")
    print(f"STUDY_METADATA={payload['study_metadata']}")
    print(f"STATUS={payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
