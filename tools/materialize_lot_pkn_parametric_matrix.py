#!/usr/bin/env python3
"""Materialize LOT/PKN parametric matrix v2 scenarios into derived YAML cases."""

from __future__ import annotations

import argparse
import copy
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Any

import yaml


SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class MaterializedScenario:
    scenario_id: str
    output_case: str | None
    overrides: dict[str, Any]
    overwrite_status: str
    status: str


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def resolve_path(anchor: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return anchor.parent / path


def ensure_safe_output_dir(output_dir: Path, allow_versioned_output: bool) -> None:
    parts = [part.lower() for part in output_dir.resolve().parts]
    if "cases" in parts and not allow_versioned_output:
        raise ValueError("output inside cases/ requires --allow-versioned-output")


def safe_filename(template: str, scenario_id: str) -> str:
    filename = template.format(scenario_id=scenario_id)
    path = Path(filename)
    if path.name != filename or ".." in path.parts:
        raise ValueError(f"unsafe materialized filename: {filename}")
    if not SAFE_FILENAME.match(filename):
        raise ValueError(f"unsafe materialized filename: {filename}")
    return filename


def set_path(target: dict, dotted_path: str, value: Any, allow_create: bool) -> None:
    if not dotted_path or ".." in dotted_path:
        raise ValueError(f"invalid override path: {dotted_path}")
    current: Any = target
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        if not isinstance(current, dict):
            raise ValueError(f"override path crosses non-mapping node: {dotted_path}")
        if part not in current:
            if allow_create:
                current[part] = {}
            else:
                raise KeyError(f"override path does not exist: {dotted_path}")
        current = current[part]
    leaf = parts[-1]
    if not isinstance(current, dict):
        raise ValueError(f"override path parent is not a mapping: {dotted_path}")
    if leaf not in current and not allow_create:
        raise KeyError(f"override path does not exist: {dotted_path}")
    current[leaf] = value


def matrix_version(matrix: dict) -> int:
    try:
        return int(matrix.get("schema_version", 1))
    except (TypeError, ValueError):
        return -1


def materialize(args: argparse.Namespace) -> dict:
    matrix_path: Path = args.matrix
    matrix = load_yaml(matrix_path)
    if matrix_version(matrix) != 2:
        raise ValueError("materializer requires matrix schema_version: 2")
    scenarios = matrix.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("matrix scenarios must be a non-empty list")
    base_case = matrix.get("base_case")
    if not base_case:
        raise ValueError("matrix base_case is required")
    base_case_path = resolve_path(matrix_path, str(base_case))
    base_data = load_yaml(base_case_path)

    ensure_safe_output_dir(args.output_dir, args.allow_versioned_output)
    materialization = matrix.get("materialization") or {}
    filename_template = materialization.get("filename_template", "{scenario_id}.yaml")
    output_dir = args.output_dir

    derived: list[MaterializedScenario] = []
    for scenario in scenarios:
        scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
        if not scenario_id:
            raise ValueError("each scenario requires id")
        scenario_id = str(scenario_id)
        overrides = scenario.get("overrides")
        if not isinstance(overrides, dict) or not overrides:
            raise ValueError(f"scenario {scenario_id} requires non-empty overrides")
        case_data = copy.deepcopy(base_data)
        for path, value in overrides.items():
            set_path(case_data, str(path), value, allow_create=args.allow_create)
        metadata = case_data.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata["scenario_id"] = scenario_id
            metadata["materialized_from"] = str(matrix_path)
            metadata["base_case"] = str(base_case_path)
        filename = safe_filename(str(filename_template), scenario_id)
        output_case = output_dir / filename
        overwrite_status = "would_write"
        if output_case.exists():
            if not args.force:
                raise FileExistsError(f"refusing to overwrite existing case: {output_case}")
            overwrite_status = "overwritten"
        elif not args.dry_run:
            overwrite_status = "created"
        if not args.dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_case.write_text(yaml.safe_dump(case_data, sort_keys=False), encoding="utf-8")
        derived.append(
            MaterializedScenario(
                scenario_id=scenario_id,
                output_case=str(output_case),
                overrides=dict(overrides),
                overwrite_status=overwrite_status,
                status="DRY_RUN" if args.dry_run else "MATERIALIZED",
            )
        )

    manifest = {
        "matrix": str(matrix_path),
        "matrix_id": matrix.get("matrix_id"),
        "schema_version": 2,
        "base_case": str(base_case_path),
        "output_dir": str(output_dir),
        "dry_run": args.dry_run,
        "allow_create": args.allow_create,
        "scenario_count": len(derived),
        "scenarios": [asdict(item) for item in derived],
        "status": "PARAMETRIC_CASE_MATERIALIZER_ADDED",
    }
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / args.manifest_name).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-create", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-versioned-output", action="store_true")
    parser.add_argument("--validate-with-lot-sim", dest="lot_sim", help="Reserved hook for explicit validation after materialization.")
    parser.add_argument("--manifest-name", default="materialization_manifest.json")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = materialize(args)
    print(f"MATRIX_ID={manifest['matrix_id']}")
    print(f"SCENARIO_COUNT={manifest['scenario_count']}")
    print(f"DRY_RUN={str(manifest['dry_run']).lower()}")
    print(f"STATUS={manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
