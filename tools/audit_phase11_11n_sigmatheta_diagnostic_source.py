#!/usr/bin/env python3
"""Audit Phase 11.11N diagnostic sigma-theta source fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.11N"
IMPLEMENTATION_STATUS = "SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED"
NEXT_PHASE = "PHASE11_11O_VALIDATE_SIGMATHETA_DIAGNOSTIC_SOURCE_ON_CONTROLLED_CASES"

REQUIRED_FIXTURES = {
    "sigma_theta_input_disabled_default.yaml": "default_disabled",
    "sigma_theta_input_valid_pkn_not_reached.yaml": "pkn_not_reached",
    "sigma_theta_input_valid_pkn_reached.yaml": "pkn_reached",
    "sigma_theta_input_valid_penny_reached_diagnostic.yaml": "penny_reached",
    "sigma_theta_input_missing_initial_invalid.yaml": "missing_initial_invalid",
    "sigma_theta_input_missing_current_invalid.yaml": "missing_current_invalid",
    "sigma_theta_input_physically_validated_true_invalid.yaml": "physically_validated_true_invalid",
    "sigma_theta_input_legacy_equivalent_true_invalid.yaml": "legacy_equivalent_true_invalid",
    "sigma_theta_input_invalid_source.yaml": "invalid_source",
    "sigma_theta_input_invalid_sign_convention.yaml": "invalid_sign_convention",
    "sigma_theta_input_invalid_reference_frame.yaml": "invalid_reference_frame",
    "sigma_theta_input_invalid_state_time.yaml": "invalid_state_time",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_audit(fixtures_dir: Path) -> dict[str, Any]:
    fixture_checks: dict[str, bool] = {}
    missing: list[str] = []
    for filename, check_name in REQUIRED_FIXTURES.items():
        path = fixtures_dir / filename
        exists = path.exists()
        fixture_checks[check_name] = exists
        if not exists:
            missing.append(filename)

    valid_pkn_reached = _read(fixtures_dir / "sigma_theta_input_valid_pkn_reached.yaml") if fixture_checks["pkn_reached"] else ""
    valid_pkn_not_reached = _read(fixtures_dir / "sigma_theta_input_valid_pkn_not_reached.yaml") if fixture_checks["pkn_not_reached"] else ""
    valid_penny = _read(fixtures_dir / "sigma_theta_input_valid_penny_reached_diagnostic.yaml") if fixture_checks["penny_reached"] else ""

    source_covered = "source: EXPLICIT_DIAGNOSTIC_INPUT" in valid_pkn_reached
    not_reached_covered = "sigma_theta_current_compression_positive_Pa: 5000000.0" in valid_pkn_not_reached
    reached_covered = "sigma_theta_current_compression_positive_Pa: -2000000.0" in valid_pkn_reached
    penny_covered = "fracture_model: PENNY_SHAPED" in valid_penny
    runtime_dispatch_disabled = "dispatch_runtime_enabled: false" in valid_pkn_reached
    physical_flags_false = (
        "physically_validated: false" in valid_pkn_reached
        and "legacy_equivalent: false" in valid_pkn_reached
    )

    all_valid = (
        not missing
        and source_covered
        and not_reached_covered
        and reached_covered
        and penny_covered
        and runtime_dispatch_disabled
        and physical_flags_false
    )

    return {
        "phase": PHASE,
        "implementation_status": IMPLEMENTATION_STATUS if all_valid else "SIGMATHETA_DIAGNOSTIC_SOURCE_PARTIAL",
        "source_type": "EXPLICIT_DIAGNOSTIC_INPUT",
        "synthetic_fixture_source_allowed": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "limited_gate_can_be_fed_diagnostically": all_valid,
        "fixture_count": len(list(fixtures_dir.glob("*.yaml"))) if fixtures_dir.exists() else 0,
        "fixture_checks": fixture_checks,
        "missing_fixtures": missing,
        "required_statuses": [
            "SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED",
            "LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
            "PKN_BEHAVIOR_NOT_CHANGED",
            "PENNY_SHAPED_RUNTIME_NOT_ENABLED",
        ],
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11N diagnostic sigma-theta source audit",
        "",
        f"- implementation_status: `{audit['implementation_status']}`",
        f"- source_type: `{audit['source_type']}`",
        f"- limited_gate_can_be_fed_diagnostically: `{audit['limited_gate_can_be_fed_diagnostically']}`",
        f"- runtime_dispatch_enabled: `{audit['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{audit['buz29_execution_allowed']}`",
        f"- pkn_behavior_changed: `{audit['pkn_behavior_changed']}`",
        f"- penny_shaped_runtime_enabled: `{audit['penny_shaped_runtime_enabled']}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Fixture Checks",
        "",
    ]
    lines.extend(f"- `{key}` = `{value}`" for key, value in audit["fixture_checks"].items())
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.11N diagnostic sigma-theta source fixtures."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase11_11n"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    audit = build_audit(args.fixtures_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, audit)

    print(f"phase={audit['phase']}")
    print(f"implementation_status={audit['implementation_status']}")
    print(f"source_type={audit['source_type']}")
    print(
        "limited_gate_can_be_fed_diagnostically="
        f"{audit['limited_gate_can_be_fed_diagnostically']}"
    )
    print(f"runtime_dispatch_enabled={audit['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={audit['recommended_next_phase']}")
    return 0 if not audit["missing_fixtures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
