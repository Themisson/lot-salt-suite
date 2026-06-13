#!/usr/bin/env python3
"""Specify Phase 11.11Q real sigma-theta source integration path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11Q"
STATUS = "REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED"
NEXT_PHASE = "PHASE11_11R_CREATE_POST_DRILLING_SIGMATHETA_PROVIDER_FIXTURES"


def build_specification() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "integration_path_status": STATUS,
        "primary_real_source": "ELASTIC_INITIAL_WELLBORE_STATE",
        "secondary_real_source": "APB_SALT_COUPLED_STATE",
        "future_real_source": "SALT_CREEP_PRE_LOT_STATE",
        "diagnostic_only_sources": [
            "EXPLICIT_DIAGNOSTIC_INPUT",
            "SYNTHETIC_FIXTURE",
        ],
        "legacy_trace_physical_validation_allowed": False,
        "requires_post_drilling_state": True,
        "lot_time_zero_is_not_drilling_time_zero": True,
        "required_state_time": "POST_DRILLING_BEFORE_LOT",
        "required_reference_frame": "WELLBORE_WALL_TOTAL_STRESS",
        "required_sign_convention": "COMPRESSION_POSITIVE",
        "provider_contract_specified": True,
        "provider_name": "PostDrillingSigmaThetaProvider",
        "provider_contract": {
            "source_enum": [
                "ElasticInitialWellboreState",
                "ApbSaltCoupledState",
                "SaltCreepPreLotState",
                "ExplicitDiagnosticInput",
                "SyntheticFixture",
                "Unknown",
            ],
            "result_fields": [
                "available",
                "sigma_theta_initial_compression_positive_Pa",
                "sigma_theta_current_compression_positive_Pa",
                "source",
                "state_time",
                "sign_convention",
                "reference_frame",
                "physically_validated",
                "legacy_equivalent",
                "caveats",
            ],
        },
        "future_sequence": [
            "11.11R_CREATE_POST_DRILLING_SIGMATHETA_PROVIDER_FIXTURES",
            "11.11S_IMPLEMENT_SYNTHETIC_DIAGNOSTIC_PROVIDER",
            "11.11T_SPECIFY_ELASTIC_INITIAL_PROVIDER",
            "11.11U_IMPLEMENT_ELASTIC_INITIAL_PROVIDER",
            "11.11V_VALIDATE_ELASTIC_INITIAL_PROVIDER_CONTROLLED_CASES",
            "11.11W_DECIDE_REAL_PROVIDER_LIMITED_GATE_READINESS",
        ],
        "implementation_allowed_next": False,
        "runtime_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "recommended_next_phase": NEXT_PHASE,
        "required_statuses": [
            "PHASE11_11Q_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED",
            "REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED",
            "PRIMARY_REAL_SOURCE_ELASTIC_INITIAL_WELLBORE_STATE",
            "POST_DRILLING_SIGMATHETA_PROVIDER_REQUIRED",
            "IMPLEMENTATION_NOT_ALLOWED_NEXT",
            "RUNTIME_DISPATCH_NOT_ALLOWED",
            "BUZ29_EXECUTION_BLOCKED",
            "PKN_BEHAVIOR_NOT_CHANGED",
        ],
        "caveats": [
            "Phase 11.11Q is specification only.",
            "A real provider is not implemented in this phase.",
            "EXPLICIT_DIAGNOSTIC_INPUT and SYNTHETIC_FIXTURE remain diagnostic sources.",
            "LEGACY_DIAGNOSTIC_TRACE is not a physical validation source.",
            "The LOT t=0 is not the drilling t=0.",
            "Physical dispatch remains disabled.",
        ],
    }


def write_markdown(path: Path, spec: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11Q real sigma-theta source integration path",
        "",
        f"- integration_path_status: `{spec['integration_path_status']}`",
        f"- primary_real_source: `{spec['primary_real_source']}`",
        f"- secondary_real_source: `{spec['secondary_real_source']}`",
        f"- future_real_source: `{spec['future_real_source']}`",
        (
            "- legacy_trace_physical_validation_allowed: "
            f"`{spec['legacy_trace_physical_validation_allowed']}`"
        ),
        f"- requires_post_drilling_state: `{spec['requires_post_drilling_state']}`",
        (
            "- lot_time_zero_is_not_drilling_time_zero: "
            f"`{spec['lot_time_zero_is_not_drilling_time_zero']}`"
        ),
        f"- provider_contract_specified: `{spec['provider_contract_specified']}`",
        f"- implementation_allowed_next: `{spec['implementation_allowed_next']}`",
        f"- runtime_dispatch_allowed_next: `{spec['runtime_dispatch_allowed_next']}`",
        f"- buz29_execution_allowed_next: `{spec['buz29_execution_allowed_next']}`",
        f"- pkn_behavior_change_allowed: `{spec['pkn_behavior_change_allowed']}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Diagnostic-only sources",
        "",
    ]
    lines.extend(f"- `{source}`" for source in spec["diagnostic_only_sources"])
    lines.extend(["", "## Future sequence", ""])
    lines.extend(f"- `{phase}`" for phase in spec["future_sequence"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in spec["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.11Q real sigma-theta source integration path."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    spec = build_specification()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(spec, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, spec)

    print(f"phase={spec['phase']}")
    print(f"integration_path_status={spec['integration_path_status']}")
    print(f"primary_real_source={spec['primary_real_source']}")
    print(f"provider_contract_specified={spec['provider_contract_specified']}")
    print(f"implementation_allowed_next={spec['implementation_allowed_next']}")
    print(f"runtime_dispatch_allowed_next={spec['runtime_dispatch_allowed_next']}")
    print(f"recommended_next_phase={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
