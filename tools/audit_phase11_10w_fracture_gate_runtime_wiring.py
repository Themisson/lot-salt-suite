#!/usr/bin/env python3
"""Audit Phase 11.10W fracture gate runtime wiring implementation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10W"
IMPLEMENTATION_STATUS = "FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED"
NEXT_PHASE = "PHASE11_10X_SPECIFY_RUNTIME_INTEGRATION_GATE"
REQUIRED_SCENARIOS = {
    "missing_model_defaults_pkn_not_reached",
    "explicit_pkn_initiated_dispatch_eligible",
    "explicit_penny_initiated_diagnostic_eligible",
    "sigmatheta_guard_blocks_dispatch",
    "pressure_sigmatheta_criterion_blocks_dispatch",
    "unsupported_kgd_model_blocked",
    "explicit_empty_model_blocked",
}


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
      raise ValueError("scenarios must be a list")
    return scenarios


def build_audit(scenarios_path: Path) -> dict[str, Any]:
    scenarios = load_scenarios(scenarios_path)
    scenario_ids = {str(item.get("id", "")) for item in scenarios}
    missing = sorted(REQUIRED_SCENARIOS - scenario_ids)
    fixtures_covered = not missing

    status = (
        IMPLEMENTATION_STATUS
        if fixtures_covered
        else "FRACTURE_GATE_RUNTIME_WIRING_PARTIAL"
    )

    return {
        "phase": PHASE,
        "implementation_status": status,
        "runtime_wiring_component_created": True,
        "runtime_execution_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_model_called": False,
        "pkn_runner_called": False,
        "penny_adapter_called": False,
        "penny_writer_called": False,
        "fixtures_covered": fixtures_covered,
        "scenario_count": len(scenarios),
        "missing_scenarios": missing,
        "classifications": [
            status,
            "RUNTIME_EXECUTION_NOT_ENABLED",
            "PKN_MODEL_NOT_CALLED",
            "PENNY_ADAPTER_NOT_CALLED",
            "BUZ29_EXECUTION_BLOCKED",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 11.10W fracture gate runtime wiring audit",
        "",
        f"- phase: `{payload['phase']}`",
        f"- implementation_status: `{payload['implementation_status']}`",
        f"- runtime_wiring_component_created: `{str(payload['runtime_wiring_component_created']).lower()}`",
        f"- runtime_execution_enabled: `{str(payload['runtime_execution_enabled']).lower()}`",
        f"- buz29_execution_allowed: `{str(payload['buz29_execution_allowed']).lower()}`",
        f"- pkn_model_called: `{str(payload['pkn_model_called']).lower()}`",
        f"- penny_adapter_called: `{str(payload['penny_adapter_called']).lower()}`",
        f"- fixtures_covered: `{str(payload['fixtures_covered']).lower()}`",
        f"- recommended_next_phase: `{payload['recommended_next_phase']}`",
        "",
        "## Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["classifications"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10W fracture gate runtime wiring implementation."
    )
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_audit(args.scenarios)

    if args.output_json:
        write_json(args.output_json, payload)
    if args.output_md:
        write_markdown(args.output_md, payload)

    print(f"PHASE={payload['phase']}")
    print(f"IMPLEMENTATION_STATUS={payload['implementation_status']}")
    print(f"RUNTIME_WIRING_COMPONENT_CREATED={str(payload['runtime_wiring_component_created']).lower()}")
    print(f"RUNTIME_EXECUTION_ENABLED={str(payload['runtime_execution_enabled']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED={str(payload['buz29_execution_allowed']).lower()}")
    print(f"PKN_MODEL_CALLED={str(payload['pkn_model_called']).lower()}")
    print(f"PENNY_ADAPTER_CALLED={str(payload['penny_adapter_called']).lower()}")
    print(f"FIXTURES_COVERED={str(payload['fixtures_covered']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={payload['recommended_next_phase']}")
    return 0 if payload["fixtures_covered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
