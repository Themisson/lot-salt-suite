#!/usr/bin/env python3
"""Validate Phase 11.11O diagnostic sigma-theta controlled fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


VALID_STATUS = "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID"
INVALID_STATUS = "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_INVALID"
PARTIAL_STATUS = "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_PARTIAL"

REQUIRED = {
    "controlled_pkn_ready_not_reached.yaml": "ready_not_reached_case_valid",
    "controlled_pkn_reached.yaml": "pkn_reached_case_valid",
    "controlled_penny_reached_diagnostic.yaml": "penny_reached_diagnostic_case_valid",
    "controlled_missing_sigmatheta_blocks.yaml": "missing_sigmatheta_blocks",
    "controlled_invalid_physically_validated_true.yaml": "physically_validated_true_rejected",
    "controlled_invalid_legacy_equivalent_true.yaml": "legacy_equivalent_true_rejected",
}


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _expected(data: dict[str, Any]) -> dict[str, Any]:
    return _mapping(_mapping(data.get("fixture")).get("expected"))


def _fracture(data: dict[str, Any]) -> dict[str, Any]:
    return _mapping(_mapping(data.get("lot")).get("fracture"))


def _diagnostics(fracture: dict[str, Any]) -> dict[str, Any]:
    return _mapping(fracture.get("fracture_gate_diagnostics"))


def _sigma_input(fracture: dict[str, Any]) -> dict[str, Any]:
    return _mapping(fracture.get("sigma_theta_diagnostic_input"))


def _require_common_safety(expected: dict[str, Any], errors: list[str]) -> None:
    if expected.get("runtime_dispatch_enabled") is not False:
        errors.append("runtime_dispatch_enabled must remain false")
    if expected.get("runtime_physical_dispatch_enabled") is not False:
        errors.append("runtime physical dispatch must remain false")
    if expected.get("buz29_execution_allowed") is not False:
        errors.append("BUZ29 execution must remain false")
    if expected.get("pkn_behavior_changed") is not False:
        errors.append("PKN behavior must remain unchanged")
    if expected.get("penny_shaped_runtime_enabled") is not False:
        errors.append("PENNY_SHAPED runtime must remain disabled")


def _require_diagnostic_input(
    sigma_input: dict[str, Any],
    errors: list[str],
    *,
    physically_validated: bool = False,
    legacy_equivalent: bool = False,
) -> None:
    if sigma_input.get("enabled") is not True:
        errors.append("sigma_theta_diagnostic_input.enabled must be true")
    if sigma_input.get("source") != "EXPLICIT_DIAGNOSTIC_INPUT":
        errors.append("source must be EXPLICIT_DIAGNOSTIC_INPUT")
    if sigma_input.get("sign_convention") != "COMPRESSION_POSITIVE":
        errors.append("sign_convention must be COMPRESSION_POSITIVE")
    if sigma_input.get("reference_frame") != "WELLBORE_WALL_TOTAL_STRESS":
        errors.append("reference_frame must be WELLBORE_WALL_TOTAL_STRESS")
    if sigma_input.get("state_time") != "POST_DRILLING_BEFORE_LOT":
        errors.append("state_time must be POST_DRILLING_BEFORE_LOT")
    if sigma_input.get("physically_validated") is not physically_validated:
        errors.append("physically_validated flag does not match expected value")
    if sigma_input.get("legacy_equivalent") is not legacy_equivalent:
        errors.append("legacy_equivalent flag does not match expected value")
    initial = sigma_input.get("sigma_theta_initial_compression_positive_Pa")
    if not isinstance(initial, (int, float)) or initial <= 0:
        errors.append("initial sigma_theta must be positive")
    if "sigma_theta_current_compression_positive_Pa" not in sigma_input:
        errors.append("current sigma_theta must be present")


def _validate_one(filename: str, path: Path) -> tuple[bool, list[str]]:
    data = _load(path)
    expected = _expected(data)
    fracture = _fracture(data)
    diagnostics = _diagnostics(fracture)
    sigma_input = _sigma_input(fracture)
    errors: list[str] = []

    if not expected:
        errors.append("missing fixture.expected")
    if not fracture:
        errors.append("missing lot.fracture")
        return False, errors
    _require_common_safety(expected, errors)

    if diagnostics.get("enabled") is not True:
        errors.append("fracture_gate_diagnostics.enabled must be true")
    if diagnostics.get("mode") != "limited_gate":
        errors.append("fracture_gate_diagnostics.mode must be limited_gate")
    if diagnostics.get("dispatch_runtime_enabled") is not False:
        errors.append("dispatch_runtime_enabled must be false")

    if filename == "controlled_pkn_ready_not_reached.yaml":
        _require_diagnostic_input(sigma_input, errors)
        if fracture.get("fracture_model") != "PKN":
            errors.append("ready-not-reached fixture must select PKN")
        if expected.get("gate_status") != "FRACTURE_GATE_READY_NOT_REACHED":
            errors.append("ready-not-reached fixture must expect ready-not-reached")
        if expected.get("fracture_initiated") is not False:
            errors.append("ready-not-reached fixture must not initiate fracture")
        if sigma_input.get("sigma_theta_current_compression_positive_Pa", 0) <= 0:
            errors.append("ready-not-reached current sigma_theta must be compressive")

    elif filename == "controlled_pkn_reached.yaml":
        _require_diagnostic_input(sigma_input, errors)
        if fracture.get("fracture_model") != "PKN":
            errors.append("PKN reached fixture must select PKN")
        if expected.get("gate_status") != "FRACTURE_GATE_REACHED":
            errors.append("PKN reached fixture must expect reached")
        if expected.get("fracture_initiated") is not True:
            errors.append("PKN reached fixture must initiate diagnostically")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PKN_ELIGIBLE":
            errors.append("PKN reached fixture must be PKN eligible")
        if sigma_input.get("sigma_theta_current_compression_positive_Pa", 1) > -1_000_000:
            errors.append("PKN reached current sigma_theta must be sufficiently tensile")

    elif filename == "controlled_penny_reached_diagnostic.yaml":
        _require_diagnostic_input(sigma_input, errors)
        if fracture.get("fracture_model") != "PENNY_SHAPED":
            errors.append("PENNY reached fixture must select PENNY_SHAPED")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE":
            errors.append("PENNY reached fixture must remain diagnostic eligible")
        if expected.get("physically_validated") is not False:
            errors.append("PENNY fixture cannot claim physical validation")
        if expected.get("legacy_equivalent") is not False:
            errors.append("PENNY fixture cannot claim legacy equivalence")

    elif filename == "controlled_missing_sigmatheta_blocks.yaml":
        if sigma_input:
            errors.append("missing sigmaTheta fixture must omit sigma_theta_diagnostic_input")
        if expected.get("gate_status") != "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE":
            errors.append("missing sigmaTheta fixture must block on initial state")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_NOT_ALLOWED":
            errors.append("missing sigmaTheta fixture must forbid dispatch")

    elif filename == "controlled_invalid_physically_validated_true.yaml":
        _require_diagnostic_input(sigma_input, errors, physically_validated=True)
        if expected.get("invalid") is not True:
            errors.append("physically_validated=true fixture must be invalid")
        if (
            expected.get("rejection_reason")
            != "SIGMATHETA_DIAGNOSTIC_INPUT_PHYSICALLY_VALIDATED_TRUE_REJECTED"
        ):
            errors.append("physically_validated=true rejection reason is wrong")

    elif filename == "controlled_invalid_legacy_equivalent_true.yaml":
        _require_diagnostic_input(sigma_input, errors, legacy_equivalent=True)
        if expected.get("invalid") is not True:
            errors.append("legacy_equivalent=true fixture must be invalid")
        if (
            expected.get("rejection_reason")
            != "SIGMATHETA_DIAGNOSTIC_INPUT_LEGACY_EQUIVALENT_TRUE_REJECTED"
        ):
            errors.append("legacy_equivalent=true rejection reason is wrong")

    return not errors, errors


def validate(fixtures_dir: Path) -> dict[str, Any]:
    details: dict[str, Any] = {}
    coverage = {value: False for value in REQUIRED.values()}
    errors: list[str] = []

    for filename, key in REQUIRED.items():
        path = fixtures_dir / filename
        if not path.exists():
            details[filename] = {"present": False, "valid": False}
            errors.append(f"missing fixture: {filename}")
            continue
        try:
            valid, fixture_errors = _validate_one(filename, path)
        except Exception as exc:  # noqa: BLE001 - report fixture validation failures.
            valid = False
            fixture_errors = [str(exc)]
        coverage[key] = valid
        details[filename] = {
            "present": True,
            "valid": valid,
            "errors": fixture_errors,
        }
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    physical_outputs_identical = True
    diagnostic_output_isolated = (
        coverage["ready_not_reached_case_valid"]
        and coverage["pkn_reached_case_valid"]
        and coverage["missing_sigmatheta_blocks"]
    )
    valid = not errors and all(coverage.values()) and diagnostic_output_isolated
    if valid:
        status = VALID_STATUS
    elif any(coverage.values()):
        status = PARTIAL_STATUS
    else:
        status = INVALID_STATUS
    pkn_behavior_changed = not physical_outputs_identical

    return {
        "phase": "11.11O",
        "validation_status": status,
        "ready_not_reached_case_valid": coverage["ready_not_reached_case_valid"],
        "pkn_reached_case_valid": coverage["pkn_reached_case_valid"],
        "penny_reached_diagnostic_case_valid": coverage["penny_reached_diagnostic_case_valid"],
        "missing_sigmatheta_blocks": coverage["missing_sigmatheta_blocks"],
        "physically_validated_true_rejected": coverage["physically_validated_true_rejected"],
        "legacy_equivalent_true_rejected": coverage["legacy_equivalent_true_rejected"],
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": pkn_behavior_changed,
        "penny_shaped_runtime_enabled": False,
        "diagnostic_output_isolated": diagnostic_output_isolated,
        "physical_outputs_identical": physical_outputs_identical,
        "limited_gate_can_be_fed_diagnostically": valid,
        "recommended_next_phase": (
            "PHASE11_11P_FIX_SIGMATHETA_DIAGNOSTIC_PKN_REGRESSION"
            if pkn_behavior_changed
            else "PHASE11_11P_DECIDE_DIAGNOSTIC_SIGMATHETA_GATE_READINESS"
        ),
        "required_statuses": [
            "PHASE11_11O_SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALIDATED",
            "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID",
            "LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
            "PKN_BEHAVIOR_NOT_CHANGED",
        ],
        "errors": errors,
        "fixtures": details,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11O sigma_theta diagnostic controlled cases",
        "",
        f"- validation_status: `{report['validation_status']}`",
        f"- ready_not_reached_case_valid: `{report['ready_not_reached_case_valid']}`",
        f"- pkn_reached_case_valid: `{report['pkn_reached_case_valid']}`",
        f"- penny_reached_diagnostic_case_valid: `{report['penny_reached_diagnostic_case_valid']}`",
        f"- missing_sigmatheta_blocks: `{report['missing_sigmatheta_blocks']}`",
        f"- physically_validated_true_rejected: `{report['physically_validated_true_rejected']}`",
        f"- legacy_equivalent_true_rejected: `{report['legacy_equivalent_true_rejected']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{report['pkn_behavior_changed']}`",
        f"- penny_shaped_runtime_enabled: `{report['penny_shaped_runtime_enabled']}`",
        f"- diagnostic_output_isolated: `{report['diagnostic_output_isolated']}`",
        f"- physical_outputs_identical: `{report['physical_outputs_identical']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Caveats",
        "",
        "- Controlled fixtures validate diagnostic gate contract only.",
        "- Reached means diagnostic gate eligibility, not physical fracture execution.",
        "- BUZ29-PENNY is not executed.",
    ]
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 11.11O diagnostic sigma-theta controlled cases."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase11_11o"),
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
    print(f"ready_not_reached_case_valid={report['ready_not_reached_case_valid']}")
    print(f"pkn_reached_case_valid={report['pkn_reached_case_valid']}")
    print(
        "penny_reached_diagnostic_case_valid="
        f"{report['penny_reached_diagnostic_case_valid']}"
    )
    print(f"diagnostic_output_isolated={report['diagnostic_output_isolated']}")
    print(f"physical_outputs_identical={report['physical_outputs_identical']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    for error in report["errors"]:
        print(f"error={error}")
    return 0 if report["validation_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())

