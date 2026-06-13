#!/usr/bin/env python3
"""Audit fixtures for the axisymmetric elastic sigma-theta upgrade source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


IMPLEMENTED_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_SOURCE_IMPLEMENTED"
PARTIAL_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_SOURCE_PARTIAL"
INVALID_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_SOURCE_INVALID"
SOURCE = "AXISYMMETRIC_ELASTIC_WELLBORE_STATE"

REQUIRED_FIXTURES = {
    "axisymmetric_provider_ready_not_reached.yaml": "ready_not_reached_case_valid",
    "axisymmetric_provider_reached_pkn.yaml": "reached_pkn_case_valid",
    "axisymmetric_provider_reached_penny_diagnostic.yaml": "reached_penny_diagnostic_case_valid",
    "axisymmetric_provider_invalid_physically_validated_true.yaml": "physically_validated_true_invalid",
    "axisymmetric_provider_invalid_legacy_equivalent_true.yaml": "legacy_equivalent_true_invalid",
}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _expected(data: dict[str, Any]) -> dict[str, Any]:
    return _mapping(_mapping(data.get("fixture")).get("expected"))


def _fracture(data: dict[str, Any]) -> dict[str, Any]:
    return _mapping(_mapping(data.get("lot")).get("fracture"))


def _diagnostics(fracture: dict[str, Any]) -> dict[str, Any]:
    return _mapping(fracture.get("fracture_gate_diagnostics"))


def _provider(fracture: dict[str, Any]) -> dict[str, Any]:
    return _mapping(fracture.get("sigma_theta_provider"))


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


def _require_axisymmetric_provider(
    provider: dict[str, Any],
    errors: list[str],
    *,
    physically_validated: bool = False,
    legacy_equivalent: bool = False,
) -> None:
    if provider.get("enabled") is not True:
        errors.append("sigma_theta_provider.enabled must be true")
    if provider.get("source") != SOURCE:
        errors.append(f"provider source must be {SOURCE}")
    far_field = provider.get("far_field_stress_compression_positive_Pa")
    if not isinstance(far_field, (int, float)) or far_field <= 0:
        errors.append("far-field compression-positive stress must be positive")
    pressure = provider.get("wellbore_pressure_Pa")
    if not isinstance(pressure, (int, float)) or pressure < 0:
        errors.append("wellbore pressure must be nonnegative")
    if provider.get("physically_validated") is not physically_validated:
        errors.append("physically_validated flag mismatch")
    if provider.get("legacy_equivalent") is not legacy_equivalent:
        errors.append("legacy_equivalent flag mismatch")


def _validate_fixture(filename: str, path: Path) -> tuple[bool, list[str]]:
    data = _load_yaml(path)
    expected = _expected(data)
    fracture = _fracture(data)
    diagnostics = _diagnostics(fracture)
    provider = _provider(fracture)
    errors: list[str] = []

    if not expected:
        errors.append("missing fixture.expected")
    _require_safety(expected, errors)
    _require_limited_gate(diagnostics, errors)

    if filename == "axisymmetric_provider_invalid_physically_validated_true.yaml":
        _require_axisymmetric_provider(provider, errors, physically_validated=True)
        if expected.get("blocking_reason") != (
            "PHYSICAL_VALIDATION_NOT_ALLOWED_FOR_AXISYMMETRIC_SIGMATHETA_SOURCE"
        ):
            errors.append("physical-validation fixture must document rejection")
    elif filename == "axisymmetric_provider_invalid_legacy_equivalent_true.yaml":
        _require_axisymmetric_provider(provider, errors, legacy_equivalent=True)
        if expected.get("blocking_reason") != (
            "LEGACY_EQUIVALENCE_NOT_ALLOWED_FOR_AXISYMMETRIC_SIGMATHETA_SOURCE"
        ):
            errors.append("legacy-equivalence fixture must document rejection")
    else:
        _require_axisymmetric_provider(provider, errors)
        if filename == "axisymmetric_provider_reached_pkn.yaml":
            if fracture.get("fracture_model") != "PKN":
                errors.append("PKN reached fixture must use PKN")
            if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PKN_ELIGIBLE":
                errors.append("PKN reached fixture must be diagnostically eligible")
        elif filename == "axisymmetric_provider_reached_penny_diagnostic.yaml":
            if fracture.get("fracture_model") != "PENNY_SHAPED":
                errors.append("PENNY reached fixture must use PENNY_SHAPED")
            if expected.get("dispatch_status") != (
                "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE"
            ):
                errors.append("PENNY fixture must remain diagnostic eligible")
        elif filename == "axisymmetric_provider_ready_not_reached.yaml":
            if expected.get("gate_status") != "FRACTURE_GATE_READY_NOT_REACHED":
                errors.append("ready fixture must expect READY_NOT_REACHED")

    return not errors, errors


def audit(fixtures_dir: Path) -> dict[str, Any]:
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

    metadata_path = fixtures_dir / "axisymmetric_sigmatheta_upgrade_metadata.json"
    metadata_valid = False
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata_valid = (
            metadata.get("implementation_status") == IMPLEMENTED_STATUS
            and metadata.get("source") == SOURCE
            and metadata.get("physically_validated") is False
            and metadata.get("legacy_equivalent") is False
            and metadata.get("runtime_dispatch_enabled") is False
            and metadata.get("buz29_execution_allowed") is False
            and metadata.get("pkn_behavior_changed") is False
            and metadata.get("penny_shaped_runtime_enabled") is False
        )
        if not metadata_valid:
            errors.append("metadata safety/status flags are invalid")
    else:
        errors.append("missing metadata")

    fixture_count = sum(1 for name in REQUIRED_FIXTURES if (fixtures_dir / name).exists())
    all_valid = all(flags.values()) and metadata_valid and not errors
    status = IMPLEMENTED_STATUS if all_valid else PARTIAL_STATUS if fixture_count else INVALID_STATUS

    return {
        "phase": "ELASTIC_SIGMATHETA_UPGRADE_SOURCE_IMPLEMENTATION",
        "implementation_status": status,
        "source": SOURCE,
        "selected_formula": "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE",
        "fixture_count": fixture_count,
        "metadata_valid": metadata_valid,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "physically_validated": False,
        "legacy_equivalent": False,
        "recommended_next_phase": "PHASE_VALIDATE_ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES",
        **flags,
        "details": details,
        "errors": errors,
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Elastic Sigma-Theta Upgrade Source Audit",
            "",
            f"- status: `{result['implementation_status']}`",
            f"- source: `{result['source']}`",
            f"- selected_formula: `{result['selected_formula']}`",
            f"- fixture_count: `{result['fixture_count']}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- buz29_execution_allowed: `{str(result['buz29_execution_allowed']).lower()}`",
            f"- pkn_behavior_changed: `{str(result['pkn_behavior_changed']).lower()}`",
            "",
            "This audit verifies a diagnostic source contract only. It does not "
            "enable physical dispatch, BUZ29 execution or legacy equivalence.",
            "",
        ]
        if result["errors"]:
            lines.append("## Errors")
            lines.extend(f"- {error}" for error in result["errors"])
            lines.append("")
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit axisymmetric elastic sigma-theta upgrade fixtures."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase_elastic_sigmatheta_upgrade"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = audit(args.fixtures_dir)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"implementation_status={result['implementation_status']}")
    print(f"source={result['source']}")
    print(f"fixture_count={result['fixture_count']}")
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    for error in result["errors"]:
        print(f"error={error}")
    return 0 if result["implementation_status"] == IMPLEMENTED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
