#!/usr/bin/env python3
"""Validate Phase 11.10Z diagnostic pre-runner fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


EXPECTED_FIXTURES = {
    "diagnostic_disabled_default.yaml": "default_disabled_covered",
    "diagnostic_enabled_pkn_pre_runner.yaml": "pkn_diagnostic_covered",
    "diagnostic_enabled_penny_pre_runner.yaml": "penny_diagnostic_covered",
    "diagnostic_dispatch_true_invalid.yaml": "dispatch_true_invalid_covered",
    "diagnostic_invalid_mode.yaml": "invalid_mode_covered",
    "diagnostic_missing_sigmatheta_blocks.yaml": "missing_sigmatheta_blocks_covered",
}


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return loaded


def _validate_fixture(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    data = _load_yaml(path)
    fixture_id = _nested(data, "fixture", "id")
    expected = _nested(data, "fixture", "expected")
    fracture = _nested(data, "lot", "fracture")
    if not fixture_id:
        errors.append("missing fixture.id")
    if not isinstance(expected, dict):
        errors.append("missing fixture.expected")
    if not isinstance(fracture, dict):
        errors.append("missing lot.fracture")
        return False, errors

    model = fracture.get("fracture_model")
    if path.name == "diagnostic_enabled_penny_pre_runner.yaml":
      # Keep this branch explicit because PENNY_SHAPED must stay diagnostic-only.
        if model != "PENNY_SHAPED":
            errors.append("expected PENNY_SHAPED fracture_model")
    elif model != "PKN":
        errors.append("expected PKN fracture_model")

    diagnostics = fracture.get("fracture_gate_diagnostics")
    if path.name == "diagnostic_disabled_default.yaml":
        if diagnostics is not None:
            errors.append("default-disabled fixture must omit diagnostics block")
    else:
        if not isinstance(diagnostics, dict):
            errors.append("missing fracture_gate_diagnostics")
        else:
            enabled = diagnostics.get("enabled")
            mode = diagnostics.get("mode")
            dispatch = diagnostics.get("dispatch_runtime_enabled")
            if enabled is not True:
                errors.append("diagnostics.enabled must be true")
            if path.name == "diagnostic_invalid_mode.yaml":
                if mode == "pre_runner" or mode == "diagnostic_only":
                    errors.append("invalid-mode fixture must use unsupported mode")
            elif mode not in {"pre_runner", "diagnostic_only"}:
                errors.append("diagnostics.mode must be accepted")
            if path.name == "diagnostic_dispatch_true_invalid.yaml":
                if dispatch is not True:
                    errors.append("dispatch-true fixture must set dispatch true")
            elif dispatch is not False:
                errors.append("dispatch_runtime_enabled must be false")

    if isinstance(expected, dict):
        if expected.get("runtime_physical_dispatch_enabled") is not False:
            errors.append("runtime physical dispatch must remain false")
        if expected.get("buz29_execution_allowed") is not False:
            errors.append("BUZ29 execution must remain false")
    return not errors, errors


def validate_fixtures(fixtures_dir: Path) -> dict[str, Any]:
    details: dict[str, Any] = {}
    coverage = {value: False for value in EXPECTED_FIXTURES.values()}
    errors: list[str] = []

    for filename, coverage_key in EXPECTED_FIXTURES.items():
        path = fixtures_dir / filename
        if not path.exists():
            errors.append(f"missing fixture: {filename}")
            details[filename] = {"present": False, "valid": False}
            continue
        valid, fixture_errors = _validate_fixture(path)
        coverage[coverage_key] = valid
        details[filename] = {
            "present": True,
            "valid": valid,
            "errors": fixture_errors,
        }
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    fixture_status = (
        "DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID"
        if not errors and all(coverage.values())
        else "DIAGNOSTIC_PRE_RUNNER_FIXTURES_INVALID"
    )
    return {
        "phase": "11.10Z",
        "fixture_status": fixture_status,
        "fixture_count": sum(1 for item in details.values() if item["present"]),
        **coverage,
        "runtime_physical_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "recommended_next_phase": (
            "PHASE11_11A_VALIDATE_DIAGNOSTIC_PRE_RUNNER_ON_CONTROLLED_CASES"
        ),
        "errors": errors,
        "fixtures": details,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.10Z diagnostic pre-runner fixtures",
        "",
        f"- phase: `{report['phase']}`",
        f"- fixture_status: `{report['fixture_status']}`",
        f"- fixture_count: `{report['fixture_count']}`",
        f"- runtime_physical_dispatch_enabled: `{report['runtime_physical_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{report['pkn_behavior_changed']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Coverage",
        "",
    ]
    for key in EXPECTED_FIXTURES.values():
        lines.append(f"- {key}: `{report[key]}`")
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 11.10Z diagnostic pre-runner fixtures."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase11_10z"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = validate_fixtures(args.fixtures_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"fixture_status={report['fixture_status']}")
    print(f"fixture_count={report['fixture_count']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    for error in report["errors"]:
        print(f"error={error}")
    return 0 if report["fixture_status"] == "DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
