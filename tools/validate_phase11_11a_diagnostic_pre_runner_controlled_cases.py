#!/usr/bin/env python3
"""Validate Phase 11.11A diagnostic pre-runner controlled cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED = {
    "diagnostic_disabled_default.yaml": "default_disabled_behavior_valid",
    "diagnostic_enabled_pkn_pre_runner.yaml": "diagnostic_opt_in_behavior_valid",
    "diagnostic_enabled_penny_pre_runner.yaml": "penny_diagnostic_behavior_valid",
    "diagnostic_dispatch_true_invalid.yaml": "dispatch_runtime_enabled_true_rejected",
    "diagnostic_invalid_mode.yaml": "invalid_mode_rejected",
    "diagnostic_missing_sigmatheta_blocks.yaml": "missing_sigmatheta_blocks",
}


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def _expected(data: dict[str, Any]) -> dict[str, Any]:
    fixture = data.get("fixture")
    if not isinstance(fixture, dict):
        return {}
    expected = fixture.get("expected")
    return expected if isinstance(expected, dict) else {}


def validate(fixtures_dir: Path) -> dict[str, Any]:
    details: dict[str, Any] = {}
    coverage = {value: False for value in REQUIRED.values()}
    errors: list[str] = []

    for filename, key in REQUIRED.items():
        path = fixtures_dir / filename
        if not path.exists():
            errors.append(f"missing fixture: {filename}")
            details[filename] = {"present": False, "valid": False}
            continue
        data = _load(path)
        expected = _expected(data)
        valid = True
        fixture_errors: list[str] = []
        if expected.get("runtime_physical_dispatch_enabled") is not False:
            valid = False
            fixture_errors.append("runtime physical dispatch must remain false")
        if expected.get("buz29_execution_allowed") is not False:
            valid = False
            fixture_errors.append("BUZ29 execution must remain false")
        if filename == "diagnostic_disabled_default.yaml":
            if expected.get("diagnostics_enabled") is not False:
                valid = False
                fixture_errors.append("default disabled fixture must disable diagnostics")
            if expected.get("diagnostic_output_expected") is not False:
                valid = False
                fixture_errors.append("default disabled fixture must not expect diagnostic output")
        if filename in {
            "diagnostic_enabled_pkn_pre_runner.yaml",
            "diagnostic_enabled_penny_pre_runner.yaml",
            "diagnostic_missing_sigmatheta_blocks.yaml",
        }:
            if expected.get("diagnostics_enabled") is not True:
                valid = False
                fixture_errors.append("enabled fixture must enable diagnostics")
            if expected.get("diagnostic_output_expected") is not True:
                valid = False
                fixture_errors.append("enabled fixture must expect isolated diagnostic output")
        if filename == "diagnostic_dispatch_true_invalid.yaml":
            if expected.get("validation_status") != "rejected":
                valid = False
                fixture_errors.append("dispatch true fixture must be rejected")
        if filename == "diagnostic_invalid_mode.yaml":
            if expected.get("validation_status") != "rejected":
                valid = False
                fixture_errors.append("invalid mode fixture must be rejected")
        if filename == "diagnostic_missing_sigmatheta_blocks.yaml":
            if expected.get("gate_status") != "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE":
                valid = False
                fixture_errors.append("missing sigmaTheta fixture must block on initial state")
            if expected.get("dispatch_status") != "FRACTURE_DISPATCH_NOT_ALLOWED":
                valid = False
                fixture_errors.append("missing sigmaTheta fixture must forbid dispatch")

        coverage[key] = valid
        details[filename] = {"present": True, "valid": valid, "errors": fixture_errors}
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    diagnostic_output_isolated = (
        coverage["default_disabled_behavior_valid"]
        and coverage["diagnostic_opt_in_behavior_valid"]
        and coverage["missing_sigmatheta_blocks"]
    )
    valid = not errors and all(coverage.values()) and diagnostic_output_isolated
    status = (
        "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID"
        if valid
        else "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_INVALID"
    )
    return {
        "phase": "11.11A",
        "validation_status": status,
        "diagnostic_opt_in_behavior_valid": coverage["diagnostic_opt_in_behavior_valid"],
        "default_disabled_behavior_valid": coverage["default_disabled_behavior_valid"],
        "dispatch_runtime_enabled_true_rejected": coverage["dispatch_runtime_enabled_true_rejected"],
        "invalid_mode_rejected": coverage["invalid_mode_rejected"],
        "missing_sigmatheta_blocks": coverage["missing_sigmatheta_blocks"],
        "diagnostic_output_isolated": diagnostic_output_isolated,
        "runtime_physical_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "penny_diagnostic_behavior_valid": coverage["penny_diagnostic_behavior_valid"],
        "recommended_next_phase": "PHASE11_11B_COMPARE_PKN_RESULTS_WITH_DIAGNOSTIC_DISABLED_ENABLED",
        "errors": errors,
        "fixtures": details,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11A diagnostic pre-runner controlled cases",
        "",
        f"- validation_status: `{report['validation_status']}`",
        f"- diagnostic_opt_in_behavior_valid: `{report['diagnostic_opt_in_behavior_valid']}`",
        f"- default_disabled_behavior_valid: `{report['default_disabled_behavior_valid']}`",
        f"- dispatch_runtime_enabled_true_rejected: `{report['dispatch_runtime_enabled_true_rejected']}`",
        f"- invalid_mode_rejected: `{report['invalid_mode_rejected']}`",
        f"- missing_sigmatheta_blocks: `{report['missing_sigmatheta_blocks']}`",
        f"- diagnostic_output_isolated: `{report['diagnostic_output_isolated']}`",
        f"- runtime_physical_dispatch_enabled: `{report['runtime_physical_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
    ]
    if report["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 11.11A diagnostic pre-runner controlled cases."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase11_10z"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = validate(args.fixtures_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"validation_status={report['validation_status']}")
    print(f"diagnostic_output_isolated={report['diagnostic_output_isolated']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    for error in report["errors"]:
        print(f"error={error}")
    return 0 if report["validation_status"] == "DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
