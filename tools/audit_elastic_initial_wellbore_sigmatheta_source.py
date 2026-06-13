#!/usr/bin/env python3
"""Audit fixtures for the elastic initial wellbore sigma-theta source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


IMPLEMENTED_STATUS = "ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED"
PARTIAL_STATUS = "ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_PARTIAL"
INVALID_STATUS = "ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_INVALID"

REQUIRED_FIXTURES = {
    "elastic_provider_disabled_default.yaml": "disabled_default_case_valid",
    "elastic_provider_ready_not_reached.yaml": "ready_not_reached_case_valid",
    "elastic_provider_reached_pkn.yaml": "reached_pkn_case_valid",
    "elastic_provider_reached_penny_diagnostic.yaml": "reached_penny_diagnostic_case_valid",
    "elastic_provider_invalid_physically_validated_true.yaml": "physically_validated_true_invalid",
    "elastic_provider_invalid_legacy_equivalent_true.yaml": "legacy_equivalent_true_invalid",
    "elastic_provider_ambiguous_with_diagnostic_input.yaml": "ambiguous_provider_input_invalid",
    "elastic_provider_invalid_missing_far_field_stress.yaml": "missing_far_field_stress_invalid",
    "elastic_provider_invalid_missing_wellbore_pressure.yaml": "missing_wellbore_pressure_invalid",
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


def _diagnostic_input(fracture: dict[str, Any]) -> dict[str, Any]:
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


def _require_elastic_provider(
    provider: dict[str, Any],
    errors: list[str],
    *,
    physically_validated: bool = False,
    legacy_equivalent: bool = False,
    require_far_field: bool = True,
    require_pressure: bool = True,
) -> None:
    if provider.get("enabled") is not True:
        errors.append("sigma_theta_provider.enabled must be true")
    if provider.get("source") != "ELASTIC_INITIAL_WELLBORE_STATE":
        errors.append("provider source must be ELASTIC_INITIAL_WELLBORE_STATE")
    if require_far_field:
        far_field = provider.get("far_field_stress_compression_positive_Pa")
        if not isinstance(far_field, (int, float)) or far_field <= 0:
            errors.append("far-field compression-positive stress must be positive")
    elif "far_field_stress_compression_positive_Pa" in provider:
        errors.append("missing-far-field fixture must omit far-field stress")
    if require_pressure:
        pressure = provider.get("wellbore_pressure_Pa")
        if not isinstance(pressure, (int, float)) or pressure < 0:
            errors.append("wellbore pressure must be nonnegative")
    elif "wellbore_pressure_Pa" in provider:
        errors.append("missing-pressure fixture must omit wellbore pressure")
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

    if filename == "elastic_provider_disabled_default.yaml":
        if expected.get("diagnostics_enabled") is not False:
            errors.append("default fixture must disable diagnostics")
        if diagnostics:
            errors.append("default fixture must omit fracture_gate_diagnostics")
        if provider:
            errors.append("default fixture must omit sigma_theta_provider")
        return not errors, errors

    _require_limited_gate(diagnostics, errors)

    if filename == "elastic_provider_ready_not_reached.yaml":
        _require_elastic_provider(provider, errors)
        if expected.get("gate_status") != "FRACTURE_GATE_READY_NOT_REACHED":
            errors.append("ready_not_reached fixture must expect READY_NOT_REACHED")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_NOT_EXECUTED":
            errors.append("ready_not_reached fixture must not execute dispatch")
    elif filename == "elastic_provider_reached_pkn.yaml":
        _require_elastic_provider(provider, errors)
        if fracture.get("fracture_model") != "PKN":
            errors.append("PKN reached fixture must use PKN")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PKN_ELIGIBLE":
            errors.append("PKN reached fixture must be diagnostically PKN eligible")
    elif filename == "elastic_provider_reached_penny_diagnostic.yaml":
        _require_elastic_provider(provider, errors)
        if fracture.get("fracture_model") != "PENNY_SHAPED":
            errors.append("PENNY reached fixture must use PENNY_SHAPED")
        if expected.get("dispatch_status") != "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE":
            errors.append("PENNY reached fixture must remain diagnostic eligible")
    elif filename == "elastic_provider_invalid_physically_validated_true.yaml":
        _require_elastic_provider(provider, errors, physically_validated=True)
        if expected.get("blocking_reason") != "PHYSICAL_VALIDATION_NOT_ALLOWED_FOR_ELASTIC_SIGMATHETA_SOURCE":
            errors.append("physical-validation fixture must document rejection")
    elif filename == "elastic_provider_invalid_legacy_equivalent_true.yaml":
        _require_elastic_provider(provider, errors, legacy_equivalent=True)
        if expected.get("blocking_reason") != "LEGACY_EQUIVALENCE_NOT_ALLOWED_FOR_ELASTIC_SIGMATHETA_SOURCE":
            errors.append("legacy-equivalence fixture must document rejection")
    elif filename == "elastic_provider_ambiguous_with_diagnostic_input.yaml":
        _require_elastic_provider(provider, errors)
        if not _diagnostic_input(fracture):
            errors.append("ambiguous fixture must include diagnostic input too")
        if expected.get("blocking_reason") != "SIGMATHETA_PROVIDER_AND_DIAGNOSTIC_INPUT_MUTUALLY_EXCLUSIVE":
            errors.append("ambiguous fixture must document mutual exclusion")
    elif filename == "elastic_provider_invalid_missing_far_field_stress.yaml":
        _require_elastic_provider(provider, errors, require_far_field=False)
        if expected.get("blocking_reason") != "MISSING_FAR_FIELD_STRESS":
            errors.append("missing far-field fixture must document missing field")
    elif filename == "elastic_provider_invalid_missing_wellbore_pressure.yaml":
        _require_elastic_provider(provider, errors, require_pressure=False)
        if expected.get("blocking_reason") != "MISSING_WELLBORE_PRESSURE":
            errors.append("missing pressure fixture must document missing field")

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

    metadata_path = fixtures_dir / "elastic_sigmatheta_source_metadata.json"
    metadata_valid = False
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata_valid = (
            metadata.get("implementation_status") == IMPLEMENTED_STATUS
            and metadata.get("source") == "ELASTIC_INITIAL_WELLBORE_STATE"
            and metadata.get("semi_physical") is True
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
        "phase": "ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE",
        "implementation_status": status,
        "source": "ELASTIC_INITIAL_WELLBORE_STATE",
        "semi_physical": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "metadata_valid": metadata_valid,
        "fixture_count": fixture_count,
        "recommended_next_phase": "PHASE_VALIDATE_ELASTIC_SIGMATHETA_SOURCE_AGAINST_KNOWN_ANALYTIC_CASE",
        "errors": errors,
        "details": details,
        **flags,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Elastic initial wellbore sigma-theta source audit",
        "",
        f"- implementation_status: `{report['implementation_status']}`",
        f"- source: `{report['source']}`",
        f"- semi_physical: `{report['semi_physical']}`",
        f"- physically_validated: `{report['physically_validated']}`",
        f"- legacy_equivalent: `{report['legacy_equivalent']}`",
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
        description="Audit fixtures for the elastic initial wellbore sigma-theta source."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase_elastic_sigmatheta_source"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = audit(args.fixtures_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"implementation_status={report['implementation_status']}")
    print(f"source={report['source']}")
    print(f"runtime_dispatch_enabled={report['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    return 0 if report["implementation_status"] == IMPLEMENTED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
