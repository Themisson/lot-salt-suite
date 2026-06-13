#!/usr/bin/env python3
"""Prepare BUZ29/PENNY diagnostic comparison inputs without executing the case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_PREPARE_BUZ29_PENNY_DIAGNOSTIC_COMPARISON_INPUTS"
PREPARED_STATUS = "BUZ29_PENNY_DIAGNOSTIC_INPUTS_PREPARED"
BLOCKED_STATUS = "BUZ29_PENNY_DIAGNOSTIC_INPUTS_BLOCKED"
DEFAULT_MANIFEST = Path(
    "tests/fixtures/comparison/phase_buz29_penny_diagnostic_inputs/"
    "buz29_penny_diagnostic_input_manifest.json"
)


def prepare_inputs(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = list(manifest.get("required_inputs", []))
    available = list(manifest.get("available_inputs", []))
    missing = list(manifest.get("missing_inputs", []))
    caveats = list(manifest.get("blocking_caveats", []))

    required_available = all(item in available for item in required)
    safety_flags_ok = (
        manifest.get("execution_allowed") is False
        and manifest.get("diagnostic_only") is True
        and manifest.get("physically_validated") is False
        and manifest.get("legacy_equivalent") is False
        and manifest.get("runtime_dispatch_enabled") is False
    )
    semantic_flags_ok = (
        manifest.get("axisymmetric_caveats_registered") is True
        and manifest.get("pressure_semantics_registered") is True
        and manifest.get("sigma_theta_source_registered") is True
    )
    sufficient = required_available and not missing and safety_flags_ok and semantic_flags_ok

    return {
        "phase": PHASE,
        "input_status": PREPARED_STATUS if sufficient else BLOCKED_STATUS,
        "case_id": manifest.get("case_id", "BUZ29_PENNY_DIAGNOSTIC"),
        "execution_allowed": False,
        "diagnostic_only": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "required_inputs_count": len(required),
        "available_inputs_count": len(available),
        "available_inputs_sufficient_for_diagnostic_gate": sufficient,
        "missing_inputs": missing,
        "blocking_caveats": caveats,
        "axisymmetric_caveats_registered": manifest.get(
            "axisymmetric_caveats_registered"
        )
        is True,
        "pressure_semantics_registered": manifest.get("pressure_semantics_registered")
        is True,
        "sigma_theta_source_registered": manifest.get("sigma_theta_source_registered")
        is True,
        "recommended_next_phase": (
            "PHASE_DECIDE_BUZ29_PENNY_DIAGNOSTIC_EXECUTION_GATE"
            if sufficient
            else "PHASE_COMPLETE_BUZ29_PENNY_DIAGNOSTIC_INPUTS"
        ),
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# BUZ29 Penny Diagnostic Comparison Inputs",
            "",
            f"- phase: `{result['phase']}`",
            f"- input_status: `{result['input_status']}`",
            f"- execution_allowed: `{str(result['execution_allowed']).lower()}`",
            f"- diagnostic_only: `{str(result['diagnostic_only']).lower()}`",
            f"- physically_validated: `{str(result['physically_validated']).lower()}`",
            f"- legacy_equivalent: `{str(result['legacy_equivalent']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- required_inputs_count: `{result['required_inputs_count']}`",
            f"- available_inputs_sufficient_for_diagnostic_gate: `{str(result['available_inputs_sufficient_for_diagnostic_gate']).lower()}`",
            f"- recommended_next_phase: `{result['recommended_next_phase']}`",
            "",
            "The manifest prepares a future diagnostic gate only. It does not execute "
            "BUZ29/PENNY and does not claim physical validation or legacy equivalence.",
            "",
        ]
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare BUZ29/PENNY diagnostic comparison inputs."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = prepare_inputs(args.manifest)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"input_status={result['input_status']}")
    print(f"execution_allowed={result['execution_allowed']}")
    print(
        "available_inputs_sufficient_for_diagnostic_gate="
        f"{result['available_inputs_sufficient_for_diagnostic_gate']}"
    )
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    return 0 if result["input_status"] == PREPARED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
