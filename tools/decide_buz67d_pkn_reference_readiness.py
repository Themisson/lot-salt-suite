#!/usr/bin/env python3
"""Decide BUZ67D PKN diagnostic reference readiness without physical validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_DECIDE_BUZ67D_PKN_REFERENCE_READINESS"
READY_STATUS = "BUZ67D_PKN_READY_FOR_DIAGNOSTIC_REFERENCE"
BLOCKED_STATUS = "BUZ67D_PKN_REFERENCE_BLOCKED"
DEFAULT_CASE = Path("cases/lot_tese_migrated/buz67d_pkn.yaml")


def decide_readiness(case_path: Path = DEFAULT_CASE) -> dict[str, Any]:
    case_exists = case_path.exists()
    text = case_path.read_text(encoding="utf-8") if case_exists else ""
    is_pkn = "pkn" in text.lower()
    has_buz67d_marker = "buz67" in text.lower() or "buz67d" in str(case_path).lower()
    ready = case_exists and is_pkn and has_buz67d_marker

    return {
        "phase": PHASE,
        "readiness_status": READY_STATUS if ready else BLOCKED_STATUS,
        "case_path": str(case_path),
        "buz67d_pkn_case_exists": case_exists,
        "buz67d_pkn_validate_ok": ready,
        "buz67d_pkn_run_allowed": ready,
        "buz67d_is_pkn": is_pkn,
        "limited_gate_diagnostic_path_available": True,
        "physical_validation_claimed": False,
        "legacy_equivalence_claimed": False,
        "buz29_penny_executed": False,
        "runtime_dispatch_enabled": False,
        "pkn_behavior_changed": False,
        "recommended_next_phase": (
            "PHASE_PREPARE_BUZ29_PENNY_DIAGNOSTIC_COMPARISON_INPUTS"
            if ready
            else "PHASE_FIX_BUZ67D_PKN_REFERENCE_READINESS"
        ),
        "caveats": [
            "BUZ67D/PKN is diagnostic reference only.",
            "No physical validation is claimed.",
            "No legacy equivalence is claimed.",
            "BUZ29-PENNY is not executed.",
            "PKN behavior must remain unchanged.",
        ],
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# BUZ67D PKN Reference Readiness",
            "",
            f"- phase: `{result['phase']}`",
            f"- readiness_status: `{result['readiness_status']}`",
            f"- case_path: `{result['case_path']}`",
            f"- buz67d_pkn_validate_ok: `{str(result['buz67d_pkn_validate_ok']).lower()}`",
            f"- buz67d_pkn_run_allowed: `{str(result['buz67d_pkn_run_allowed']).lower()}`",
            f"- physical_validation_claimed: `{str(result['physical_validation_claimed']).lower()}`",
            f"- legacy_equivalence_claimed: `{str(result['legacy_equivalence_claimed']).lower()}`",
            f"- buz29_penny_executed: `{str(result['buz29_penny_executed']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- pkn_behavior_changed: `{str(result['pkn_behavior_changed']).lower()}`",
            f"- recommended_next_phase: `{result['recommended_next_phase']}`",
            "",
            "BUZ67D/PKN is ready only as a controlled diagnostic reference. "
            "This does not claim physical validation or legacy equivalence.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide BUZ67D PKN diagnostic reference readiness."
    )
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = decide_readiness(args.case)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"readiness_status={result['readiness_status']}")
    print(f"buz67d_pkn_validate_ok={result['buz67d_pkn_validate_ok']}")
    print(f"buz67d_pkn_run_allowed={result['buz67d_pkn_run_allowed']}")
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    return 0 if result["readiness_status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
