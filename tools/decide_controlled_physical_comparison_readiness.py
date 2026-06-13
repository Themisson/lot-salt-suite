#!/usr/bin/env python3
"""Decide readiness for a controlled BUZ/legacy comparison gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


READY_STATUS = "READY_FOR_BUZ_OR_LEGACY_COMPARISON_GATE"
ANALYTIC_ONLY_STATUS = "READY_FOR_ANALYTIC_REFERENCE_ONLY"
BLOCKED_REFERENCE_STATUS = "BLOCKED_BY_REFERENCE_GAP"
PHASE = "PHASE_DECIDE_CONTROLLED_PHYSICAL_COMPARISON_READINESS"


def build_decision(
    *,
    reference_within_tolerance: bool = True,
    pkn_regression_ok: bool = True,
) -> dict[str, Any]:
    ready_for_gate = reference_within_tolerance and pkn_regression_ok
    if ready_for_gate:
        status = READY_STATUS
        recommended_next = "PHASE_PREPARE_BUZ_OR_LEGACY_COMPARISON_GATE"
    elif reference_within_tolerance:
        status = ANALYTIC_ONLY_STATUS
        recommended_next = "PHASE_FIX_PKN_REGRESSION_BEFORE_COMPARISON_GATE"
    else:
        status = BLOCKED_REFERENCE_STATUS
        recommended_next = "PHASE_FIX_ELASTIC_SIGMATHETA_REFERENCE_COMPARISON"

    return {
        "phase": PHASE,
        "readiness_status": status,
        "source": "AXISYMMETRIC_ELASTIC_WELLBORE_STATE",
        "reference_comparison_status": (
            "ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_VALID"
            if reference_within_tolerance
            else "ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_INVALID"
        ),
        "reference_within_tolerance": reference_within_tolerance,
        "pkn_regression_ok": pkn_regression_ok,
        "ready_for_buz_or_legacy_gate": ready_for_gate,
        "ready_for_physical_validation": False,
        "ready_for_physical_dispatch": False,
        "legacy_equivalence_allowed": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "allowed_next_activity": "prepare_gate_only" if ready_for_gate else "stay_analytic_only",
        "recommended_next_phase": recommended_next,
        "caveats": [
            "Readiness is only for preparing a controlled comparison gate.",
            "Physical validation remains false.",
            "Legacy equivalence remains disallowed.",
            "BUZ29-PENNY remains blocked.",
            "Runtime dispatch remains disabled.",
        ],
    }


def write_outputs(decision: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Controlled Physical Comparison Readiness Decision",
            "",
            f"- readiness_status: `{decision['readiness_status']}`",
            f"- source: `{decision['source']}`",
            f"- ready_for_buz_or_legacy_gate: `{str(decision['ready_for_buz_or_legacy_gate']).lower()}`",
            f"- ready_for_physical_validation: `{str(decision['ready_for_physical_validation']).lower()}`",
            f"- legacy_equivalence_allowed: `{str(decision['legacy_equivalence_allowed']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(decision['runtime_dispatch_enabled']).lower()}`",
            f"- buz29_execution_allowed: `{str(decision['buz29_execution_allowed']).lower()}`",
            f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
            "",
            "This decision allows preparation of a comparison gate only. It does not "
            "allow physical validation, legacy equivalence or BUZ29-PENNY execution.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide readiness for controlled BUZ/legacy comparison gate."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument(
        "--reference-within-tolerance",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether the controlled reference comparison passed.",
    )
    parser.add_argument(
        "--pkn-regression-ok",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether PKN regression gates passed.",
    )
    args = parser.parse_args()

    decision = build_decision(
        reference_within_tolerance=args.reference_within_tolerance,
        pkn_regression_ok=args.pkn_regression_ok,
    )
    write_outputs(decision, args.output_json, args.output_md)
    print(f"phase={decision['phase']}")
    print(f"readiness_status={decision['readiness_status']}")
    print(f"ready_for_buz_or_legacy_gate={decision['ready_for_buz_or_legacy_gate']}")
    print(f"ready_for_physical_validation={decision['ready_for_physical_validation']}")
    print(f"legacy_equivalence_allowed={decision['legacy_equivalence_allowed']}")
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0 if decision["readiness_status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
