#!/usr/bin/env python3
"""Specify the future opt-in PennyShaped diagnostic writer."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "11.10F"
SPECIFIED_STATUS = "PENNY_DIAGNOSTIC_WRITER_SPECIFIED"
PARTIAL_STATUS = "PENNY_DIAGNOSTIC_WRITER_SPEC_PARTIAL"
BLOCKED_STATUS = "PENNY_DIAGNOSTIC_WRITER_SPEC_BLOCKED"
INCONCLUSIVE_STATUS = "PENNY_DIAGNOSTIC_WRITER_SPEC_INCONCLUSIVE"
NEXT_IMPLEMENT = "PHASE11_10G_IMPLEMENT_PENNY_DIAGNOSTIC_WRITER_OPT_IN"
NEXT_COMPLETE = "PHASE11_10G_COMPLETE_WRITER_SPEC_OR_FIXTURES"
NEXT_RECONCILE = "PHASE11_10G_RECONCILE_CONTRACT_AND_FIXTURES"

REQUIRED_OUTPUTS = [
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
]

REQUIRED_METADATA = [
    "phase",
    "status",
    "fixture_status",
    "implementation_status",
    "contract_materialized",
    "axisymmetric_angle_rad",
    "axisymmetric_basis",
    "volume_conversion_factor_1rad_to_2pi",
    "volume_multiplier_semantics",
    "volume_multiplier_interpretation",
    "volume_multiplier_is_2pi",
    "json_fixture",
    "csv_fixture",
    "source_contract",
    "physically_validated",
    "legacy_equivalent",
    "active_simulation_case",
    "diagnostic_only",
    "implementation_allowed",
    "runtime_writer_implemented",
    "recommended_next_phase",
    "required_caveats",
    "forbidden_interpretations",
]

REQUIRED_CAVEATS = [
    "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED",
    "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED",
    "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI",
    "IMPLEMENTATION_NOT_ALLOWED_IN_11_10E",
    "NOT_PHYSICALLY_VALIDATED",
    "NOT_LEGACY_EQUIVALENT",
    "NOT_ACTIVE_SIMULATION_CASE",
    "DIAGNOSTIC_ONLY",
]

FUTURE_WRITER_CAVEATS = [
    "IMPLEMENTATION_NOT_ALLOWED_IN_11_10F",
    "RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F",
]

CONVERSION_RULES = [
    "fracture_volume_equivalent_2pi_m3 = fracture_volume_proxy_1rad_m3 * 2pi only when the 1rad source is preserved and source/caveat is present.",
    "solid_volume_equivalent_2pi_m3 = solid_volume_1rad_m3 * 2pi only when the 1rad source is preserved and source/caveat is present.",
    "volume_multiplier remains empirical and must not be used as the 1rad to 2pi geometric conversion factor.",
    "Any 2pi equivalent output must preserve the corresponding *_1rad_m3 field.",
]

FORBIDDEN_INTERPRETATIONS = [
    "Do not implement or infer runtime writer behavior in Phase 11.10F.",
    "Do not treat volume_multiplier as 2pi.",
    "Do not treat fracture_volume_proxy_1rad_m3 as physically validated total fracture volume.",
    "Do not emit a 2pi equivalent without source/caveat.",
    "Do not declare BUZ29-PENNY physical validation.",
    "Do not declare LOT_Tese legacy equivalence.",
    "Do not treat this specification as an active simulation case.",
]


def _read_existing_text(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path, label: str) -> dict[str, Any]:
    return json.loads(_read_existing_text(path, label))


def load_csv_row(path: Path) -> dict[str, str]:
    _read_existing_text(path, "fixture CSV")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"fixture CSV must contain exactly one data row, got {len(rows)}")
    return rows[0]


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
    raise ValueError(f"cannot parse boolean value {value!r}")


def as_float(value: Any) -> float:
    return float(value)


def _missing_fields(data: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if field not in data]


def analyze_fixtures(
    fixture_json: Path,
    fixture_csv: Path,
    fixture_metadata: Path,
) -> dict[str, Any]:
    json_data = load_json(fixture_json, "fixture JSON")
    csv_data = load_csv_row(fixture_csv)
    metadata = load_json(fixture_metadata, "fixture metadata")

    errors: list[str] = []
    warnings: list[str] = []

    for field in _missing_fields(json_data, REQUIRED_OUTPUTS):
        errors.append(f"JSON fixture missing required output: {field}")
    for field in _missing_fields(csv_data, REQUIRED_OUTPUTS):
        errors.append(f"CSV fixture missing required output: {field}")
    for field in _missing_fields(metadata, REQUIRED_METADATA):
        errors.append(f"metadata fixture missing required field: {field}")

    if errors:
        return {
            "fixture_contract_valid": False,
            "json_data": json_data,
            "csv_data": csv_data,
            "metadata": metadata,
            "errors": errors,
            "warnings": warnings,
        }

    try:
        angle = as_float(json_data["axisymmetric_angle_rad"])
        factor = as_float(json_data["volume_conversion_factor_1rad_to_2pi"])
        fracture_1rad = as_float(json_data["fracture_volume_proxy_1rad_m3"])
        fracture_2pi = as_float(json_data["fracture_volume_equivalent_2pi_m3"])
        solid_1rad = as_float(json_data["solid_volume_1rad_m3"])
        solid_2pi = as_float(json_data["solid_volume_equivalent_2pi_m3"])
        volume_multiplier = as_float(json_data["volume_multiplier"])
    except (TypeError, ValueError) as exc:
        errors.append(f"numeric field parse failed: {exc}")
        angle = factor = fracture_1rad = fracture_2pi = solid_1rad = solid_2pi = volume_multiplier = math.nan

    if not math.isclose(angle, 1.0, rel_tol=0.0, abs_tol=1e-12):
        errors.append("axisymmetric_angle_rad must be 1.0")
    if not math.isclose(factor, math.tau, rel_tol=1e-12, abs_tol=1e-12):
        errors.append("volume_conversion_factor_1rad_to_2pi must be 2pi")
    if math.isclose(volume_multiplier, math.tau, rel_tol=1e-12, abs_tol=1e-12):
        errors.append("volume_multiplier must not be interpreted as 2pi")
    if as_bool(json_data["volume_multiplier_is_2pi"]):
        errors.append("volume_multiplier_is_2pi must be false")
    if as_bool(json_data["physically_validated"]):
        errors.append("physically_validated must be false")
    if as_bool(json_data["legacy_equivalent"]):
        errors.append("legacy_equivalent must be false")
    if as_bool(json_data["active_simulation_case"]):
        errors.append("active_simulation_case must be false")
    if not as_bool(json_data["diagnostic_only"]):
        errors.append("diagnostic_only must be true")
    if as_bool(json_data["implementation_allowed"]):
        errors.append("implementation_allowed must be false")

    if not math.isclose(fracture_2pi, fracture_1rad * math.tau, rel_tol=1e-12, abs_tol=1e-12):
        errors.append("fracture_volume_equivalent_2pi_m3 must equal fracture_volume_proxy_1rad_m3 * 2pi")
    if not math.isclose(solid_2pi, solid_1rad * math.tau, rel_tol=1e-12, abs_tol=1e-12):
        errors.append("solid_volume_equivalent_2pi_m3 must equal solid_volume_1rad_m3 * 2pi")

    for field in REQUIRED_OUTPUTS:
        if field in json_data and field in csv_data and str(json_data[field]).lower() != str(csv_data[field]).lower():
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
            else:
                errors.append(f"CSV/JSON mismatch for field: {field}")

    missing_caveats = sorted(set(REQUIRED_CAVEATS) - set(metadata["required_caveats"]))
    for caveat in missing_caveats:
        errors.append(f"metadata missing caveat: {caveat}")
    forbidden_text = "\n".join(metadata["forbidden_interpretations"])
    for phrase in ["volume_multiplier as 2pi", "physical validation", "legacy equivalence", "active simulation case"]:
        if phrase not in forbidden_text:
            warnings.append(f"metadata forbidden_interpretations should mention: {phrase}")

    return {
        "fixture_contract_valid": not errors,
        "json_data": json_data,
        "csv_data": csv_data,
        "metadata": metadata,
        "errors": errors,
        "warnings": warnings,
    }


def decide_status(analysis: dict[str, Any]) -> tuple[str, str]:
    if analysis["fixture_contract_valid"]:
        return SPECIFIED_STATUS, NEXT_IMPLEMENT
    errors = "\n".join(analysis["errors"])
    if "missing required" in errors:
        return PARTIAL_STATUS, NEXT_COMPLETE
    if "must not" in errors or "mismatch" in errors or "2pi" in errors:
        return BLOCKED_STATUS, NEXT_RECONCILE
    return INCONCLUSIVE_STATUS, NEXT_COMPLETE


def build_writer_spec(
    fixture_json: Path,
    fixture_csv: Path,
    fixture_metadata: Path,
) -> dict[str, Any]:
    analysis = analyze_fixtures(fixture_json, fixture_csv, fixture_metadata)
    status, next_phase = decide_status(analysis)
    metadata = analysis["metadata"]

    return {
        "phase": PHASE,
        "writer_spec_status": status,
        "implementation_allowed": False,
        "runtime_execution_allowed": False,
        "requires_cpp_implementation_future": True,
        "fixture_contract_valid": analysis["fixture_contract_valid"],
        "source": "PHASE11_10D_11_10E_FIXTURE_CONTRACT",
        "fixture_json": str(fixture_json),
        "fixture_csv": str(fixture_csv),
        "fixture_metadata": str(fixture_metadata),
        "required_outputs": REQUIRED_OUTPUTS,
        "required_metadata": REQUIRED_METADATA,
        "required_caveats": list(metadata.get("required_caveats", REQUIRED_CAVEATS)) + FUTURE_WRITER_CAVEATS,
        "conversion_rules": CONVERSION_RULES,
        "forbidden_interpretations": FORBIDDEN_INTERPRETATIONS,
        "conceptual_cpp_api": {
            "input": "PennyDiagnosticOutputInput",
            "record": "PennyDiagnosticOutputRecord",
            "future_files": [
                "include/io/PennyShapedDiagnosticWriter.hpp",
                "src/io/PennyShapedDiagnosticWriter.cpp",
                "tests/cpp/test_penny_shaped_diagnostic_writer.cpp",
            ],
        },
        "json_output_contract": {
            "single_record": True,
            "must_preserve_1rad_fields": True,
            "must_include_2pi_sources": True,
        },
        "csv_output_contract": {
            "one_row_per_record": True,
            "headers_match_required_outputs": True,
            "boolean_values_lowercase": True,
        },
        "errors": analysis["errors"],
        "warnings": analysis["warnings"],
        "recommended_next_phase": next_phase,
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10F PennyShaped Diagnostic Writer Specification",
        "",
        f"- phase: `{spec['phase']}`",
        f"- writer_spec_status: `{spec['writer_spec_status']}`",
        f"- implementation_allowed: `{str(spec['implementation_allowed']).lower()}`",
        f"- runtime_execution_allowed: `{str(spec['runtime_execution_allowed']).lower()}`",
        f"- requires_cpp_implementation_future: `{str(spec['requires_cpp_implementation_future']).lower()}`",
        f"- fixture_contract_valid: `{str(spec['fixture_contract_valid']).lower()}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Required Outputs",
        "",
    ]
    lines.extend(f"- `{field}`" for field in spec["required_outputs"])
    lines.extend(["", "## Required Metadata", ""])
    lines.extend(f"- `{field}`" for field in spec["required_metadata"])
    lines.extend(["", "## Required Caveats", ""])
    lines.extend(f"- `{caveat}`" for caveat in spec["required_caveats"])
    lines.extend(["", "## Conversion Rules", ""])
    lines.extend(f"- {rule}" for rule in spec["conversion_rules"])
    lines.extend(["", "## Forbidden Interpretations", ""])
    lines.extend(f"- {item}" for item in spec["forbidden_interpretations"])
    lines.extend(["", "## Future C++ Files", ""])
    lines.extend(f"- `{item}`" for item in spec["conceptual_cpp_api"]["future_files"])
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {item}" for item in spec["errors"] or ["none"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in spec["warnings"] or ["none"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10F future opt-in PennyShaped diagnostic writer."
    )
    parser.add_argument("--fixture-json", type=Path, required=True)
    parser.add_argument("--fixture-csv", type=Path, required=True)
    parser.add_argument("--fixture-metadata", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    spec = build_writer_spec(args.fixture_json, args.fixture_csv, args.fixture_metadata)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(spec, args.output_md)

    print(f"PHASE={spec['phase']}")
    print(f"WRITER_SPEC_STATUS={spec['writer_spec_status']}")
    print(f"IMPLEMENTATION_ALLOWED={str(spec['implementation_allowed']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED={str(spec['runtime_execution_allowed']).lower()}")
    print(f"REQUIRES_CPP_IMPLEMENTATION_FUTURE={str(spec['requires_cpp_implementation_future']).lower()}")
    print(f"FIXTURE_CONTRACT_VALID={str(spec['fixture_contract_valid']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0 if spec["writer_spec_status"] == SPECIFIED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
