#!/usr/bin/env python3
"""Run the first controlled axisymmetric sigma-theta reference comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON"
VALID_STATUS = "FIRST_CONTROLLED_REFERENCE_COMPARISON_VALID"
INVALID_STATUS = "FIRST_CONTROLLED_REFERENCE_COMPARISON_INVALID"
REFERENCE_TYPE = "ANALYTIC_AXISYMMETRIC_CONTROLLED_REFERENCE"
SOURCE = "AXISYMMETRIC_ELASTIC_WELLBORE_STATE"
DEFAULT_CASES = Path(
    "tests/fixtures/comparison/phase_first_controlled_reference/"
    "axisymmetric_reference_cases.json"
)


def _numeric(row: dict[str, Any], key: str) -> float:
    if key not in row:
        raise ValueError(f"{row.get('id', '<unknown>')}: missing required field {key}")
    value = row[key]
    if not isinstance(value, (int, float)):
        raise ValueError(f"{row.get('id', '<unknown>')}: {key} must be numeric")
    return float(value)


def _boolean(row: dict[str, Any], key: str) -> bool:
    if key not in row:
        raise ValueError(f"{row.get('id', '<unknown>')}: missing required field {key}")
    value = row[key]
    if not isinstance(value, bool):
        raise ValueError(f"{row.get('id', '<unknown>')}: {key} must be boolean")
    return value


def evaluate_case(row: dict[str, Any]) -> dict[str, Any]:
    far_field = _numeric(row, "far_field_stress_compression_positive_Pa")
    pressure = _numeric(row, "wellbore_pressure_Pa")
    axisymmetric_factor = _numeric(row, "axisymmetric_factor")
    pressure_coupling_factor = _numeric(row, "pressure_coupling_factor")
    tensile_strength = _numeric(row, "tensile_strength_Pa")

    expected_initial = _numeric(
        row, "expected_sigma_theta_initial_compression_positive_Pa"
    )
    expected_current = _numeric(
        row, "expected_sigma_theta_current_compression_positive_Pa"
    )
    expected_tensile_condition = _numeric(row, "expected_tensile_condition_Pa")
    expected_margin = _numeric(row, "expected_fracture_margin_Pa")
    expected_initiated = _boolean(row, "expected_fracture_initiated")
    expected_status = row.get("expected_gate_status")

    initial = axisymmetric_factor * far_field
    current = initial - pressure_coupling_factor * pressure
    tensile_condition = -current
    margin = tensile_condition - tensile_strength
    initiated = margin >= 0.0
    gate_status = "Reached" if initiated else "NotReached"

    return {
        "id": row.get("id", "<unknown>"),
        "actual_sigma_theta_initial_compression_positive_Pa": initial,
        "actual_sigma_theta_current_compression_positive_Pa": current,
        "actual_tensile_condition_Pa": tensile_condition,
        "actual_fracture_margin_Pa": margin,
        "actual_gate_status": gate_status,
        "actual_fracture_initiated": initiated,
        "initial_abs_error_Pa": abs(initial - expected_initial),
        "current_abs_error_Pa": abs(current - expected_current),
        "tensile_condition_abs_error_Pa": abs(
            tensile_condition - expected_tensile_condition
        ),
        "margin_abs_error_Pa": abs(margin - expected_margin),
        "gate_status_matches": gate_status == expected_status,
        "fracture_initiated_matches": initiated == expected_initiated,
    }


def run_comparison(cases_path: Path, tolerance_pa: float = 1.0e-9) -> dict[str, Any]:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if payload.get("reference_type") != REFERENCE_TYPE:
        raise ValueError(f"reference_type must be {REFERENCE_TYPE}")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases fixture must contain a non-empty cases list")

    evaluated = [evaluate_case(row) for row in cases]
    max_abs_error = max(
        max(
            row["initial_abs_error_Pa"],
            row["current_abs_error_Pa"],
            row["tensile_condition_abs_error_Pa"],
            row["margin_abs_error_Pa"],
        )
        for row in evaluated
    )
    statuses_match = all(row["gate_status_matches"] for row in evaluated)
    initiation_matches = all(row["fracture_initiated_matches"] for row in evaluated)
    within_tolerance = max_abs_error <= tolerance_pa and statuses_match and initiation_matches

    return {
        "phase": PHASE,
        "comparison_status": VALID_STATUS if within_tolerance else INVALID_STATUS,
        "reference_type": REFERENCE_TYPE,
        "implemented_source": SOURCE,
        "case_count": len(evaluated),
        "max_abs_error_Pa": max_abs_error,
        "within_tolerance": within_tolerance,
        "physical_validation_claimed": False,
        "legacy_equivalence_claimed": False,
        "runtime_dispatch_enabled": False,
        "buz29_penny_executed": False,
        "pkn_behavior_changed": False,
        "recommended_next_phase": "PHASE_DECIDE_BUZ67D_PKN_REFERENCE_READINESS",
        "cases": evaluated,
        "caveats": [
            "Analytic controlled reference only.",
            "No physical validation is claimed.",
            "No legacy equivalence is claimed.",
            "BUZ29-PENNY is not executed.",
            "Runtime dispatch remains disabled.",
            "PKN behavior is unchanged.",
        ],
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# First Controlled Reference Comparison",
            "",
            f"- phase: `{result['phase']}`",
            f"- comparison_status: `{result['comparison_status']}`",
            f"- reference_type: `{result['reference_type']}`",
            f"- implemented_source: `{result['implemented_source']}`",
            f"- case_count: `{result['case_count']}`",
            f"- max_abs_error_Pa: `{result['max_abs_error_Pa']}`",
            f"- within_tolerance: `{str(result['within_tolerance']).lower()}`",
            f"- physical_validation_claimed: `{str(result['physical_validation_claimed']).lower()}`",
            f"- legacy_equivalence_claimed: `{str(result['legacy_equivalence_claimed']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- buz29_penny_executed: `{str(result['buz29_penny_executed']).lower()}`",
            f"- pkn_behavior_changed: `{str(result['pkn_behavior_changed']).lower()}`",
            f"- recommended_next_phase: `{result['recommended_next_phase']}`",
            "",
            "This comparison pins the algebraic axisymmetric elastic source against "
            "independent analytic fixture values. It does not claim physical "
            "validation or legacy equivalence.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the first controlled axisymmetric reference comparison."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--tolerance-pa", type=float, default=1.0e-9)
    args = parser.parse_args()

    result = run_comparison(args.cases, args.tolerance_pa)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"comparison_status={result['comparison_status']}")
    print(f"reference_type={result['reference_type']}")
    print(f"max_abs_error_Pa={result['max_abs_error_Pa']}")
    print(f"within_tolerance={result['within_tolerance']}")
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    return 0 if result["comparison_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
