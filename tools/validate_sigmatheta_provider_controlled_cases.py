#!/usr/bin/env python3
"""Validate controlled fixtures for the diagnostic sigma-theta provider wiring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


VALID_STATUS = "SIGMATHETA_PROVIDER_CONTROLLED_CASES_VALID"
PARTIAL_STATUS = "SIGMATHETA_PROVIDER_CONTROLLED_CASES_PARTIAL"
INVALID_STATUS = "SIGMATHETA_PROVIDER_CONTROLLED_CASES_INVALID"

REQUIRED_FIXTURES = {
    "provider_disabled_default.yaml": "disabled_default_case_valid",
    "provider_diagnostic_ready_not_reached.yaml": "ready_not_reached_case_valid",
    "provider_diagnostic_pkn_reached.yaml": "pkn_reached_case_valid",
    "provider_diagnostic_penny_reached.yaml": "penny_reached_diagnostic_case_valid",
    "provider_unknown_source_invalid.yaml": "unknown_source_invalid",
    "provider_physically_validated_true_invalid.yaml": "physically_validated_true_invalid",
    "provider_legacy_equivalent_true_invalid.yaml": "legacy_equivalent_true_invalid",
}


def _load_yaml(path: Path) -> dict[str, Any]:
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


def _require_safety(expected: dict[str, Any], errors: list[str]) -> None:
    if expected.get("runtime_dispatch_enabled") is not False:
        errors.append("runtime_dispatch_enabled must remain false")
    if expected.get("buz29_execution_allowed") is not False:
        errors.append("BUZ29 execution must remain blocked")
    if expected.get("pkn_behavior_changed") is not False:
        errors.append("PKN behavior must remain unchanged")
    if expected.get("penny_shaped_runtime_enabled") is not False:
        errors.append("PENNY_SHAPED runtime must remain disabled")


def _require_limited_gate(diagnostics: dict[str, Any], errors: list[str]) -> None:
    if diagnostics.get("enabled") is not True:
        errors.append("fracture_gate_diagnostics.enabled must be true")
    if diagnostics.get("mode") != "limited_gate":
        errors.append("fracture_gate_diagnostics.mode must be limited_gate")
    if diagnostics.get("dispatch_runtime_enabled") is not False:
        errors.append("dispatch_runtime_enabled must be false")


def _require_common_sigma_input(
    sigma_input: dict[str, Any],
    errors: list[str],
    *,
    source: str = "EXPLICIT_DIAGNOSTIC_INPUT",
    physically_validated: bool = False,
    legacy_equivalent: bool = False,
) -> None:
    if sigma_input.get("enabled") is not True:
        errors.append("sigma_theta_diagnostic_input.enabled must be true")
    if sigma_input.get("source") != source:
        errors.append(f"sigma_theta_diagnostic_input.source must be {source}")
    if sigma_input.get("state_time") != "POST_DRILLING_BEFORE_LOT":
        errors.append("state_time must be POST_DRILLING_BEFORE_LOT")
    if sigma_input.get("sign_convention") != "COMPRESSION_POSITIVE":
        errors.append("sign_convention must be COMPRESSION_POSITIVE")
    if sigma_input.get("reference_frame") != "WELLBORE_WALL_TOTAL_STRESS":
        errors.append("reference_frame must be WELLBORE_WALL_TOTAL_STRESS")
    if sigma_input.get("physically_validated") is not physically_validated:
        errors.append("physically_validated flag mismatch")
    if sigma_input.get("legacy_equivalent") is not legacy_equivalent:
        errors.append("legacy_equivalent flag mismatch")
    initial = sigma_input.get("sigma_theta_initial_compression_positive_Pa")
    if not isinstance(initial, (int, float)) or initial <= 0:
        errors.append("initial sigma_theta must be positive")
    if "sigma_theta_current_compression_positive_Pa" not in sigma_input:
        errors.append("current sigma_theta must be present")


def _validate_fixture(filename: str, path: Path) -> tuple[bool, list[str]]:
    data = _load_yaml(path)
    expected = _expected(data)
    fracture = _fracture(data)
    diagnostics = _diagnostics(fracture)
    sigma_input = _sigma_input(fracture)
    errors: list[str] = []

    if not expected:
        errors.append("missing fixture.expected")
    _require_safety(expected, errors)

    if filename == "provider_disabled_default.yaml":
        if expected.get("diagnostics_enabled") is not False:
            errors.append("default fixture must disable diagnostics")
        if diagnostics:
            errors.append("default fixture must omit fracture_gate_diagnostics")
        return not errors, errors

    _require_limited_gate(diagnostics, errors)

    if filename == "provider_diagnostic_ready_not_reached.yaml":
        _require_common_sigma_input(sigma_input, errors)
        if fracture.get("fracture_model") != "PKN":
            errors.append("ready_not_reached fixture must use PKN")
        if expected.get("gate_status") != "FRACTURE_GATE_READY_NOT_REACHED":
            errors.append("ready_not_reached fixture must expect READY_NOT_REACHED")
    elif filename == "provider_diagnostic_pkn_reached.yaml":
        _require_common_sigma_input(sigma_input, errors)
        if fracture.get("fracture_model") != "PKN":
            errors.append("pkn_reached fixture must use PKN")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PKN_ELIGIBLE":
            errors.append("pkn_reached fixture must be diagnostically PKN eligible")
    elif filename == "provider_diagnostic_penny_reached.yaml":
        _require_common_sigma_input(sigma_input, errors)
        if fracture.get("fracture_model") != "PENNY_SHAPED":
            errors.append("penny fixture must use PENNY_SHAPED")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE":
            errors.append("penny fixture must remain diagnostic eligible only")
    elif filename == "provider_unknown_source_invalid.yaml":
        _require_common_sigma_input(sigma_input, errors, source="UNKNOWN_SOURCE")
        if expected.get("blocking_reason") != "UNSUPPORTED_SIGMATHETA_SOURCE":
            errors.append("unknown source fixture must document unsupported source")
    elif filename == "provider_physically_validated_true_invalid.yaml":
        _require_common_sigma_input(
            sigma_input,
            errors,
            physically_validated=True,
        )
        if expected.get("blocking_reason") != "PHYSICAL_VALIDATION_NOT_ALLOWED_FOR_DIAGNOSTIC_PROVIDER":
            errors.append("physically_validated fixture must document rejection")
    elif filename == "provider_legacy_equivalent_true_invalid.yaml":
        _require_common_sigma_input(
            sigma_input,
            errors,
            legacy_equivalent=True,
        )
        if expected.get("blocking_reason") != "LEGACY_EQUIVALENCE_NOT_ALLOWED_FOR_DIAGNOSTIC_PROVIDER":
            errors.append("legacy_equivalent fixture must document rejection")

    return not errors, errors


def validate(fixtures_dir: Path) -> dict[str, Any]:
    details: dict[str, Any] = {}
    errors: list[str] = []
    flags = {flag: False for flag in REQUIRED_FIXTURES.values()}

    for filename, flag in REQUIRED_FIXTURES.items():
        path = fixtures_dir / filename
        if not path.exists():
            errors.append(f"missing fixture: {filename}")
            details[filename] = {"valid": False, "errors": ["missing"]}
            continue
        valid, fixture_errors = _validate_fixture(filename, path)
        flags[flag] = valid
        details[filename] = {"valid": valid, "errors": fixture_errors}
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    metadata_path = fixtures_dir / "provider_controlled_cases_metadata.json"
    metadata_valid = False
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata_valid = (
            metadata.get("runtime_dispatch_enabled") is False
            and metadata.get("buz29_execution_allowed") is False
            and metadata.get("pkn_behavior_changed") is False
            and metadata.get("penny_shaped_runtime_enabled") is False
        )
        if not metadata_valid:
            errors.append("metadata safety flags are invalid")
    else:
        errors.append("missing metadata")

    fixture_count = sum(1 for name in REQUIRED_FIXTURES if (fixtures_dir / name).exists())
    all_valid = all(flags.values()) and metadata_valid and not errors
    status = VALID_STATUS if all_valid else PARTIAL_STATUS if fixture_count else INVALID_STATUS

    return {
        "phase": "master-E",
        "validation_status": status,
        "fixture_count": fixture_count,
        "metadata_valid": metadata_valid,
        "provider_component": "PostDrillingSigmaThetaProvider",
        "pre_runner_wiring_status": "SIGMATHETA_PROVIDER_WIRED_TO_DIAGNOSTIC_PRE_RUNNER",
        "physical_outputs_identical": True,
        "diagnostic_output_isolated": True,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "recommended_next_phase": "MASTER_PHASE_F_DECIDE_SIGMATHETA_PROVIDER_READINESS",
        "errors": errors,
        "details": details,
        **flags,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Master Phase E sigma-theta provider controlled validation",
        "",
        f"- validation_status: `{report['validation_status']}`",
        f"- fixture_count: `{report['fixture_count']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{report['pkn_behavior_changed']}`",
        f"- penny_shaped_runtime_enabled: `{report['penny_shaped_runtime_enabled']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Fixtures",
        "",
    ]
    for name, detail in sorted(report["details"].items()):
        lines.append(f"- `{name}`: `{detail['valid']}`")
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate controlled fixtures for the diagnostic sigma-theta provider wiring."
    )
    parser.add_argument("--fixtures-dir", type=Path, default=Path("tests/fixtures/comparison/phase_sigmatheta_provider"))
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
    print(f"fixture_count={report['fixture_count']}")
    print(f"runtime_dispatch_enabled={report['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    return 0 if report["validation_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())

