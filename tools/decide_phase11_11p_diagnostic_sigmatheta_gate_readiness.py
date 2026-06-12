#!/usr/bin/env python3
"""Decide Phase 11.11P diagnostic sigma-theta gate readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11P"
READY = "DIAGNOSTIC_SIGMATHETA_GATE_READY"
PARTIAL = "DIAGNOSTIC_SIGMATHETA_GATE_PARTIAL"
BLOCKED_PKN = "DIAGNOSTIC_SIGMATHETA_GATE_BLOCKED_BY_PKN_REGRESSION"
BLOCKED_OUTPUT = "DIAGNOSTIC_SIGMATHETA_GATE_BLOCKED_BY_OUTPUT_CONTAMINATION"
INCONCLUSIVE = "DIAGNOSTIC_SIGMATHETA_GATE_INCONCLUSIVE"
NEXT_PHASE = "PHASE11_11Q_SPECIFY_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH"


def _load_gate(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_decision(readiness_gate: Path) -> dict[str, Any]:
    gate = _load_gate(readiness_gate)
    phase11n = _mapping(gate.get("phase11_11n_sigmatheta_diagnostic_source"))
    phase11o = _mapping(gate.get("phase11_11o_sigmatheta_diagnostic_controlled_validation"))

    source_ready = (
        phase11n.get("implementation_status") == "SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED"
        and phase11n.get("limited_gate_can_be_fed_diagnostically") is True
    )
    controlled_ready = (
        phase11o.get("validation_status") == "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID"
        and phase11o.get("limited_gate_can_be_fed_diagnostically") is True
        and phase11o.get("ready_not_reached_case_valid") is True
        and phase11o.get("pkn_reached_case_valid") is True
        and phase11o.get("penny_reached_diagnostic_case_valid") is True
        and phase11o.get("missing_sigmatheta_blocks") is True
    )
    pkn_outputs_unchanged = (
        phase11o.get("physical_outputs_identical") is True
        and phase11o.get("pkn_behavior_changed") is False
    )
    diagnostic_output_isolated = phase11o.get("diagnostic_output_isolated") is True
    runtime_dispatch_enabled = (
        phase11n.get("runtime_dispatch_enabled") is True
        or phase11o.get("runtime_dispatch_enabled") is True
    )
    buz29_execution_allowed = (
        phase11n.get("buz29_execution_allowed") is True
        or phase11o.get("buz29_execution_allowed") is True
    )
    penny_shaped_runtime_enabled = (
        phase11n.get("penny_shaped_runtime_enabled") is True
        or phase11o.get("penny_shaped_runtime_enabled") is True
    )

    if not pkn_outputs_unchanged:
        readiness_status = BLOCKED_PKN
    elif not diagnostic_output_isolated:
        readiness_status = BLOCKED_OUTPUT
    elif (
        source_ready
        and controlled_ready
        and not runtime_dispatch_enabled
        and not buz29_execution_allowed
        and not penny_shaped_runtime_enabled
    ):
        readiness_status = READY
    elif source_ready or controlled_ready:
        readiness_status = PARTIAL
    else:
        readiness_status = INCONCLUSIVE

    ready_for_diagnostic_use = readiness_status == READY
    return {
        "phase": PHASE,
        "readiness_status": readiness_status,
        "ready_for_diagnostic_use": ready_for_diagnostic_use,
        "ready_for_physical_validation": False,
        "ready_for_physical_dispatch": False,
        "ready_for_real_source_integration_spec": ready_for_diagnostic_use,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "pkn_outputs_unchanged": pkn_outputs_unchanged,
        "diagnostic_output_isolated": diagnostic_output_isolated,
        "source_ready": source_ready,
        "controlled_cases_ready": controlled_ready,
        "evidence": [
            "SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED",
            "SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID",
            "LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY",
            "PKN_BEHAVIOR_NOT_CHANGED",
            "DIAGNOSTIC_OUTPUT_ISOLATED",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
        ],
        "limits": [
            "Diagnostic readiness is not physical validation.",
            "Reached means diagnostic gate eligibility, not fracture execution.",
            "Physical dispatch remains disabled.",
            "BUZ29-PENNY remains blocked.",
            "PENNY_SHAPED remains diagnostic-only.",
            "A real sigma-theta source integration specification is still required.",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, decision: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11P diagnostic sigma-theta gate readiness",
        "",
        f"- readiness_status: `{decision['readiness_status']}`",
        f"- ready_for_diagnostic_use: `{decision['ready_for_diagnostic_use']}`",
        f"- ready_for_physical_validation: `{decision['ready_for_physical_validation']}`",
        f"- ready_for_physical_dispatch: `{decision['ready_for_physical_dispatch']}`",
        (
            "- ready_for_real_source_integration_spec: "
            f"`{decision['ready_for_real_source_integration_spec']}`"
        ),
        f"- runtime_dispatch_enabled: `{decision['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{decision['buz29_execution_allowed']}`",
        f"- pkn_behavior_change_allowed: `{decision['pkn_behavior_change_allowed']}`",
        f"- penny_shaped_runtime_enabled: `{decision['penny_shaped_runtime_enabled']}`",
        f"- pkn_outputs_unchanged: `{decision['pkn_outputs_unchanged']}`",
        f"- diagnostic_output_isolated: `{decision['diagnostic_output_isolated']}`",
        f"- recommended_next_phase: `{decision['recommended_next_phase']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{item}`" for item in decision["evidence"])
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in decision["limits"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.11P diagnostic sigma-theta gate readiness."
    )
    parser.add_argument(
        "--readiness-gate",
        type=Path,
        default=Path("tests/fixtures/comparison/level1_readiness_gate.json"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    decision = build_decision(args.readiness_gate)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, decision)

    print(f"phase={decision['phase']}")
    print(f"readiness_status={decision['readiness_status']}")
    print(f"ready_for_diagnostic_use={decision['ready_for_diagnostic_use']}")
    print(f"ready_for_physical_validation={decision['ready_for_physical_validation']}")
    print(f"ready_for_physical_dispatch={decision['ready_for_physical_dispatch']}")
    print(f"recommended_next_phase={decision['recommended_next_phase']}")
    return 0 if decision["readiness_status"] == READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
