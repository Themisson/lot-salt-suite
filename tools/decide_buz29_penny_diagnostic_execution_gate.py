#!/usr/bin/env python3
"""Decide whether BUZ29/PENNY may advance to a future diagnostic execution gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_DECIDE_BUZ29_PENNY_DIAGNOSTIC_EXECUTION_GATE"
ALLOWED_STATUS = "BUZ29_PENNY_DIAGNOSTIC_EXECUTION_ALLOWED_NEXT"
BLOCKED_STATUS = "BUZ29_PENNY_DIAGNOSTIC_EXECUTION_BLOCKED"
DEFAULT_MANIFEST = Path(
    "tests/fixtures/comparison/phase_buz29_penny_diagnostic_inputs/"
    "buz29_penny_diagnostic_input_manifest.json"
)
REQUIRED_CAVEATS = {
    "NO_PHYSICAL_VALIDATION",
    "NO_LEGACY_EQUIVALENCE",
    "NO_RUNTIME_DISPATCH",
}


def decide_execution_gate(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = set(manifest.get("required_inputs", []))
    available = set(manifest.get("available_inputs", []))
    missing = list(manifest.get("missing_inputs", []))
    caveats = set(manifest.get("blocking_caveats", []))

    inputs_ready = required.issubset(available) and not missing
    safety_flags_ok = (
        manifest.get("execution_allowed") is False
        and manifest.get("diagnostic_only") is True
        and manifest.get("physically_validated") is False
        and manifest.get("legacy_equivalent") is False
        and manifest.get("runtime_dispatch_enabled") is False
    )
    caveats_ok = REQUIRED_CAVEATS.issubset(caveats)
    semantic_flags_ok = (
        manifest.get("axisymmetric_caveats_registered") is True
        and manifest.get("pressure_semantics_registered") is True
        and manifest.get("sigma_theta_source_registered") is True
    )
    allowed_next = inputs_ready and safety_flags_ok and caveats_ok and semantic_flags_ok

    blocked_reasons: list[str] = []
    if not inputs_ready:
        blocked_reasons.append("REQUIRED_INPUTS_NOT_READY")
    if not safety_flags_ok:
        blocked_reasons.append("SAFETY_FLAGS_NOT_DIAGNOSTIC_ONLY")
    if not caveats_ok:
        blocked_reasons.append("REQUIRED_CAVEATS_MISSING")
    if not semantic_flags_ok:
        blocked_reasons.append("SEMANTIC_FLAGS_NOT_REGISTERED")

    return {
        "phase": PHASE,
        "gate_status": ALLOWED_STATUS if allowed_next else BLOCKED_STATUS,
        "case_id": manifest.get("case_id", "BUZ29_PENNY_DIAGNOSTIC"),
        "execution_allowed_next": allowed_next,
        "diagnostic_only": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_penny_executed_now": False,
        "pkn_behavior_change_allowed": False,
        "required_inputs_count": len(required),
        "required_inputs_ready": inputs_ready,
        "required_caveats_present": caveats_ok,
        "semantic_flags_registered": semantic_flags_ok,
        "blocked_reasons": blocked_reasons,
        "recommended_next_phase": (
            "PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_COMPARISON"
            if allowed_next
            else "PHASE_COMPLETE_BUZ29_PENNY_DIAGNOSTIC_EXECUTION_GATE"
        ),
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# BUZ29 Penny Diagnostic Execution Gate",
            "",
            f"- phase: `{result['phase']}`",
            f"- gate_status: `{result['gate_status']}`",
            f"- execution_allowed_next: `{str(result['execution_allowed_next']).lower()}`",
            f"- diagnostic_only: `{str(result['diagnostic_only']).lower()}`",
            f"- physically_validated: `{str(result['physically_validated']).lower()}`",
            f"- legacy_equivalent: `{str(result['legacy_equivalent']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- buz29_penny_executed_now: `{str(result['buz29_penny_executed_now']).lower()}`",
            f"- pkn_behavior_change_allowed: `{str(result['pkn_behavior_change_allowed']).lower()}`",
            f"- recommended_next_phase: `{result['recommended_next_phase']}`",
            "",
            "The gate authorizes only a future diagnostic execution step. It does not "
            "execute BUZ29/PENNY now, enable runtime dispatch, claim physical validation, "
            "or claim legacy equivalence.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide the BUZ29/PENNY diagnostic execution gate."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = decide_execution_gate(args.manifest)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"gate_status={result['gate_status']}")
    print(f"execution_allowed_next={result['execution_allowed_next']}")
    print(f"buz29_penny_executed_now={result['buz29_penny_executed_now']}")
    print(f"runtime_dispatch_enabled={result['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    return 0 if result["gate_status"] == ALLOWED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
