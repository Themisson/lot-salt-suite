#!/usr/bin/env python3
"""Specify the Phase 11.10D axisymmetric 1rad to 2pi output contract."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


PHASE = "11.10D"
CONTRACT_STATUS = "AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED"
NEXT_PHASE = "PHASE11_10E_DEFINE_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES"
AXISYMMETRIC_CAVEAT = "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED"
FUTURE_OUTPUT_REQUIREMENT = "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED"
VOLUME_MULTIPLIER_SEMANTICS = "VOLUME_MULTIPLIER_EMPIRICAL"


def field_contract_row(
    name: str,
    unit: str,
    angular_basis: str,
    meaning: str,
    required: bool,
    source_required: bool = False,
    allowed_values: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "unit": unit,
        "angular_basis": angular_basis,
        "meaning": meaning,
        "required": required,
        "source_required": source_required,
        "allowed_values": allowed_values or [],
    }


def build_field_contract() -> list[dict[str, Any]]:
    return [
        field_contract_row(
            "axisymmetric_angle_rad",
            "rad",
            "metadata",
            "Internal angular basis of the axisymmetric diagnostic formulation. Initial expected value is 1.0.",
            True,
        ),
        field_contract_row(
            "axisymmetric_basis",
            "text",
            "metadata",
            "Name of the internal angular basis; expected value axisymmetric_1rad.",
            True,
            allowed_values=["axisymmetric_1rad"],
        ),
        field_contract_row(
            "volume_multiplier",
            "dimensionless",
            "empirical",
            "Legacy-inspired diagnostic multiplier carried by the adapter. It is not the 2pi geometric conversion factor.",
            True,
        ),
        field_contract_row(
            "volume_multiplier_semantics",
            "text",
            "metadata",
            "Semantic classification of volume_multiplier.",
            True,
            allowed_values=[VOLUME_MULTIPLIER_SEMANTICS],
        ),
        field_contract_row(
            "fracture_volume_proxy_1rad_m3",
            "m3",
            "axisymmetric_1rad_internal",
            "Diagnostic fracture-volume proxy in the internal 1 rad basis.",
            True,
        ),
        field_contract_row(
            "fracture_volume_equivalent_2pi_m3",
            "m3",
            "axisymmetric_2pi_equivalent",
            "2pi equivalent computed from the 1 rad proxy only when the field is declared geometrically integrable.",
            False,
            source_required=True,
        ),
        field_contract_row(
            "fracture_volume_equivalent_2pi_source",
            "text",
            "metadata",
            "Source/caveat for fracture_volume_equivalent_2pi_m3.",
            True,
            allowed_values=[
                "computed_from_1rad_proxy",
                "not_applicable",
                "blocked_proxy_only",
                "future_runtime_field",
            ],
        ),
        field_contract_row(
            "solid_volume_1rad_m3",
            "m3",
            "axisymmetric_1rad_internal",
            "Solid/domain volume in the internal 1 rad basis, when applicable.",
            False,
        ),
        field_contract_row(
            "solid_volume_equivalent_2pi_m3",
            "m3",
            "axisymmetric_2pi_equivalent",
            "Total equivalent solid/domain volume over 2pi, when applicable.",
            False,
            source_required=True,
        ),
        field_contract_row(
            "volume_conversion_factor_1rad_to_2pi",
            "dimensionless",
            "geometric_conversion",
            "Geometric factor used to convert integrable 1 rad quantities to 2pi equivalents.",
            True,
        ),
        field_contract_row(
            "volume_interpretation",
            "text",
            "metadata",
            "Explicit interpretation of volumetric fields.",
            True,
            allowed_values=[
                "axisymmetric_1rad_internal",
                "axisymmetric_1rad_with_2pi_equivalent",
                "proxy_only_not_total_volume",
                "empirical_multiplier_applied",
                "not_physically_validated",
            ],
        ),
        field_contract_row(
            "physically_validated",
            "boolean",
            "metadata",
            "Whether the output has physical validation. Must remain false for this diagnostic contract.",
            True,
        ),
        field_contract_row(
            "legacy_equivalent",
            "boolean",
            "metadata",
            "Whether the output is strict legacy-equivalent. Must remain false until proven.",
            True,
        ),
        field_contract_row(
            "diagnostic_only",
            "boolean",
            "metadata",
            "Whether the output is diagnostic-only.",
            True,
        ),
    ]


def build_conversion_rules() -> list[dict[str, str]]:
    return [
        {
            "id": "RULE_1_INTEGRABLE_1RAD_TO_2PI",
            "rule": "If a volumetric field is declared as *_1rad_m3 and is geometrically integrable, *_equivalent_2pi_m3 = *_1rad_m3 * 2pi.",
        },
        {
            "id": "RULE_2_PROXY_NO_AUTOMATIC_2PI",
            "rule": "If a volumetric field is an empirical proxy, do not generate an automatic 2pi equivalent without a source/caveat field.",
        },
        {
            "id": "RULE_3_VOLUME_MULTIPLIER_NOT_2PI",
            "rule": "volume_multiplier is not equal to 2pi unless a future phase renames and redefines it semantically.",
        },
        {
            "id": "RULE_4_2PI_SOURCE_REQUIRED",
            "rule": "Every 2pi equivalent output must report a source field.",
        },
        {
            "id": "RULE_5_PRESERVE_1RAD_ORIGIN",
            "rule": "Any output with a total 2pi equivalent must preserve the 1rad source value.",
        },
        {
            "id": "RULE_6_REPORT_ANGULAR_METADATA",
            "rule": "Reports must declare axisymmetric_angle_rad, volume_conversion_factor_1rad_to_2pi and volume_interpretation.",
        },
    ]


def build_contract(mode: str = "complete") -> dict[str, Any]:
    field_contract = build_field_contract()
    conversion_rules = build_conversion_rules()
    forbidden_interpretations = [
        "Do not treat volume_multiplier as 2pi.",
        "Do not treat fracture_volume_proxy_1rad_m3 as a physically validated total fracture volume.",
        "Do not drop the 1rad source value when reporting a 2pi equivalent.",
        "Do not declare BUZ29-PENNY physical validation from this contract.",
        "Do not declare legacy equivalence from this contract.",
    ]
    required_caveats = [
        AXISYMMETRIC_CAVEAT,
        FUTURE_OUTPUT_REQUIREMENT,
        "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI",
        "IMPLEMENTATION_NOT_ALLOWED_IN_11_10D",
        "NOT_PHYSICALLY_VALIDATED",
        "NOT_LEGACY_EQUIVALENT",
        "DIAGNOSTIC_ONLY",
    ]

    missing: list[str] = []
    if mode == "missing_volume_multiplier_semantics":
        field_contract = [row for row in field_contract if row["name"] != "volume_multiplier_semantics"]
        missing.append("volume_multiplier_semantics")
    elif mode == "conflict":
        forbidden_interpretations = []
        missing.append("forbidden_interpretations")

    required_fields = {
        "axisymmetric_angle_rad",
        "axisymmetric_basis",
        "volume_multiplier",
        "volume_multiplier_semantics",
        "fracture_volume_proxy_1rad_m3",
        "fracture_volume_equivalent_2pi_m3",
        "fracture_volume_equivalent_2pi_source",
        "solid_volume_1rad_m3",
        "solid_volume_equivalent_2pi_m3",
        "volume_conversion_factor_1rad_to_2pi",
        "volume_interpretation",
        "physically_validated",
        "legacy_equivalent",
        "diagnostic_only",
    }
    present_fields = {row["name"] for row in field_contract}
    missing.extend(sorted(required_fields - present_fields))

    if "volume_multiplier_semantics" in missing:
        contract_status = "AXISYMMETRIC_OUTPUT_CONTRACT_PARTIAL"
        recommended_next_phase = "PHASE11_10E_RESOLVE_VOLUME_MULTIPLIER_SEMANTICS"
    elif missing:
        contract_status = "AXISYMMETRIC_OUTPUT_CONTRACT_BLOCKED"
        recommended_next_phase = "PHASE11_10E_RECONCILE_OUTPUT_CONTRACT_WITH_EXISTING_API"
    else:
        contract_status = CONTRACT_STATUS
        recommended_next_phase = NEXT_PHASE

    return {
        "phase": PHASE,
        "contract_status": contract_status,
        "axisymmetric_angle_rad": 1.0,
        "axisymmetric_basis": "axisymmetric_1rad",
        "volume_conversion_factor_1rad_to_2pi": math.tau,
        "volume_multiplier_semantics": VOLUME_MULTIPLIER_SEMANTICS,
        "field_contract": field_contract,
        "conversion_rules": conversion_rules,
        "forbidden_interpretations": forbidden_interpretations,
        "required_caveats": required_caveats,
        "missing_contract_items": missing,
        "implementation_allowed": False,
        "physical_validation": False,
        "legacy_equivalence": False,
        "diagnostic_only": True,
        "recommended_next_phase": recommended_next_phase,
    }


def write_markdown(contract: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10D Axisymmetric 1rad to 2pi Output Contract",
        "",
        f"- phase: `{contract['phase']}`",
        f"- contract_status: `{contract['contract_status']}`",
        f"- axisymmetric_angle_rad: `{contract['axisymmetric_angle_rad']}`",
        f"- volume_conversion_factor_1rad_to_2pi: `{contract['volume_conversion_factor_1rad_to_2pi']}`",
        f"- volume_multiplier_semantics: `{contract['volume_multiplier_semantics']}`",
        f"- implementation_allowed: `{str(contract['implementation_allowed']).lower()}`",
        f"- recommended_next_phase: `{contract['recommended_next_phase']}`",
        "",
        "## Field Contract",
        "",
        "| Field | Unit | Angular basis | Required | Source required | Meaning |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in contract["field_contract"]:
        lines.append(
            f"| `{row['name']}` | `{row['unit']}` | `{row['angular_basis']}` | `{row['required']}` | `{row['source_required']}` | {row['meaning']} |"
        )
    lines.extend(["", "## Conversion Rules", ""])
    lines.extend(f"- `{row['id']}`: {row['rule']}" for row in contract["conversion_rules"])
    lines.extend(["", "## Forbidden Interpretations", ""])
    lines.extend(f"- {item}" for item in contract["forbidden_interpretations"])
    lines.extend(["", "## Required Caveats", ""])
    lines.extend(f"- `{item}`" for item in contract["required_caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10D axisymmetric 1rad to 2pi output contract."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument(
        "--fixture-mode",
        choices=["complete", "missing_volume_multiplier_semantics", "conflict"],
        default="complete",
        help="Test hook for contract decision branches.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    contract = build_contract(args.fixture_mode)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(contract, args.output_md)

    print(f"PHASE={contract['phase']}")
    print(f"CONTRACT_STATUS={contract['contract_status']}")
    print(f"AXISYMMETRIC_ANGLE_RAD={contract['axisymmetric_angle_rad']}")
    print(f"VOLUME_CONVERSION_FACTOR_1RAD_TO_2PI={contract['volume_conversion_factor_1rad_to_2pi']}")
    print(f"VOLUME_MULTIPLIER_SEMANTICS={contract['volume_multiplier_semantics']}")
    print(f"IMPLEMENTATION_ALLOWED={str(contract['implementation_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={contract['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
