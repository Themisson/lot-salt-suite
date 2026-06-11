#!/usr/bin/env python3
"""Validate LOT/PKN sensitivity matrix YAML files.

The validator accepts the existing v1 format based on scenario.case and the
Stage 11 v2 format based on base_case plus scenario.overrides.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


VALID_STATUSES = {
    "MATRIX_V1_VALID",
    "MATRIX_V2_VALID",
    "MATRIX_INVALID",
    "MATRIX_UNSUPPORTED_VERSION",
    "MATRIX_MISSING_BASE_CASE",
    "MATRIX_MISSING_SCENARIO_CASE",
    "MATRIX_DUPLICATE_SCENARIO_ID",
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("matrix YAML root must be a mapping")
    return data


def resolve_path(matrix_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return matrix_path.parent / path


def schema_version(data: dict) -> int:
    raw = data.get("schema_version", 1)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return -1


def validate_ids(scenarios: list[dict]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, scenario in enumerate(scenarios):
        scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
        if not scenario_id:
            issues.append(ValidationIssue("MATRIX_INVALID", f"scenario at index {index} is missing id"))
            continue
        scenario_id = str(scenario_id)
        if scenario_id in seen:
            issues.append(ValidationIssue("MATRIX_DUPLICATE_SCENARIO_ID", f"duplicate scenario id: {scenario_id}"))
        seen.add(scenario_id)
    return issues


def validate_metadata(scenarios: list[dict], strict: bool) -> list[ValidationIssue]:
    if not strict:
        return []
    issues: list[ValidationIssue] = []
    for scenario in scenarios:
        metadata = scenario.get("metadata", {})
        if metadata is not None and not isinstance(metadata, dict):
            issues.append(ValidationIssue("MATRIX_INVALID", f"scenario {scenario.get('id')} metadata must be a mapping"))
    return issues


def validate_v1(matrix_path: Path, data: dict, strict: bool) -> tuple[str, list[ValidationIssue]]:
    scenarios = data.get("scenarios")
    issues: list[ValidationIssue] = []
    if not data.get("matrix_id"):
        issues.append(ValidationIssue("MATRIX_INVALID", "matrix_id is required"))
    if not isinstance(scenarios, list) or not scenarios:
        issues.append(ValidationIssue("MATRIX_INVALID", "scenarios must be a non-empty list"))
        return "MATRIX_INVALID", issues
    issues.extend(validate_ids(scenarios))
    issues.extend(validate_metadata(scenarios, strict))
    for scenario in scenarios:
        case = scenario.get("case")
        if not case:
            issues.append(ValidationIssue("MATRIX_MISSING_SCENARIO_CASE", f"scenario {scenario.get('id')} is missing case"))
            continue
        if strict and not resolve_path(matrix_path, str(case)).exists():
            issues.append(ValidationIssue("MATRIX_MISSING_SCENARIO_CASE", f"scenario case does not exist: {case}"))
    status = first_error_status(issues) if issues else "MATRIX_V1_VALID"
    return status, issues


def validate_v2(matrix_path: Path, data: dict, strict: bool) -> tuple[str, list[ValidationIssue]]:
    scenarios = data.get("scenarios")
    issues: list[ValidationIssue] = []
    if not data.get("matrix_id"):
        issues.append(ValidationIssue("MATRIX_INVALID", "matrix_id is required"))
    base_case = data.get("base_case")
    if not base_case:
        issues.append(ValidationIssue("MATRIX_MISSING_BASE_CASE", "base_case is required for schema_version 2"))
    elif not resolve_path(matrix_path, str(base_case)).exists():
        issues.append(ValidationIssue("MATRIX_MISSING_BASE_CASE", f"base_case does not exist: {base_case}"))
    if not isinstance(scenarios, list) or not scenarios:
        issues.append(ValidationIssue("MATRIX_INVALID", "scenarios must be a non-empty list"))
        return first_error_status(issues), issues
    issues.extend(validate_ids(scenarios))
    issues.extend(validate_metadata(scenarios, strict))
    for scenario in scenarios:
        overrides = scenario.get("overrides")
        if not isinstance(overrides, dict) or not overrides:
            issues.append(ValidationIssue("MATRIX_INVALID", f"scenario {scenario.get('id')} requires non-empty overrides"))
        if "case" in scenario and strict:
            issues.append(ValidationIssue("MATRIX_INVALID", f"scenario {scenario.get('id')} must not mix case with v2 overrides"))
    status = first_error_status(issues) if issues else "MATRIX_V2_VALID"
    return status, issues


def first_error_status(issues: list[ValidationIssue]) -> str:
    priority = [
        "MATRIX_UNSUPPORTED_VERSION",
        "MATRIX_MISSING_BASE_CASE",
        "MATRIX_MISSING_SCENARIO_CASE",
        "MATRIX_DUPLICATE_SCENARIO_ID",
        "MATRIX_INVALID",
    ]
    codes = {issue.code for issue in issues}
    for code in priority:
        if code in codes:
            return code
    return "MATRIX_INVALID"


def validate_matrix(matrix_path: Path, strict: bool = False) -> dict:
    data = load_yaml(matrix_path)
    version = schema_version(data)
    if version == 1:
        status, issues = validate_v1(matrix_path, data, strict)
    elif version == 2:
        status, issues = validate_v2(matrix_path, data, strict)
    else:
        status = "MATRIX_UNSUPPORTED_VERSION"
        issues = [ValidationIssue(status, f"unsupported schema_version: {data.get('schema_version')}")]
    assert status in VALID_STATUSES
    scenarios = data.get("scenarios") or []
    return {
        "matrix": str(matrix_path),
        "matrix_id": data.get("matrix_id"),
        "schema_version": version,
        "scenario_count": len(scenarios) if isinstance(scenarios, list) else 0,
        "status": status,
        "valid": status in {"MATRIX_V1_VALID", "MATRIX_V2_VALID"},
        "issues": [issue.__dict__ for issue in issues],
    }


def print_text(payload: dict) -> None:
    print(f"MATRIX_ID={payload['matrix_id']}")
    print(f"SCHEMA_VERSION={payload['schema_version']}")
    print(f"SCENARIO_COUNT={payload['scenario_count']}")
    print(f"STATUS={payload['status']}")
    for issue in payload["issues"]:
        print(f"ISSUE={issue['code']}: {issue['message']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="Emit JSON payload.")
    parser.add_argument("--strict", action="store_true", help="Enable extra structural checks.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = validate_matrix(args.matrix, strict=args.strict)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
