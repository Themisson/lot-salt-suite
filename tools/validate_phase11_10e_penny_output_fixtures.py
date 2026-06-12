#!/usr/bin/env python3
"""Validate Phase 11.10E PennyShaped diagnostic output fixtures."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "11.10E"
VALID_STATUS = "PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID"
INVALID_STATUS = "PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_INVALID"
NEXT_PHASE = "PHASE11_10F_SPECIFY_PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION"
TAU = math.tau
REQUIRED_CAVEATS = {
    "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED",
    "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED",
    "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI",
    "IMPLEMENTATION_NOT_ALLOWED_IN_11_10E",
    "NOT_PHYSICALLY_VALIDATED",
    "NOT_LEGACY_EQUIVALENT",
    "NOT_ACTIVE_SIMULATION_CASE",
    "DIAGNOSTIC_ONLY",
}
REQUIRED_FIELDS = {
    "axisymmetric_angle_rad",
    "axisymmetric_basis",
    "volume_conversion_factor_1rad_to_2pi",
    "volume_multiplier",
    "volume_multiplier_semantics",
    "volume_multiplier_interpretation",
    "volume_multiplier_is_2pi",
    "fracture_volume_proxy_1rad_m3",
    "fracture_volume_equivalent_2pi_m3",
    "fracture_volume_equivalent_2pi_source",
    "solid_volume_1rad_m3",
    "solid_volume_equivalent_2pi_m3",
    "solid_volume_equivalent_2pi_source",
    "volume_interpretation",
    "physically_validated",
    "legacy_equivalent",
    "active_simulation_case",
    "diagnostic_only",
    "runtime_writer_implemented",
    "implementation_allowed",
    "source_contract",
    "source_phase",
    "recommended_next_phase",
}


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValueError(f"cannot parse boolean value {value!r}")


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cannot parse numeric value {value!r}") from exc


def load_json_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv_fixture(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"expected exactly one CSV row, got {len(rows)}")
    return rows[0]


def _check_required_fields(name: str, data: dict[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_FIELDS - data.keys())
    for field in missing:
        errors.append(f"{name} missing required field: {field}")


def _check_common_values(name: str, data: dict[str, Any], errors: list[str]) -> None:
    _check_required_fields(name, data, errors)
    try:
        angle = as_float(data.get("axisymmetric_angle_rad"))
        conversion = as_float(data.get("volume_conversion_factor_1rad_to_2pi"))
        volume_multiplier = as_float(data.get("volume_multiplier"))
        fracture_1rad = as_float(data.get("fracture_volume_proxy_1rad_m3"))
        fracture_2pi = as_float(data.get("fracture_volume_equivalent_2pi_m3"))
        solid_1rad = as_float(data.get("solid_volume_1rad_m3"))
        solid_2pi = as_float(data.get("solid_volume_equivalent_2pi_m3"))
    except ValueError as exc:
        errors.append(f"{name}: {exc}")
        return

    if not math.isclose(angle, 1.0, rel_tol=0.0, abs_tol=1e-12):
        errors.append(f"{name}: axisymmetric_angle_rad must be 1.0")
    if data.get("axisymmetric_basis") != "axisymmetric_1rad":
        errors.append(f"{name}: axisymmetric_basis must be axisymmetric_1rad")
    if not math.isclose(conversion, TAU, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name}: volume_conversion_factor_1rad_to_2pi must be 2pi")
    if math.isclose(volume_multiplier, TAU, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name}: volume_multiplier must not be interpreted as 2pi")
    if data.get("volume_multiplier_semantics") != "VOLUME_MULTIPLIER_EMPIRICAL":
        errors.append(f"{name}: volume_multiplier_semantics must be VOLUME_MULTIPLIER_EMPIRICAL")
    if data.get("volume_multiplier_interpretation") != "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI":
        errors.append(f"{name}: volume_multiplier_interpretation must be VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI")

    try:
        if as_bool(data.get("volume_multiplier_is_2pi")):
            errors.append(f"{name}: volume_multiplier_is_2pi must be false")
        if as_bool(data.get("physically_validated")):
            errors.append(f"{name}: physically_validated must be false")
        if as_bool(data.get("legacy_equivalent")):
            errors.append(f"{name}: legacy_equivalent must be false")
        if as_bool(data.get("active_simulation_case")):
            errors.append(f"{name}: active_simulation_case must be false")
        if not as_bool(data.get("diagnostic_only")):
            errors.append(f"{name}: diagnostic_only must be true")
        if as_bool(data.get("runtime_writer_implemented")):
            errors.append(f"{name}: runtime_writer_implemented must be false")
        if as_bool(data.get("implementation_allowed")):
            errors.append(f"{name}: implementation_allowed must be false")
    except ValueError as exc:
        errors.append(f"{name}: {exc}")

    if not math.isclose(fracture_2pi, fracture_1rad * TAU, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name}: fracture_volume_equivalent_2pi_m3 must equal fracture_volume_proxy_1rad_m3 * 2pi")
    if not math.isclose(solid_2pi, solid_1rad * TAU, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name}: solid_volume_equivalent_2pi_m3 must equal solid_volume_1rad_m3 * 2pi")
    if not data.get("fracture_volume_equivalent_2pi_source"):
        errors.append(f"{name}: fracture_volume_equivalent_2pi_source is required")
    if not data.get("solid_volume_equivalent_2pi_source"):
        errors.append(f"{name}: solid_volume_equivalent_2pi_source is required")
    if data.get("source_contract") != "docs/77_axisymmetric_1rad_2pi_output_contract.md":
        errors.append(f"{name}: source_contract must point to docs/77_axisymmetric_1rad_2pi_output_contract.md")
    if data.get("recommended_next_phase") != NEXT_PHASE:
        errors.append(f"{name}: recommended_next_phase must be {NEXT_PHASE}")


def _check_cross_fixture_consistency(json_data: dict[str, Any], csv_data: dict[str, Any], errors: list[str]) -> None:
    for field in REQUIRED_FIELDS:
        if field not in json_data or field not in csv_data:
            continue
        if field.endswith("_m3") or field in {
            "axisymmetric_angle_rad",
            "volume_conversion_factor_1rad_to_2pi",
            "volume_multiplier",
        }:
            if not math.isclose(as_float(json_data[field]), as_float(csv_data[field]), rel_tol=1e-12, abs_tol=1e-12):
                errors.append(f"CSV/JSON mismatch for numeric field: {field}")
        elif field in {
            "volume_multiplier_is_2pi",
            "physically_validated",
            "legacy_equivalent",
            "active_simulation_case",
            "diagnostic_only",
            "runtime_writer_implemented",
            "implementation_allowed",
        }:
            if as_bool(json_data[field]) != as_bool(csv_data[field]):
                errors.append(f"CSV/JSON mismatch for boolean field: {field}")
        elif str(json_data[field]) != str(csv_data[field]):
            errors.append(f"CSV/JSON mismatch for field: {field}")


def _check_metadata(metadata: dict[str, Any], errors: list[str]) -> None:
    if metadata.get("fixture_status") != VALID_STATUS:
        errors.append(f"metadata fixture_status must be {VALID_STATUS}")
    if metadata.get("implementation_status") != "FIXTURE_ONLY_NO_RUNTIME_WRITER":
        errors.append("metadata implementation_status must be FIXTURE_ONLY_NO_RUNTIME_WRITER")
    if metadata.get("contract_materialized") != "AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_MATERIALIZED_AS_FIXTURE":
        errors.append("metadata contract_materialized must record fixture materialization")
    try:
        if as_bool(metadata.get("volume_multiplier_is_2pi")):
            errors.append("metadata volume_multiplier_is_2pi must be false")
        if as_bool(metadata.get("physically_validated")):
            errors.append("metadata physically_validated must be false")
        if as_bool(metadata.get("legacy_equivalent")):
            errors.append("metadata legacy_equivalent must be false")
        if as_bool(metadata.get("active_simulation_case")):
            errors.append("metadata active_simulation_case must be false")
        if not as_bool(metadata.get("diagnostic_only")):
            errors.append("metadata diagnostic_only must be true")
        if as_bool(metadata.get("implementation_allowed")):
            errors.append("metadata implementation_allowed must be false")
    except ValueError as exc:
        errors.append(f"metadata: {exc}")

    caveats = set(metadata.get("required_caveats", []))
    missing_caveats = sorted(REQUIRED_CAVEATS - caveats)
    for caveat in missing_caveats:
        errors.append(f"metadata missing required caveat: {caveat}")
    forbidden = "\n".join(metadata.get("forbidden_interpretations", []))
    for phrase in ["volume_multiplier as 2pi", "physical validation", "legacy equivalence", "active simulation case"]:
        if phrase not in forbidden:
            errors.append(f"metadata forbidden_interpretations missing phrase: {phrase}")


def validate_fixtures(json_path: Path, csv_path: Path, metadata_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    json_data: dict[str, Any] = {}
    csv_data: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    try:
        json_data = load_json_fixture(json_path)
    except Exception as exc:  # noqa: BLE001 - validator must report all input failures.
        errors.append(f"could not read JSON fixture: {exc}")
    try:
        csv_data = load_csv_fixture(csv_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"could not read CSV fixture: {exc}")
    try:
        metadata = load_json_fixture(metadata_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"could not read metadata fixture: {exc}")

    if json_data:
        _check_common_values("json", json_data, errors)
        missing_caveats = sorted(REQUIRED_CAVEATS - set(json_data.get("required_caveats", [])))
        for caveat in missing_caveats:
            errors.append(f"json missing required caveat: {caveat}")
    if csv_data:
        _check_common_values("csv", csv_data, errors)
    if json_data and csv_data:
        _check_cross_fixture_consistency(json_data, csv_data, errors)
    if metadata:
        _check_metadata(metadata, errors)

    valid = not errors
    return {
        "phase": PHASE,
        "fixture_status": VALID_STATUS if valid else INVALID_STATUS,
        "json_fixture": str(json_path),
        "csv_fixture": str(csv_path),
        "metadata_fixture": str(metadata_path),
        "json_fixture_valid": bool(json_data) and not any(error.startswith("json") for error in errors),
        "csv_fixture_valid": bool(csv_data) and not any(error.startswith("csv") for error in errors),
        "metadata_fixture_valid": bool(metadata) and not any(error.startswith("metadata") for error in errors),
        "conversion_checks_passed": valid,
        "required_caveats_present": valid,
        "volume_multiplier_not_2pi": valid,
        "implementation_allowed": False,
        "recommended_next_phase": NEXT_PHASE,
        "errors": errors,
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10E PennyShaped Diagnostic Output Fixture Validation",
        "",
        f"- phase: `{result['phase']}`",
        f"- fixture_status: `{result['fixture_status']}`",
        f"- json_fixture_valid: `{str(result['json_fixture_valid']).lower()}`",
        f"- csv_fixture_valid: `{str(result['csv_fixture_valid']).lower()}`",
        f"- metadata_fixture_valid: `{str(result['metadata_fixture_valid']).lower()}`",
        f"- implementation_allowed: `{str(result['implementation_allowed']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Errors",
        "",
    ]
    if result["errors"]:
        lines.extend(f"- {error}" for error in result["errors"])
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Phase 11.10E PennyShaped diagnostic output fixtures."
    )
    parser.add_argument("--json-fixture", type=Path, required=True)
    parser.add_argument("--csv-fixture", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = validate_fixtures(args.json_fixture, args.csv_fixture, args.metadata)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"FIXTURE_STATUS={result['fixture_status']}")
    print(f"JSON_FIXTURE_VALID={str(result['json_fixture_valid']).lower()}")
    print(f"CSV_FIXTURE_VALID={str(result['csv_fixture_valid']).lower()}")
    print(f"METADATA_FIXTURE_VALID={str(result['metadata_fixture_valid']).lower()}")
    print(f"IMPLEMENTATION_ALLOWED={str(result['implementation_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
