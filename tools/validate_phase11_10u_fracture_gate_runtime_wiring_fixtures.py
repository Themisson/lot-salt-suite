#!/usr/bin/env python3
"""Validate Phase 11.10U fracture gate runtime wiring fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10U"
VALID_STATUS = "FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID"
PARTIAL_STATUS = "FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_PARTIAL"
INVALID_STATUS = "FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_INVALID"
NEXT_PHASE = "PHASE11_10V_SPECIFY_RUNTIME_WIRING_IMPLEMENTATION_PLAN"

REQUIRED_SCENARIO_IDS = {
    "missing_model_defaults_pkn_not_reached",
    "explicit_pkn_initiated_dispatch_eligible",
    "explicit_penny_initiated_diagnostic_eligible",
    "sigmatheta_guard_blocks_dispatch",
    "pressure_sigmatheta_criterion_blocks_dispatch",
    "unsupported_kgd_model_blocked",
    "explicit_empty_model_blocked",
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = _load_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("scenarios"), list):
        return payload["scenarios"]
    if isinstance(payload, list):
        return payload
    raise ValueError("scenarios file must be a list or contain a scenarios list")


def validate_fixture_payload(
    scenarios: list[dict[str, Any]], metadata: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    scenario_ids = {str(item.get("id", "")) for item in scenarios}
    missing_ids = sorted(REQUIRED_SCENARIO_IDS - scenario_ids)
    if len(scenarios) < 7:
        errors.append("at_least_7_scenarios_required")
    if missing_ids:
        errors.append("missing_required_scenarios:" + ",".join(missing_ids))

    by_id = {str(item.get("id", "")): item for item in scenarios}
    penny = by_id.get("explicit_penny_initiated_diagnostic_eligible", {})
    if penny.get("physically_validated") is not False:
        errors.append("penny_shaped_physically_validated_must_be_false")
    if penny.get("legacy_equivalent") is not False:
        errors.append("penny_shaped_legacy_equivalent_must_be_false")

    if metadata.get("runtime_wiring_implemented") is not False:
        errors.append("metadata_runtime_wiring_implemented_must_be_false")
    if metadata.get("runtime_execution_allowed") is not False:
        errors.append("metadata_runtime_execution_allowed_must_be_false")
    if metadata.get("buz29_execution_allowed") is not False:
        errors.append("metadata_buz29_execution_allowed_must_be_false")
    if metadata.get("physically_validated") is not False:
        errors.append("metadata_physically_validated_must_be_false")
    if metadata.get("legacy_equivalent") is not False:
        errors.append("metadata_legacy_equivalent_must_be_false")

    required_caveats = set(metadata.get("required_caveats", []))
    for caveat in [
        "PKN_DEFAULT_RETROCOMPATIBLE",
        "PENNY_SHAPED_DIAGNOSTIC_ONLY",
        "SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH",
        "PRESSURE_SIGMATHETA_CRITERION_REQUIRED_BEFORE_DISPATCH",
        "BUZ29_EXECUTION_BLOCKED",
    ]:
        if caveat not in required_caveats:
            warnings.append(f"missing_caveat:{caveat}")

    status = VALID_STATUS
    if errors:
        status = INVALID_STATUS
    elif warnings:
        status = PARTIAL_STATUS

    return {
        "phase": PHASE,
        "fixture_status": status,
        "scenario_count": len(scenarios),
        "scenario_ids": sorted(scenario_ids),
        "missing_scenario_ids": missing_ids,
        "runtime_wiring_implemented": metadata.get("runtime_wiring_implemented"),
        "runtime_execution_allowed": metadata.get("runtime_execution_allowed"),
        "buz29_execution_allowed": metadata.get("buz29_execution_allowed"),
        "physically_validated": metadata.get("physically_validated"),
        "legacy_equivalent": metadata.get("legacy_equivalent"),
        "errors": errors,
        "warnings": warnings,
        "recommended_next_phase": NEXT_PHASE if not errors else "PHASE11_10V_COMPLETE_RUNTIME_WIRING_FIXTURES",
        "classifications": [
            "PHASE11_10U_FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_DEFINED",
            status,
            "RUNTIME_WIRING_NOT_IMPLEMENTED",
            "BUZ29_EXECUTION_BLOCKED",
            "PENNY_SHAPED_DIAGNOSTIC_ONLY",
        ],
    }


def validate_files(scenarios_path: Path, metadata_path: Path) -> dict[str, Any]:
    scenarios = load_scenarios(scenarios_path)
    metadata = _load_json(metadata_path)
    if not isinstance(metadata, dict):
        raise ValueError("metadata file must contain a JSON object")
    return validate_fixture_payload(scenarios, metadata)


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10U fracture gate runtime wiring fixture validation",
        "",
        f"- phase: `{summary['phase']}`",
        f"- fixture_status: `{summary['fixture_status']}`",
        f"- scenario_count: `{summary['scenario_count']}`",
        f"- runtime_wiring_implemented: `{str(summary['runtime_wiring_implemented']).lower()}`",
        f"- runtime_execution_allowed: `{str(summary['runtime_execution_allowed']).lower()}`",
        f"- buz29_execution_allowed: `{str(summary['buz29_execution_allowed']).lower()}`",
        f"- recommended_next_phase: `{summary['recommended_next_phase']}`",
        "",
        "## Scenario IDs",
        "",
    ]
    lines.extend(f"- `{item}`" for item in summary["scenario_ids"])
    lines.extend(["", "## Classifications", ""])
    lines.extend(f"- `{item}`" for item in summary["classifications"])
    if summary["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- `{item}`" for item in summary["errors"])
    if summary["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- `{item}`" for item in summary["warnings"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 11.10U fracture gate runtime wiring fixtures."
    )
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args(argv)

    summary = validate_files(args.scenarios, args.metadata)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(summary, args.output_md)

    print(f"PHASE={summary['phase']}")
    print(f"FIXTURE_STATUS={summary['fixture_status']}")
    print(f"SCENARIO_COUNT={summary['scenario_count']}")
    print(f"RUNTIME_WIRING_IMPLEMENTED={str(summary['runtime_wiring_implemented']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED={str(summary['runtime_execution_allowed']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED={str(summary['buz29_execution_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={summary['recommended_next_phase']}")
    return 0 if summary["fixture_status"] != INVALID_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
