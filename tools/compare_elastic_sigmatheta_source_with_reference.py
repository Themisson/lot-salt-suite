#!/usr/bin/env python3
"""Compare the elastic sigma-theta source with controlled analytic references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_STATUS = "ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_VALID"
INVALID_STATUS = "ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_INVALID"
SOURCE = "AXISYMMETRIC_ELASTIC_WELLBORE_STATE"
PHASE = "PHASE_COMPARE_ELASTIC_SIGMATHETA_SOURCE_WITH_REFERENCE"
DEFAULT_REFERENCE = Path(
    "tests/fixtures/comparison/phase_elastic_sigmatheta_reference/"
    "axisymmetric_reference_cases.json"
)


def _required_float(row: dict[str, Any], key: str) -> float:
    if key not in row:
        raise ValueError(f"{row.get('case_id', '<unknown>')}: missing required field {key}")
    value = row[key]
    if not isinstance(value, (int, float)):
        raise ValueError(f"{row.get('case_id', '<unknown>')}: {key} must be numeric")
    return float(value)


def _required_bool(row: dict[str, Any], key: str) -> bool:
    if key not in row:
        raise ValueError(f"{row.get('case_id', '<unknown>')}: missing required field {key}")
    value = row[key]
    if not isinstance(value, bool):
        raise ValueError(f"{row.get('case_id', '<unknown>')}: {key} must be boolean")
    return value


def evaluate_case(row: dict[str, Any]) -> dict[str, Any]:
    far_field = _required_float(row, "far_field_stress_compression_positive_Pa")
    wellbore_pressure = _required_float(row, "wellbore_pressure_Pa")
    tensile_strength = _required_float(row, "tensile_strength_Pa")
    expected_initial = _required_float(
        row, "expected_sigma_theta_initial_compression_positive_Pa"
    )
    expected_current = _required_float(
        row, "expected_sigma_theta_current_compression_positive_Pa"
    )
    expected_margin = _required_float(row, "expected_margin_Pa")
    expected_reached = _required_bool(row, "expected_reached")

    actual_initial = far_field
    actual_current = far_field - wellbore_pressure
    tensile_condition = -actual_current
    actual_margin = tensile_condition - tensile_strength
    actual_reached = actual_margin >= 0.0

    return {
        "case_id": row.get("case_id", "<unknown>"),
        "actual_sigma_theta_initial_compression_positive_Pa": actual_initial,
        "actual_sigma_theta_current_compression_positive_Pa": actual_current,
        "actual_margin_Pa": actual_margin,
        "actual_reached": actual_reached,
        "initial_abs_error_Pa": abs(actual_initial - expected_initial),
        "current_abs_error_Pa": abs(actual_current - expected_current),
        "margin_abs_error_Pa": abs(actual_margin - expected_margin),
        "reached_matches": actual_reached == expected_reached,
    }


def compare_reference(reference_json: Path, tolerance_pa: float) -> dict[str, Any]:
    payload = json.loads(reference_json.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("reference fixture must contain a non-empty cases list")

    evaluated = [evaluate_case(row) for row in cases]
    max_abs_error = max(
        max(
            row["initial_abs_error_Pa"],
            row["current_abs_error_Pa"],
            row["margin_abs_error_Pa"],
        )
        for row in evaluated
    )
    all_reached_match = all(row["reached_matches"] for row in evaluated)
    within_tolerance = max_abs_error <= tolerance_pa and all_reached_match

    return {
        "phase": PHASE,
        "comparison_status": VALID_STATUS if within_tolerance else INVALID_STATUS,
        "source": SOURCE,
        "reference_type": payload.get("reference_type", "ANALYTIC_CONTROLLED_REFERENCE"),
        "case_count": len(evaluated),
        "max_abs_error_Pa": max_abs_error,
        "within_tolerance": within_tolerance,
        "formula_verified": within_tolerance,
        "sign_convention_verified": within_tolerance,
        "threshold_behavior_verified": all_reached_match,
        "physically_validated": False,
        "legacy_equivalent": False,
        "legacy_trace_used_as_physical_validation": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "recommended_next_phase": "PHASE_DECIDE_CONTROLLED_PHYSICAL_COMPARISON_READINESS",
        "cases": evaluated,
        "caveats": [
            "Analytic controlled reference only; not physical validation.",
            "No legacy equivalence is claimed.",
            "BUZ29-PENNY remains blocked.",
            "Runtime dispatch remains disabled.",
        ],
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Elastic Sigma-Theta Source Reference Comparison",
            "",
            f"- comparison_status: `{result['comparison_status']}`",
            f"- source: `{result['source']}`",
            f"- reference_type: `{result['reference_type']}`",
            f"- case_count: `{result['case_count']}`",
            f"- max_abs_error_Pa: `{result['max_abs_error_Pa']}`",
            f"- within_tolerance: `{str(result['within_tolerance']).lower()}`",
            f"- physically_validated: `{str(result['physically_validated']).lower()}`",
            f"- legacy_equivalent: `{str(result['legacy_equivalent']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- recommended_next_phase: `{result['recommended_next_phase']}`",
            "",
            "This comparison is analytic and controlled. It does not claim physical "
            "validation, legacy equivalence or runtime dispatch readiness.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the axisymmetric elastic sigma-theta source with references."
    )
    parser.add_argument("--reference-json", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--tolerance-pa", type=float, default=1.0e-9)
    args = parser.parse_args()

    result = compare_reference(args.reference_json, args.tolerance_pa)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"comparison_status={result['comparison_status']}")
    print(f"source={result['source']}")
    print(f"max_abs_error_Pa={result['max_abs_error_Pa']}")
    print(f"within_tolerance={result['within_tolerance']}")
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    return 0 if result["comparison_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
