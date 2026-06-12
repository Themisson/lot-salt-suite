#!/usr/bin/env python3
"""Check Phase 11.10G PennyShaped writer contract against fixtures."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "11.10G"
IMPLEMENTED_STATUS = "PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN"
PARTIAL_STATUS = "PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION_PARTIAL"
BLOCKED_STATUS = "PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION_BLOCKED"
INCONCLUSIVE_STATUS = "PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION_INCONCLUSIVE"
NEXT_PHASE = "PHASE11_10H_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER_GATE"
REQUIRED_CAVEATS = {
    "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED",
    "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED",
    "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI",
    "NOT_PHYSICALLY_VALIDATED",
    "NOT_LEGACY_EQUIVALENT",
    "NOT_ACTIVE_SIMULATION_CASE",
    "DIAGNOSTIC_ONLY",
}
REQUIRED_FIELDS = {
    "case_id",
    "phase",
    "track",
    "model",
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
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValueError(f"cannot parse boolean value {value!r}")


def as_float(value: Any) -> float:
    return float(value)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"expected exactly one CSV data row, got {len(rows)}")
    return rows[0]


def _check_fields(name: str, data: dict[str, Any], errors: list[str]) -> None:
    for field in sorted(REQUIRED_FIELDS - set(data)):
        errors.append(f"{name} missing required field: {field}")


def _check_booleans(name: str, data: dict[str, Any], errors: list[str]) -> None:
    checks = {
        "volume_multiplier_is_2pi": False,
        "physically_validated": False,
        "legacy_equivalent": False,
        "active_simulation_case": False,
        "diagnostic_only": True,
    }
    for field, expected in checks.items():
        try:
            actual = as_bool(data[field])
        except (KeyError, ValueError) as exc:
            errors.append(f"{name} invalid boolean {field}: {exc}")
            continue
        if actual is not expected:
            errors.append(f"{name} {field} must be {str(expected).lower()}")


def _check_values(name: str, data: dict[str, Any], errors: list[str]) -> None:
    try:
        factor = as_float(data["volume_conversion_factor_1rad_to_2pi"])
        fracture_1rad = as_float(data["fracture_volume_proxy_1rad_m3"])
        fracture_2pi = as_float(data["fracture_volume_equivalent_2pi_m3"])
        solid_1rad = as_float(data["solid_volume_1rad_m3"])
        solid_2pi = as_float(data["solid_volume_equivalent_2pi_m3"])
        volume_multiplier = as_float(data["volume_multiplier"])
    except (KeyError, ValueError) as exc:
        errors.append(f"{name} numeric parse failed: {exc}")
        return

    if not math.isclose(factor, math.tau, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name} conversion factor must be 2pi")
    if math.isclose(volume_multiplier, math.tau, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name} volume_multiplier must not be 2pi")
    if data.get("volume_multiplier_semantics") != "VOLUME_MULTIPLIER_EMPIRICAL":
        errors.append(f"{name} volume_multiplier_semantics mismatch")
    if data.get("volume_multiplier_interpretation") != "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI":
        errors.append(f"{name} volume_multiplier_interpretation mismatch")
    if not math.isclose(fracture_2pi, fracture_1rad * factor, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name} fracture 2pi volume must equal 1rad * factor")
    if not math.isclose(solid_2pi, solid_1rad * factor, rel_tol=1e-12, abs_tol=1e-12):
        errors.append(f"{name} solid 2pi volume must equal 1rad * factor")
    if not data.get("fracture_volume_equivalent_2pi_source"):
        errors.append(f"{name} fracture 2pi source is required")
    if not data.get("solid_volume_equivalent_2pi_source"):
        errors.append(f"{name} solid 2pi source is required")


def check_fixture_contract(fixture_json: Path, fixture_csv: Path) -> dict[str, Any]:
    errors: list[str] = []
    json_data = load_json(fixture_json)
    csv_data = load_csv_row(fixture_csv)

    _check_fields("json", json_data, errors)
    _check_fields("csv", csv_data, errors)
    _check_booleans("json", json_data, errors)
    _check_booleans("csv", csv_data, errors)
    _check_values("json", json_data, errors)
    _check_values("csv", csv_data, errors)

    caveats = set(json_data.get("required_caveats", []))
    for caveat in sorted(REQUIRED_CAVEATS - caveats):
        errors.append(f"json missing writer-required caveat: {caveat}")

    for field in sorted(REQUIRED_FIELDS):
        if field not in json_data or field not in csv_data:
            continue
        if field.endswith("_m3") or field in {
            "axisymmetric_angle_rad",
            "volume_conversion_factor_1rad_to_2pi",
            "volume_multiplier",
        }:
            if not math.isclose(as_float(json_data[field]), as_float(csv_data[field]), rel_tol=1e-12, abs_tol=1e-12):
                errors.append(f"CSV/JSON numeric mismatch: {field}")
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
                errors.append(f"CSV/JSON boolean mismatch: {field}")
        elif str(json_data[field]) != str(csv_data[field]):
            errors.append(f"CSV/JSON text mismatch: {field}")

    return {
        "fixture_contract_valid": not errors,
        "fixture_json": str(fixture_json),
        "fixture_csv": str(fixture_csv),
        "errors": errors,
    }


def build_result(fixture_json: Path, fixture_csv: Path) -> dict[str, Any]:
    try:
        fixture_check = check_fixture_contract(fixture_json, fixture_csv)
    except Exception as exc:  # noqa: BLE001 - command-line audit reports failures as JSON.
        return {
            "phase": PHASE,
            "writer_implementation_status": BLOCKED_STATUS,
            "fixture_contract_valid": False,
            "runtime_execution_allowed": False,
            "buz29_executed": False,
            "physically_validated": False,
            "legacy_equivalent": False,
            "active_simulation_case": False,
            "cpp_runtime_verification": "CATCH2_WRITER_TESTS_REQUIRED",
            "recommended_next_phase": "PHASE11_10G_FIX_WRITER_OR_FIXTURES",
            "errors": [str(exc)],
        }

    status = IMPLEMENTED_STATUS if fixture_check["fixture_contract_valid"] else PARTIAL_STATUS
    return {
        "phase": PHASE,
        "writer_implementation_status": status,
        "fixture_contract_valid": fixture_check["fixture_contract_valid"],
        "runtime_execution_allowed": False,
        "buz29_executed": False,
        "physically_validated": False,
        "legacy_equivalent": False,
        "active_simulation_case": False,
        "cpp_runtime_verification": "CATCH2_WRITER_TESTS_ARE_SOURCE_OF_RUNTIME_VERIFICATION",
        "fixture_json": fixture_check["fixture_json"],
        "fixture_csv": fixture_check["fixture_csv"],
        "classification_options": [
            IMPLEMENTED_STATUS,
            PARTIAL_STATUS,
            BLOCKED_STATUS,
            INCONCLUSIVE_STATUS,
        ],
        "recommended_next_phase": NEXT_PHASE,
        "errors": fixture_check["errors"],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10G PennyShaped Writer Fixture Check",
        "",
        f"- phase: `{result['phase']}`",
        f"- writer_implementation_status: `{result['writer_implementation_status']}`",
        f"- fixture_contract_valid: `{str(result['fixture_contract_valid']).lower()}`",
        f"- runtime_execution_allowed: `{str(result['runtime_execution_allowed']).lower()}`",
        f"- buz29_executed: `{str(result['buz29_executed']).lower()}`",
        f"- physically_validated: `{str(result['physically_validated']).lower()}`",
        f"- legacy_equivalent: `{str(result['legacy_equivalent']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {error}" for error in result["errors"] or ["none"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Phase 11.10G PennyShaped diagnostic writer against fixture contract."
    )
    parser.add_argument("--fixture-json", type=Path, required=True)
    parser.add_argument("--fixture-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = build_result(args.fixture_json, args.fixture_csv)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"WRITER_IMPLEMENTATION_STATUS={result['writer_implementation_status']}")
    print(f"FIXTURE_CONTRACT_VALID={str(result['fixture_contract_valid']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED={str(result['runtime_execution_allowed']).lower()}")
    print(f"BUZ29_EXECUTED={str(result['buz29_executed']).lower()}")
    print(f"PHYSICALLY_VALIDATED={str(result['physically_validated']).lower()}")
    print(f"LEGACY_EQUIVALENT={str(result['legacy_equivalent']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0 if result["writer_implementation_status"] == IMPLEMENTED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
