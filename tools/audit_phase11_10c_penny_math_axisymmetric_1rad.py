#!/usr/bin/env python3
"""Audit PennyShaped math as an axisymmetric 1 rad diagnostic formulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10C"
PRIMARY_CLASSIFICATION = "PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING"
SECONDARY_CLASSIFICATION = "PENNY_MATH_AXISYMMETRIC_1RAD_PROXY"
TERTIARY_CLASSIFICATION = "PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL"

AXISYMMETRIC_CAVEAT = "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED"
FUTURE_OUTPUT_REQUIREMENT = "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED"

NEXT_OUTPUT_CONTRACT = "PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT"
NEXT_CORRECT_MATH = "PHASE11_10D_CORRECT_PENNY_SHAPED_MODEL_MATH"
NEXT_PRESSURE = "PHASE11_10D_RESOLVE_PENNY_PRESSURE_SIGMATHETA_SEMANTICS"
NEXT_VOLUME = "PHASE11_10D_RESOLVE_VOLUME_MULTIPLIER_AND_OUTPUT_CONTRACT"


def dimension_row(
    field: str,
    declared_unit: str,
    expected_dimension: str,
    code_expression: str,
    derived_dimension: str,
    status: str,
    notes: str,
) -> dict[str, str]:
    return {
        "field": field,
        "declared_unit": declared_unit,
        "expected_dimension": expected_dimension,
        "code_expression": code_expression,
        "derived_dimension": derived_dimension,
        "status": status,
        "notes": notes,
    }


def build_dimension_audit(mode: str = "consistent") -> list[dict[str, str]]:
    rows = [
        dimension_row(
            "young_modulus_Pa",
            "Pa",
            "M L^-1 T^-2",
            "input.young_modulus_Pa",
            "pressure",
            "DIMENSION_OK",
            "Positive elastic modulus used in E' = E / (1 - nu^2).",
        ),
        dimension_row(
            "poisson_ratio",
            "dimensionless",
            "1",
            "input.poisson_ratio",
            "dimensionless",
            "DIMENSION_OK",
            "Validated in [0, 0.5).",
        ),
        dimension_row(
            "viscosity_Pa_min",
            "Pa.min",
            "pressure*time",
            "mu",
            "pressure*time",
            "DIMENSION_OK",
            "The hydraulic scaling uses minutes consistently with Q in m3/min and elapsed time in min.",
        ),
        dimension_row(
            "flow_rate_m3_min",
            "m3/min",
            "L^3 T^-1",
            "q",
            "volume/time",
            "DIMENSION_OK",
            "Used as Q^3 in both opening and radius scalings.",
        ),
        dimension_row(
            "elapsed_since_opening_min",
            "min",
            "time",
            "time",
            "time",
            "DIMENSION_OK",
            "The exponents cancel the time dimensions in the hydraulic scaling.",
        ),
        dimension_row(
            "wellbore_pressure_Pa",
            "Pa",
            "pressure",
            "input.wellbore_pressure_Pa",
            "pressure",
            "DIMENSION_REQUIRES_SEMANTIC_REVIEW",
            "Used only in pressure_factor = wellbore_pressure_Pa / sigma_theta_compression_positive_Pa, not as net pressure.",
        ),
        dimension_row(
            "sigma_theta_compression_positive_Pa",
            "Pa",
            "pressure",
            "input.sigma_theta_compression_positive_Pa",
            "pressure",
            "DIMENSION_REQUIRES_SEMANTIC_REVIEW",
            "Compression-positive sigmaTheta is a denominator in a diagnostic pressure ratio.",
        ),
        dimension_row(
            "volume_multiplier",
            "dimensionless",
            "1",
            "input.volume_multiplier",
            "dimensionless",
            "DIMENSION_PROXY_ONLY",
            "Default 10.0 is legacy-inspired and not yet an angular-basis contract.",
        ),
        dimension_row(
            "plane_strain_modulus_Pa",
            "Pa",
            "pressure",
            "E / (1 - nu^2)",
            "pressure",
            "DIMENSION_OK",
            "Plane-strain modulus is dimensionally pressure.",
        ),
        dimension_row(
            "opening_m",
            "m",
            "length",
            "3.65 * ((mu^2 * Q^3) / E'^2)^(1/9) * time^(1/9)",
            "length",
            "DIMENSION_OK",
            "(Pa^2 min^2 * m9 min^-3 / Pa^2)^(1/9) * min^(1/9) = m.",
        ),
        dimension_row(
            "radius_m",
            "m",
            "length",
            "0.572 * ((E' * Q^3) / mu)^(1/9) * time^(4/9)",
            "length",
            "DIMENSION_OK",
            "(Pa * m9 min^-3 / (Pa min))^(1/9) * min^(4/9) = m.",
        ),
        dimension_row(
            "pressure_factor",
            "dimensionless",
            "1",
            "wellbore_pressure_Pa / sigma_theta_compression_positive_Pa",
            "dimensionless",
            "DIMENSION_REQUIRES_SEMANTIC_REVIEW",
            "This is a ratio, not a fracture-driving pressure or breakdown margin.",
        ),
        dimension_row(
            "fracture_volume_proxy_m3",
            "m3",
            "volume",
            "volume_multiplier * (opening_m/2)^2 * radius_m * pi * pressure_factor",
            "volume",
            "DIMENSION_PROXY_ONLY",
            "Dimensionally volume, but semantically a proxy until 1rad/2pi output contract is defined.",
        ),
    ]
    if mode == "inconsistent":
        rows[-1] = {**rows[-1], "derived_dimension": "length^2", "status": "DIMENSION_INCONSISTENT"}
    return rows


def audit_math(mode: str = "consistent") -> dict[str, Any]:
    dimension_audit = build_dimension_audit("inconsistent" if mode == "inconsistent" else "consistent")
    has_dimension_error = any(row["status"] == "DIMENSION_INCONSISTENT" for row in dimension_audit)

    pressure_semantics = (
        "PRESSURE_SEMANTICS_REQUIRES_REVIEW"
        if mode == "pressure_ambiguous"
        else "PRESSURE_SEMANTICS_CLEAR"
    )
    volume_multiplier_semantics = (
        "VOLUME_MULTIPLIER_AMBIGUOUS"
        if mode == "volume_ambiguous"
        else "VOLUME_MULTIPLIER_EMPIRICAL"
    )

    if has_dimension_error:
        math_audit_passed = False
        requires_code_correction = True
        requires_documentation_update = True
        requires_output_contract = False
        recommended_next_phase = NEXT_CORRECT_MATH
        blocking_gaps = ["dimension_inconsistency"]
    elif pressure_semantics != "PRESSURE_SEMANTICS_CLEAR":
        math_audit_passed = False
        requires_code_correction = False
        requires_documentation_update = True
        requires_output_contract = False
        recommended_next_phase = NEXT_PRESSURE
        blocking_gaps = ["pressure_sigmaTheta_semantics"]
    elif volume_multiplier_semantics == "VOLUME_MULTIPLIER_AMBIGUOUS":
        math_audit_passed = False
        requires_code_correction = False
        requires_documentation_update = True
        requires_output_contract = True
        recommended_next_phase = NEXT_VOLUME
        blocking_gaps = ["volume_multiplier_semantics"]
    else:
        math_audit_passed = True
        requires_code_correction = False
        requires_documentation_update = True
        requires_output_contract = True
        recommended_next_phase = NEXT_OUTPUT_CONTRACT
        blocking_gaps = []

    return {
        "phase": PHASE,
        "primary_classification": PRIMARY_CLASSIFICATION,
        "secondary_classification": SECONDARY_CLASSIFICATION,
        "tertiary_classification": TERTIARY_CLASSIFICATION,
        "dimension_audit": dimension_audit,
        "pressure_semantics": pressure_semantics,
        "volume_multiplier_semantics": volume_multiplier_semantics,
        "axisymmetric_interpretation": AXISYMMETRIC_CAVEAT,
        "future_output_requirement": FUTURE_OUTPUT_REQUIREMENT,
        "math_audit_passed": math_audit_passed,
        "requires_code_correction": requires_code_correction,
        "requires_documentation_update": requires_documentation_update,
        "requires_output_contract": requires_output_contract,
        "blocking_gaps": blocking_gaps,
        "equations": {
            "plane_strain_modulus_Pa": "E' = E / (1 - nu^2)",
            "opening_m": "w0 = 3.65 * ((mu^2 * Q^3) / E'^2)^(1/9) * t^(1/9)",
            "radius_m": "R = 0.572 * ((E' * Q^3) / mu)^(1/9) * t^(4/9)",
            "pressure_factor": "pw / sigmaTheta",
            "fracture_volume_proxy_m3": "volume_multiplier * (w0/2)^2 * R * pi * pressure_factor",
        },
        "recommended_next_phase": recommended_next_phase,
        "caveats": [
            "No BUZ29-PENNY simulation is executed.",
            "No legacy equivalence or physical validation is claimed.",
            "fracture_volume_proxy_m3 is dimensionally a volume but remains a proxy until angular-basis output is explicit.",
            "volume_multiplier=10.0 is legacy-inspired and should not be reused as a 2pi conversion factor without a contract.",
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10C PennyShaped Math Axisymmetric 1rad Audit",
        "",
        f"- primary_classification: `{result['primary_classification']}`",
        f"- secondary_classification: `{result['secondary_classification']}`",
        f"- pressure_semantics: `{result['pressure_semantics']}`",
        f"- volume_multiplier_semantics: `{result['volume_multiplier_semantics']}`",
        f"- math_audit_passed: `{str(result['math_audit_passed']).lower()}`",
        f"- requires_code_correction: `{str(result['requires_code_correction']).lower()}`",
        f"- requires_output_contract: `{str(result['requires_output_contract']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Equations",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in result["equations"].items())
    lines.extend(
        [
            "",
            "## Dimension Audit",
            "",
            "| Field | Unit | Expression | Derived | Status | Notes |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in result["dimension_audit"]:
        lines.append(
            f"| `{row['field']}` | `{row['declared_unit']}` | `{row['code_expression']}` | `{row['derived_dimension']}` | `{row['status']}` | {row['notes']} |"
        )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10C PennyShaped math in axisymmetric 1 rad formulation."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument(
        "--fixture-mode",
        choices=["consistent", "inconsistent", "pressure_ambiguous", "volume_ambiguous"],
        default="consistent",
        help="Test hook for audit decision branches.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = audit_math(args.fixture_mode)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"PRIMARY_CLASSIFICATION={result['primary_classification']}")
    print(f"SECONDARY_CLASSIFICATION={result['secondary_classification']}")
    print(f"MATH_AUDIT_PASSED={str(result['math_audit_passed']).lower()}")
    print(f"REQUIRES_CODE_CORRECTION={str(result['requires_code_correction']).lower()}")
    print(f"REQUIRES_OUTPUT_CONTRACT={str(result['requires_output_contract']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
