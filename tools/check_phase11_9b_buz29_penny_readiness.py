#!/usr/bin/env python3
"""Check BUZ29 readiness for a future PennyShaped diagnostic route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_EVIDENCE = {
    "active_model_penny_shaped": "BUZ29 active source identified as penny-shaped",
    "penny_math_audited": "Penny-shaped formulas audited",
    "penny_core_implemented": "PennyShapedModel kernel implemented",
    "diagnostic_adapter_implemented": "PennyShapedDiagnosticAdapter implemented",
    "synthetic_case_created": "Synthetic diagnostic case created",
    "pressure_history": "BUZ29 pressure history suitable for adapter",
    "sigma_theta_history": "BUZ29 sigmaTheta history suitable for adapter",
    "elapsed_opening_time": "BUZ29 elapsed time since opening trace",
    "apb_salt_state": "BUZ29 APB/salt state aligned with legacy criterion",
}


def _contains(path: Path, token: str) -> bool:
    return path.exists() and token in path.read_text(encoding="utf-8", errors="replace")


def evaluate_readiness(paths: dict[str, Path]) -> dict[str, Any]:
    evidence = {
        "active_model_penny_shaped": _contains(
            paths["buz29_audit"], "BUZ29_VISCO_FIRST_WELL_NOT_PKN"
        )
        and _contains(paths["buz29_audit"], "penny-shaped"),
        "penny_math_audited": _contains(
            paths["math_audit"], "SELECTED_MODEL_MATH_AUDITED"
        ),
        "penny_core_implemented": _contains(
            paths["minimal_impl"], "SELECTED_NON_PKN_MINIMAL_MODEL_IMPLEMENTED"
        ),
        "diagnostic_adapter_implemented": _contains(
            paths["adapter_impl"], "PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED"
        ),
        "synthetic_case_created": paths["synthetic_case"].exists()
        and _contains(paths["synthetic_case"], "Synthetic diagnostic case only"),
        "pressure_history": False,
        "sigma_theta_history": False,
        "elapsed_opening_time": False,
        "apb_salt_state": False,
    }
    missing = [key for key, value in evidence.items() if not value]

    if all(evidence.values()):
        readiness = "BUZ29_PENNY_READY_FOR_DIAGNOSTIC_YAML"
        can_start_11_10a = True
        next_phase = "PHASE11_10A_BUZ29_PENNY_DIAGNOSTIC_ROUTE"
    elif evidence["active_model_penny_shaped"] and evidence["diagnostic_adapter_implemented"]:
        readiness = "BUZ29_PENNY_CANDIDATE_PARTIAL"
        can_start_11_10a = False
        next_phase = "PHASE11_9C_COMPLETE_BUZ29_PENNY_EVIDENCE"
    else:
        readiness = "BUZ29_PENNY_CANDIDATE_BLOCKED"
        can_start_11_10a = False
        next_phase = "PHASE11_9C_COMPLETE_BUZ29_PENNY_EVIDENCE"

    return {
        "phase": "11.9B",
        "case": "BUZ29-VISCO-first-well",
        "track": "PENNY_SHAPED",
        "readiness": readiness,
        "gate": (
            "BUZ29_PENNY_READINESS_SUFFICIENT_FOR_11_10A"
            if can_start_11_10a
            else "BUZ29_PENNY_READINESS_PARTIAL_DO_NOT_START_11_10A"
        ),
        "can_start_11_10a": can_start_11_10a,
        "recommended_next_phase": next_phase,
        "evidence": evidence,
        "missing_evidence": missing,
        "physical_validation": False,
        "legacy_equivalence": False,
        "modern_yaml_created": False,
        "caveats": [
            "BUZ29 active model is penny-shaped, not PKN.",
            "The synthetic PennyShaped case does not validate BUZ29.",
            "BUZ29 still lacks complete pressure, sigmaTheta, elapsed-opening-time and APB/salt state evidence for a diagnostic YAML.",
            "Phase 11.10A must not start until readiness becomes sufficient.",
        ],
    }


def default_paths() -> dict[str, Path]:
    return {
        "buz29_audit": Path("docs/57_buz29_visco_first_well_audit.md"),
        "math_audit": Path("docs/61_selected_non_pkn_model_math_audit.md"),
        "minimal_impl": Path("docs/63_selected_non_pkn_model_minimal_implementation.md"),
        "adapter_impl": Path("docs/66_penny_diagnostic_adapter_implementation.md"),
        "synthetic_case": Path("cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml"),
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.9B BUZ29 PennyShaped Readiness",
        "",
        f"- readiness: `{result['readiness']}`",
        f"- gate: `{result['gate']}`",
        f"- can_start_11_10a: `{str(result['can_start_11_10a']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Evidence",
        "",
        "| Evidence | Present |",
        "|---|---:|",
    ]
    for key, value in result["evidence"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines.extend(["", "## Missing Evidence", ""])
    lines.extend(f"- `{item}`" for item in result["missing_evidence"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check BUZ29 readiness for a future PennyShaped diagnostic route."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = evaluate_readiness(default_paths())
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)
    print("PHASE=11.9B")
    print(f"READINESS={result['readiness']}")
    print(f"GATE={result['gate']}")
    print(f"CAN_START_11_10A={str(result['can_start_11_10a']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
