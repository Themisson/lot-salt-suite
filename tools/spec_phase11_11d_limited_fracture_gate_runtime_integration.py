#!/usr/bin/env python3
"""Specify Phase 11.11D limited fracture gate runtime integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11D"
SPEC_STATUS = "LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_SPECIFIED"
RECOMMENDED_NEXT_PHASE = "PHASE11_11E_IMPLEMENT_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION"


def specification() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "integration_spec_status": SPEC_STATUS,
        "implementation_allowed_next": True,
        "runtime_dispatch_allowed_next": False,
        "runtime_physical_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "penny_runtime_allowed": False,
        "penny_diagnostic_only": True,
        "required_integration_point": "after parse_validate_before_run_pkn_case",
        "required_feature_flag": "lot.fracture.fracture_gate_diagnostics.enabled",
        "required_dispatch_flag": "lot.fracture.fracture_gate_diagnostics.dispatch_runtime_enabled=false",
        "required_outputs": [
            "result.json",
            "timeseries.csv",
            "diagnostic_fracture_gate.json when opt-in enabled",
        ],
        "forbidden_changes": [
            "do_not_change_PknModel",
            "do_not_change_PknRunner",
            "do_not_enable_physical_dispatch",
            "do_not_execute_BUZ29_PENNY",
            "do_not_call_PennyShaped_adapter_as_runtime_physical_model",
        ],
        "acceptance_gates_for_next_phase": [
            "default_disabled_preserves_outputs",
            "diagnostic_enabled_preserves_result_json",
            "diagnostic_enabled_preserves_timeseries_csv",
            "diagnostic_json_isolated",
            "dispatch_runtime_enabled_true_rejected",
            "BUZ29_execution_blocked",
        ],
        "required_statuses": [
            "PHASE11_11D_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_SPECIFIED",
            SPEC_STATUS,
            "IMPLEMENTATION_ALLOWED_NEXT_WITH_DISPATCH_DISABLED",
            "PKN_BEHAVIOR_CHANGE_NOT_ALLOWED",
            "BUZ29_EXECUTION_BLOCKED",
        ],
        "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        "caveats": [
            "Phase 11.11D is specification only.",
            "The next phase may implement limited diagnostic integration only.",
            "Physical dispatch remains forbidden.",
            "PENNY_SHAPED remains diagnostic-only.",
            "BUZ29-PENNY remains blocked.",
        ],
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11D Limited Fracture Gate Runtime Integration Spec",
        "",
        f"- phase: `{data['phase']}`",
        f"- integration_spec_status: `{data['integration_spec_status']}`",
        f"- implementation_allowed_next: `{data['implementation_allowed_next']}`",
        f"- runtime_dispatch_allowed_next: `{data['runtime_dispatch_allowed_next']}`",
        f"- buz29_execution_allowed_next: `{data['buz29_execution_allowed_next']}`",
        f"- recommended_next_phase: `{data['recommended_next_phase']}`",
        "",
        "## Acceptance Gates",
    ]
    lines.extend(f"- `{item}`" for item in data["acceptance_gates_for_next_phase"])
    lines.extend(["", "## Forbidden Changes"])
    lines.extend(f"- `{item}`" for item in data["forbidden_changes"])
    write_text(path, "\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.11D limited fracture gate runtime integration."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = specification()
    if args.output_json:
        write_text(args.output_json, json.dumps(data, indent=2) + "\n")
    if args.output_md:
        write_markdown(args.output_md, data)
    print(f"phase={data['phase']}")
    print(f"integration_spec_status={data['integration_spec_status']}")
    print(f"recommended_next_phase={data['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
