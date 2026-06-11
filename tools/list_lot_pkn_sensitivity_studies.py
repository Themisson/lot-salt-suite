#!/usr/bin/env python3
"""List and validate LOT/PKN sensitivity studies."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml


REQUIRED_FIELDS = {"id", "title", "matrix", "route", "status", "tags", "caveat"}


@dataclass(frozen=True)
class Study:
    id: str
    title: str
    matrix: str
    route: str
    status: str
    tags: list[str]
    caveat: str


def load_studies(index_path: Path) -> list[Study]:
    if not index_path.exists():
        raise FileNotFoundError(index_path)
    data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    raw_studies = data.get("studies") or []
    if not isinstance(raw_studies, list) or not raw_studies:
        raise ValueError("studies must be a non-empty list")
    studies = []
    for raw in raw_studies:
        missing = REQUIRED_FIELDS - set(raw)
        if missing:
            raise ValueError(f"study missing required fields: {sorted(missing)}")
        tags = raw["tags"]
        if not isinstance(tags, list) or not tags:
            raise ValueError(f"study {raw['id']} requires non-empty tags")
        studies.append(
            Study(
                id=str(raw["id"]),
                title=str(raw["title"]),
                matrix=str(raw["matrix"]),
                route=str(raw["route"]),
                status=str(raw["status"]),
                tags=[str(tag) for tag in tags],
                caveat=str(raw["caveat"]),
            )
        )
    return studies


def resolve_matrix_path(index_path: Path, matrix: str) -> Path:
    matrix_path = Path(matrix)
    if matrix_path.is_absolute():
        return matrix_path
    cwd_path = Path.cwd() / matrix_path
    if cwd_path.exists():
        return cwd_path
    return index_path.parent / matrix_path


def validate_studies(index_path: Path, studies: list[Study]) -> list[dict]:
    results = []
    for study in studies:
        matrix_path = resolve_matrix_path(index_path, study.matrix)
        exists = matrix_path.exists()
        results.append(
            {
                "id": study.id,
                "matrix": study.matrix,
                "resolved_matrix": str(matrix_path),
                "matrix_exists": exists,
                "status": "OK" if exists else "MISSING_MATRIX",
            }
        )
    return results


def filter_studies(studies: list[Study], tag: str | None = None, status: str | None = None) -> list[Study]:
    filtered = studies
    if tag:
        filtered = [study for study in filtered if tag in study.tags]
    if status:
        filtered = [study for study in filtered if study.status == status]
    return filtered


def build_payload(index_path: Path, tag: str | None = None, status: str | None = None, validate: bool = False) -> dict:
    studies = filter_studies(load_studies(index_path), tag=tag, status=status)
    validation = validate_studies(index_path, studies) if validate else []
    return {
        "index": str(index_path),
        "study_count": len(studies),
        "studies": [asdict(study) for study in studies],
        "validation": validation,
        "validation_status": "OK" if not validate or all(item["matrix_exists"] for item in validation) else "FAILED",
    }


def print_text(payload: dict) -> None:
    print(f"STUDY_COUNT={payload['study_count']}")
    print(f"VALIDATION_STATUS={payload['validation_status']}")
    for study in payload["studies"]:
        print(f"{study['id']}\t{study['status']}\t{study['route']}\t{study['matrix']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of tabular text.")
    parser.add_argument("--tag", help="Filter by tag.")
    parser.add_argument("--status", help="Filter by study status.")
    parser.add_argument("--validate", action="store_true", help="Validate referenced matrix files.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(args.index, tag=args.tag, status=args.status, validate=args.validate)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)
    return 0 if payload["validation_status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
