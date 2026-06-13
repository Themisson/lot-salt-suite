#!/usr/bin/env python3
"""Validate axisymmetric elastic sigma-theta upgrade analytic fixture cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES_VALID"
INVALID_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES_INVALID"
PARTIAL_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES_PARTIAL"
INCONCLUSIVE_STATUS = "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES_INCONCLUSIVE"
SOURCE = "AXISYMMETRIC_ELASTIC_WELLBORE_STATE"


def _is_close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def _gate_status(fracture_margin: float) -> str:
    return "Reached" if fracture_margin >= 0.0 else "ReadyNotReached"


def _validate_case(case: dict[str, Any], tolerance: float) -> dict[str, Any]:
    errors: list[str] = []
    case_id = str(case.get("id", "<missing>"))

    try:
        far_field = float(case["far_field_stress_compression_positive_Pa"])
        wellbore_pressure = float(case["wellbore_pressure_Pa"])
        tensile_strength = float(case["tensile_strength_Pa"])
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "id": case_id,
            "valid": False,
            "errors": [f"missing or invalid required input: {exc}"],
        }

    sigma_theta_initial = far_field
    sigma_theta_current = far_field - wellbore_pressure
    tensile_condition = -sigma_theta_current
    fracture_margin = tensile_condition - tensile_strength
    fracture_initiated = fracture_margin >= 0.0
    gate_status = _gate_status(fracture_margin)

    checks = {
        "expected_sigma_theta_initial_compression_positive_Pa": sigma_theta_initial,
        "expected_sigma_theta_current_compression_positive_Pa": sigma_theta_current,
        "expected_tensile_condition_Pa": tensile_condition,
        "expected_fracture_margin_Pa": fracture_margin,
    }
    for field, actual in checks.items():
        expected = case.get(field)
        if not isinstance(expected, (int, float)):
            errors.append(f"{field} missing or nonnumeric")
        elif not _is_close(actual, float(expected), tolerance):
            errors.append(f"{field}: actual {actual} != expected {expected}")

    if case.get("expected_gate_status") != gate_status:
        errors.append(
            f"expected_gate_status: actual {gate_status} != expected {case.get('expected_gate_status')}"
        )
    if case.get("expected_fracture_initiated") is not fracture_initiated:
        errors.append(
            "expected_fracture_initiated: "
            f"actual {fracture_initiated} != expected {case.get('expected_fracture_initiated')}"
        )

    return {
        "id": case_id,
        "valid": not errors,
        "errors": errors,
        "computed": {
            "sigma_theta_initial_compression_positive_Pa": sigma_theta_initial,
            "sigma_theta_current_compression_positive_Pa": sigma_theta_current,
            "tensile_condition_Pa": tensile_condition,
            "fracture_margin_Pa": fracture_margin,
            "gate_status": gate_status,
            "fracture_initiated": fracture_initiated,
        },
    }


def validate(cases_path: Path) -> dict[str, Any]:
    if not cases_path.exists():
        return {
            "phase": "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_VALIDATION",
            "source": SOURCE,
            "validation_status": INCONCLUSIVE_STATUS,
            "formula_verified": False,
            "sign_convention_verified": False,
            "threshold_behavior_verified": False,
            "case_count": 0,
            "semi_physical": True,
            "physically_validated": False,
            "legacy_equivalent": False,
            "runtime_dispatch_enabled": False,
            "buz29_execution_allowed": False,
            "pkn_behavior_changed": False,
            "penny_shaped_runtime_enabled": False,
            "errors": [f"missing cases file: {cases_path}"],
            "case_results": [],
            "recommended_next_phase": "PHASE_DECIDE_ELASTIC_SIGMATHETA_UPGRADE_READINESS",
        }

    data = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = data.get("cases")
    tolerance = float(data.get("absolute_tolerance", 1.0e-9))
    source = data.get("source")
    if not isinstance(cases, list):
        cases = []

    case_results = [_validate_case(case, tolerance) for case in cases]
    errors = [
        f"{case_result['id']}: {error}"
        for case_result in case_results
        for error in case_result["errors"]
    ]
    if source != SOURCE:
        errors.append(f"source must be {SOURCE}")

    all_valid = len(case_results) == 5 and all(r["valid"] for r in case_results) and not errors
    threshold_behavior_verified = any(
        r["id"] == "exact_threshold_reached"
        and r.get("computed", {}).get("fracture_margin_Pa") == 0.0
        and r.get("computed", {}).get("fracture_initiated") is True
        for r in case_results
    )

    formula_verified = all_valid
    sign_convention_verified = all_valid and all(
        _is_close(
            r["computed"]["tensile_condition_Pa"],
            -r["computed"]["sigma_theta_current_compression_positive_Pa"],
            tolerance,
        )
        for r in case_results
        if "computed" in r
    )

    if all_valid and threshold_behavior_verified:
        status = VALID_STATUS
    elif case_results:
        status = PARTIAL_STATUS
    else:
        status = INVALID_STATUS

    return {
        "phase": "ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_VALIDATION",
        "source": SOURCE,
        "validation_status": status,
        "formula_verified": formula_verified,
        "sign_convention_verified": sign_convention_verified,
        "threshold_behavior_verified": threshold_behavior_verified,
        "case_count": len(case_results),
        "absolute_tolerance": tolerance,
        "semi_physical": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "errors": errors,
        "case_results": case_results,
        "recommended_next_phase": "PHASE_DECIDE_ELASTIC_SIGMATHETA_UPGRADE_READINESS",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Elastic Sigma-Theta Upgrade Analytic Validation",
        "",
        f"- validation_status: `{report['validation_status']}`",
        f"- source: `{report['source']}`",
        f"- formula_verified: `{report['formula_verified']}`",
        f"- sign_convention_verified: `{report['sign_convention_verified']}`",
        f"- threshold_behavior_verified: `{report['threshold_behavior_verified']}`",
        f"- case_count: `{report['case_count']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{report['pkn_behavior_changed']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Cases",
        "",
    ]
    for case_result in report["case_results"]:
        computed = case_result.get("computed", {})
        lines.append(
            "- `{id}`: valid=`{valid}`, gate=`{gate}`, margin_Pa=`{margin}`".format(
                id=case_result["id"],
                valid=case_result["valid"],
                gate=computed.get("gate_status", "n/a"),
                margin=computed.get("fracture_margin_Pa", "n/a"),
            )
        )
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate axisymmetric elastic sigma-theta upgrade analytic cases."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(
            "tests/fixtures/comparison/phase_elastic_sigmatheta_upgrade_analytic/"
            "elastic_sigmatheta_upgrade_analytic_cases.json"
        ),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = validate(args.cases)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"source={report['source']}")
    print(f"validation_status={report['validation_status']}")
    print(f"formula_verified={report['formula_verified']}")
    print(f"threshold_behavior_verified={report['threshold_behavior_verified']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    return 0 if report["validation_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
