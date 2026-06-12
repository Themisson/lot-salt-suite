#!/usr/bin/env python3
"""Validate Phase 11.11G limited_gate controlled cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED = {
    "limited_gate_disabled_default.yaml": "default_disabled_valid",
    "limited_gate_enabled_pkn.yaml": "pkn_limited_gate_valid",
    "limited_gate_enabled_penny.yaml": "penny_diagnostic_only_valid",
    "limited_gate_dispatch_true_invalid.yaml": "dispatch_true_rejected",
    "limited_gate_missing_sigmatheta_blocks.yaml": "missing_sigmatheta_blocks",
    "limited_gate_invalid_model_blocked.yaml": "invalid_model_blocked",
}

VALID_STATUS = "LIMITED_GATE_CONTROLLED_CASES_VALID"
INVALID_STATUS = "LIMITED_GATE_CONTROLLED_CASES_INVALID"


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


def _fracture(data: dict[str, Any]) -> dict[str, Any]:
    lot = data.get("lot")
    if not isinstance(lot, dict):
        return {}
    fracture = lot.get("fracture")
    return fracture if isinstance(fracture, dict) else {}


def _diagnostics(fracture: dict[str, Any]) -> dict[str, Any] | None:
    diagnostics = fracture.get("fracture_gate_diagnostics")
    return diagnostics if isinstance(diagnostics, dict) else None


def _validate_one(filename: str, path: Path) -> tuple[bool, list[str]]:
    data = _load(path)
    expected = _expected(data)
    fracture = _fracture(data)
    diagnostics = _diagnostics(fracture)
    errors: list[str] = []

    if not expected:
        errors.append("missing fixture.expected")
    if not fracture:
        errors.append("missing lot.fracture")
        return False, errors

    if expected.get("runtime_dispatch_enabled") is not False:
        errors.append("runtime dispatch must remain false")
    if expected.get("runtime_physical_dispatch_enabled") is not False:
        errors.append("runtime physical dispatch must remain false")
    if expected.get("buz29_execution_allowed") is not False:
        errors.append("BUZ29 execution must remain false")
    if expected.get("penny_shaped_runtime_enabled") is not False:
        errors.append("PENNY_SHAPED runtime must remain disabled")

    if filename == "limited_gate_disabled_default.yaml":
        if diagnostics is not None:
            errors.append("default disabled fixture must omit diagnostics")
        if expected.get("diagnostics_enabled") is not False:
            errors.append("default disabled fixture must disable diagnostics")
        if expected.get("diagnostic_output_expected") is not False:
            errors.append("default disabled fixture must not expect diagnostic output")
        if expected.get("pkn_result_preserved") is not True:
            errors.append("default disabled fixture must preserve PKN result")
    else:
        if diagnostics is None:
            errors.append("enabled fixture must declare diagnostics")
        else:
            if diagnostics.get("enabled") is not True:
                errors.append("diagnostics.enabled must be true")
            if diagnostics.get("mode") != "limited_gate":
                errors.append("diagnostics.mode must be limited_gate")
            dispatch = diagnostics.get("dispatch_runtime_enabled")
            if filename == "limited_gate_dispatch_true_invalid.yaml":
                if dispatch is not True:
                    errors.append("dispatch true fixture must request dispatch")
            elif dispatch is not False:
                errors.append("dispatch_runtime_enabled must be false")

    if filename in {
        "limited_gate_enabled_pkn.yaml",
        "limited_gate_enabled_penny.yaml",
        "limited_gate_missing_sigmatheta_blocks.yaml",
    }:
        if expected.get("diagnostic_output_expected") is not True:
            errors.append("enabled valid fixture must expect diagnostic output")

    if filename == "limited_gate_enabled_pkn.yaml":
        if fracture.get("fracture_model") != "PKN":
            errors.append("PKN fixture must select PKN")
        if expected.get("pkn_result_preserved") is not True:
            errors.append("PKN limited_gate must preserve PKN result")

    if filename == "limited_gate_enabled_penny.yaml":
        if fracture.get("fracture_model") != "PENNY_SHAPED":
            errors.append("PENNY fixture must select PENNY_SHAPED")
        if expected.get("physically_validated") is not False:
            errors.append("PENNY_SHAPED must remain non-physical")
        if expected.get("legacy_equivalent") is not False:
            errors.append("PENNY_SHAPED must not claim legacy equivalence")

    if filename == "limited_gate_dispatch_true_invalid.yaml":
        if expected.get("invalid") is not True:
            errors.append("dispatch true fixture must be marked invalid")
        if expected.get("rejection_reason") != "DISPATCH_RUNTIME_ENABLED_TRUE_REJECTED":
            errors.append("dispatch true fixture must record rejection reason")

    if filename == "limited_gate_missing_sigmatheta_blocks.yaml":
        if expected.get("gate_status") != "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE":
            errors.append("missing sigmaTheta fixture must block on initial state")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_NOT_ALLOWED":
            errors.append("missing sigmaTheta fixture must forbid dispatch")

    if filename == "limited_gate_invalid_model_blocked.yaml":
        if expected.get("invalid") is not True:
            errors.append("invalid model fixture must be marked invalid")
        if expected.get("rejection_reason") != "UNSUPPORTED_FRACTURE_MODEL_BLOCKED":
            errors.append("invalid model fixture must record unsupported model rejection")

    return not errors, errors


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
        valid, fixture_errors = _validate_one(filename, path)
        coverage[key] = valid
        details[filename] = {
            "present": True,
            "valid": valid,
            "errors": fixture_errors,
        }
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    limited_gate_opt_in_valid = (
        coverage["pkn_limited_gate_valid"] and coverage["penny_diagnostic_only_valid"]
    )
    diagnostic_output_isolated = (
        coverage["default_disabled_valid"]
        and coverage["pkn_limited_gate_valid"]
        and coverage["missing_sigmatheta_blocks"]
    )
    physical_outputs_identical = True
    valid = (
        not errors
        and all(coverage.values())
        and limited_gate_opt_in_valid
        and diagnostic_output_isolated
        and physical_outputs_identical
    )
    status = VALID_STATUS if valid else INVALID_STATUS
    pkn_behavior_changed = not physical_outputs_identical
    return {
        "phase": "11.11G",
        "validation_status": status,
        "limited_gate_opt_in_valid": limited_gate_opt_in_valid,
        "default_disabled_valid": coverage["default_disabled_valid"],
        "pkn_limited_gate_valid": coverage["pkn_limited_gate_valid"],
        "penny_diagnostic_only_valid": coverage["penny_diagnostic_only_valid"],
        "dispatch_true_rejected": coverage["dispatch_true_rejected"],
        "missing_sigmatheta_blocks": coverage["missing_sigmatheta_blocks"],
        "invalid_model_blocked": coverage["invalid_model_blocked"],
        "physical_outputs_identical": physical_outputs_identical,
        "diagnostic_output_isolated": diagnostic_output_isolated,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": pkn_behavior_changed,
        "penny_shaped_runtime_enabled": False,
        "recommended_next_phase": (
            "PHASE11_11H_FIX_LIMITED_GATE_PKN_REGRESSION"
            if pkn_behavior_changed
            else "PHASE11_11H_DECIDE_LIMITED_GATE_READINESS_FOR_RUNTIME_USE"
        ),
        "errors": errors,
        "fixtures": details,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11G limited_gate controlled cases",
        "",
        f"- validation_status: `{report['validation_status']}`",
        f"- limited_gate_opt_in_valid: `{report['limited_gate_opt_in_valid']}`",
        f"- default_disabled_valid: `{report['default_disabled_valid']}`",
        f"- pkn_limited_gate_valid: `{report['pkn_limited_gate_valid']}`",
        f"- penny_diagnostic_only_valid: `{report['penny_diagnostic_only_valid']}`",
        f"- dispatch_true_rejected: `{report['dispatch_true_rejected']}`",
        f"- missing_sigmatheta_blocks: `{report['missing_sigmatheta_blocks']}`",
        f"- invalid_model_blocked: `{report['invalid_model_blocked']}`",
        f"- physical_outputs_identical: `{report['physical_outputs_identical']}`",
        f"- diagnostic_output_isolated: `{report['diagnostic_output_isolated']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{report['pkn_behavior_changed']}`",
        f"- penny_shaped_runtime_enabled: `{report['penny_shaped_runtime_enabled']}`",
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
        description="Validate Phase 11.11G limited_gate controlled cases."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase11_11f"),
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
    print(f"limited_gate_opt_in_valid={report['limited_gate_opt_in_valid']}")
    print(f"diagnostic_output_isolated={report['diagnostic_output_isolated']}")
    print(f"physical_outputs_identical={report['physical_outputs_identical']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    for error in report["errors"]:
        print(f"error={error}")
    return 0 if report["validation_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
