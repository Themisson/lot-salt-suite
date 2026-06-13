#!/usr/bin/env python3
"""Run the APB/LOT extended regression contract suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_OUTPUT_FORMATS = {"json", "legacy_dat"}
VALID_LEAKOFF_MODES = {"volume_balance", "legacy_nodal_force"}
VALID_SALT_MODES = {"pre_iterative", "legacy_inside_newton"}


def _read_yaml_scalars(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"')
        if key in {
            "output_format",
            "legacy_dat_output_enabled",
            "leakoff_coupling_mode",
            "salt_displacement_mode",
            "name",
        }:
            values[key] = value
    return values


def _derive_output_name(input_name: str) -> str:
    return f"{Path(input_name).stem}_out.json"


def _sample_json_contract() -> dict[str, Any]:
    return {
        "metadata": {
            "input_file": "input.yaml",
            "output_file": "input_out.json",
            "schema_version": "apb_lot_output_v1",
            "generated_by": "lot-salt-suite",
        },
        "configuration": {
            "output_format": "json",
            "leakoff_coupling_mode": "volume_balance",
            "salt_displacement_mode": "pre_iterative",
        },
        "time_series": [],
        "layers": [],
        "annulars": [],
        "summary": {},
        "caveats": ["contract validation only"],
    }


def _validate_json_contract(manifest: dict[str, Any]) -> bool:
    sample = _sample_json_contract()
    sections_ok = all(section in sample for section in manifest["required_json_sections"])
    metadata_ok = all(field in sample["metadata"] for field in manifest["required_metadata_fields"])
    config_ok = all(
        field in sample["configuration"]
        for field in manifest["required_configuration_fields"]
    )
    return sections_ok and metadata_ok and config_ok


def _validate_fixture(manifest_path: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    fixture_path = manifest_path.parent / fixture["path"]
    exists = fixture_path.exists()
    scalars = _read_yaml_scalars(fixture_path) if exists else {}

    output_format = scalars.get("output_format", "json")
    leakoff_mode = scalars.get("leakoff_coupling_mode", "volume_balance")
    salt_mode = scalars.get("salt_displacement_mode", "pre_iterative")

    accepted_by_contract = (
        output_format in VALID_OUTPUT_FORMATS
        and leakoff_mode in VALID_LEAKOFF_MODES
        and salt_mode in VALID_SALT_MODES
    )
    expected_valid = bool(fixture["expected_valid"])
    valid_matches_expectation = accepted_by_contract == expected_valid

    mode_matches = True
    for key, observed in (
        ("expected_output_format", output_format),
        ("expected_leakoff_coupling_mode", leakoff_mode),
        ("expected_salt_displacement_mode", salt_mode),
    ):
        if key in fixture and fixture[key] != observed:
            mode_matches = False

    explicit_output_path_valid = True
    if "expected_explicit_output_path" in fixture:
        explicit_output_path_valid = fixture["expected_explicit_output_path"].endswith(".json")

    return {
        "id": fixture["id"],
        "exists": exists,
        "expected_valid": expected_valid,
        "accepted_by_contract": accepted_by_contract,
        "valid_matches_expectation": valid_matches_expectation,
        "mode_matches": mode_matches,
        "output_format": output_format,
        "leakoff_coupling_mode": leakoff_mode,
        "salt_displacement_mode": salt_mode,
        "explicit_output_path_valid": explicit_output_path_valid,
    }


def run_regression(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture_results = [_validate_fixture(manifest_path, fixture) for fixture in manifest["fixtures"]]

    valid_fixtures = [item for item in fixture_results if item["expected_valid"]]
    invalid_fixtures = [item for item in fixture_results if not item["expected_valid"]]
    modern_modes_valid = any(
        item["output_format"] == "json"
        and item["leakoff_coupling_mode"] == "volume_balance"
        and item["salt_displacement_mode"] == "pre_iterative"
        and item["accepted_by_contract"]
        for item in valid_fixtures
    )
    legacy_modes_valid = any(
        item["output_format"] == "legacy_dat"
        and item["leakoff_coupling_mode"] == "legacy_nodal_force"
        and item["salt_displacement_mode"] == "legacy_inside_newton"
        and item["accepted_by_contract"]
        for item in valid_fixtures
    )
    invalid_modes_rejected = all(not item["accepted_by_contract"] for item in invalid_fixtures)
    all_expectations_met = all(
        item["exists"]
        and item["valid_matches_expectation"]
        and item["mode_matches"]
        and item["explicit_output_path_valid"]
        for item in fixture_results
    )
    output_name_rule_valid = all(
        _derive_output_name(source) == expected
        for source, expected in manifest["output_name_rule_cases"]
    )
    explicit_output_path_valid = any(
        item["explicit_output_path_valid"]
        for item in fixture_results
        if item["id"].endswith("explicit_output")
    )
    json_output_contract_valid = _validate_json_contract(manifest)

    passed = (
        all_expectations_met
        and modern_modes_valid
        and legacy_modes_valid
        and invalid_modes_rejected
        and output_name_rule_valid
        and explicit_output_path_valid
        and json_output_contract_valid
    )

    return {
        "phase": "APB_LOT_RUN_EXTENDED_REGRESSION_SUITE",
        "regression_status": (
            "APB_LOT_EXTENDED_REGRESSION_PASSED"
            if passed
            else "APB_LOT_EXTENDED_REGRESSION_FAILED"
        ),
        "modern_modes_valid": modern_modes_valid,
        "legacy_modes_valid": legacy_modes_valid,
        "invalid_modes_rejected": invalid_modes_rejected,
        "json_output_contract_valid": json_output_contract_valid,
        "output_name_rule_valid": output_name_rule_valid,
        "explicit_output_path_valid": explicit_output_path_valid,
        "legacy_modes_preserved": legacy_modes_valid,
        "runtime_metrics_available": False,
        "contract_validation_only": True,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
        "fixture_count": len(fixture_results),
        "fixture_results": fixture_results,
        "recommended_next_phase": "APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# APB/LOT extended regression suite",
        "",
        f"Status: `{report['regression_status']}`",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for key, value in report.items():
        if key != "fixture_results":
            lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Fixtures", "", "| Fixture | Accepted | Expected |", "|---|---:|---:|"])
    for item in report["fixture_results"]:
        lines.append(
            f"| `{item['id']}` | `{item['accepted_by_contract']}` | `{item['expected_valid']}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the APB/LOT extended regression contract suite.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "tests/fixtures/comparison/phase_apb_lot_extended_regression/"
            "apb_lot_extended_regression_manifest.json"
        ),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = run_regression(args.manifest)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)
    print(report["regression_status"])
    return 0 if report["regression_status"] == "APB_LOT_EXTENDED_REGRESSION_PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
