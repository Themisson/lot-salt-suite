#!/usr/bin/env python3
"""Audit Phase 11.11J runtime sigma-theta and pressure availability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11J"
AUDIT_STATUS = "RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED"
NEXT_PHASE = "PHASE11_11K_SPECIFY_POST_DRILLING_INITIAL_STATE_INTEGRATION"


def build_audit() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "audit_status": AUDIT_STATUS,
        "sigma_theta_initial_runtime_available": False,
        "sigma_theta_current_runtime_available": False,
        "wellbore_pressure_runtime_available": True,
        "pressure_semantics_resolved": False,
        "sign_convention_resolved": False,
        "reference_frame_resolved": False,
        "runtime_real_wiring_allowed_next": False,
        "sources_audited": [
            "apps/lot-sim.cpp",
            "include/lot",
            "src/lot",
            "include/io",
            "src/io",
            "include/salt",
            "src/salt",
            "external/saltcreep (read-only)",
            "legacy (read-only)",
            "legance (read-only)",
        ],
        "findings": [
            {
                "capability": "sigma_theta_initial_runtime_available",
                "available": False,
                "evidence": (
                    "Limited gate pre-runner still initializes the sigma-theta "
                    "state as missing; existing sigma-theta fields are diagnostic "
                    "inputs, case fixtures, or salt diagnostics, not a resolved "
                    "post-drilling runtime source."
                ),
            },
            {
                "capability": "sigma_theta_current_runtime_available",
                "available": False,
                "evidence": (
                    "The LOT/PKN runtime does not expose a current total wall "
                    "sigma-theta stream with sign and reference frame aligned to "
                    "the fracture gate."
                ),
            },
            {
                "capability": "wellbore_pressure_runtime_available",
                "available": True,
                "evidence": (
                    "PKN result/timeseries and diagnostic cases carry wellbore "
                    "pressure values, but pressure semantics for real gate wiring "
                    "remain to be resolved against sigma-theta reference frame."
                ),
            },
        ],
        "blocking_reasons": [
            "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE",
            "MISSING_RUNTIME_SIGMATHETA_CURRENT_SOURCE",
            "PRESSURE_SEMANTICS_NOT_RESOLVED_FOR_REAL_GATE",
            "SIGMATHETA_SIGN_CONVENTION_NOT_RUNTIME_RESOLVED",
            "SIGMATHETA_REFERENCE_FRAME_NOT_RUNTIME_RESOLVED",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11J runtime sigma-theta pressure availability audit",
        "",
        f"- audit_status: `{audit['audit_status']}`",
        "- sigma_theta_initial_runtime_available: "
        f"`{audit['sigma_theta_initial_runtime_available']}`",
        "- sigma_theta_current_runtime_available: "
        f"`{audit['sigma_theta_current_runtime_available']}`",
        f"- wellbore_pressure_runtime_available: `{audit['wellbore_pressure_runtime_available']}`",
        f"- pressure_semantics_resolved: `{audit['pressure_semantics_resolved']}`",
        f"- sign_convention_resolved: `{audit['sign_convention_resolved']}`",
        f"- reference_frame_resolved: `{audit['reference_frame_resolved']}`",
        f"- runtime_real_wiring_allowed_next: `{audit['runtime_real_wiring_allowed_next']}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Findings",
        "",
    ]
    for item in audit["findings"]:
        lines.append(f"- `{item['capability']}` = `{item['available']}`: {item['evidence']}")
    lines.extend(["", "## Blocking Reasons", ""])
    lines.extend(f"- `{item}`" for item in audit["blocking_reasons"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.11J runtime sigma-theta and pressure availability."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    audit = build_audit()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, audit)

    print(f"phase={audit['phase']}")
    print(f"audit_status={audit['audit_status']}")
    print(
        "sigma_theta_initial_runtime_available="
        f"{audit['sigma_theta_initial_runtime_available']}"
    )
    print(
        "sigma_theta_current_runtime_available="
        f"{audit['sigma_theta_current_runtime_available']}"
    )
    print(f"wellbore_pressure_runtime_available={audit['wellbore_pressure_runtime_available']}")
    print(f"runtime_real_wiring_allowed_next={audit['runtime_real_wiring_allowed_next']}")
    print(f"recommended_next_phase={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
