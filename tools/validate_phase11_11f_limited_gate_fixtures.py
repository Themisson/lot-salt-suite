#!/usr/bin/env python3
"""Validate Phase 11.11F limited_gate fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


EXPECTED_FIXTURES = {
    "limited_gate_disabled_default.yaml": "default_disabled_covered",
    "limited_gate_enabled_pkn.yaml": "pkn_limited_gate_covered",
    "limited_gate_enabled_penny.yaml": "penny_limited_gate_covered",
    "limited_gate_dispatch_true_invalid.yaml": "dispatch_true_invalid_covered",
    "limited_gate_missing_sigmatheta_blocks.yaml": "missing_sigmatheta_blocks_covered",
    "limited_gate_invalid_model_blocked.yaml": "invalid_model_blocked_covered",
}

METADATA_FILE = "limited_gate_fixtures_metadata.json"
VALID_STATUS = "LIMITED_GATE_FIXTURES_VALID"
INVALID_STATUS = "LIMITED_GATE_FIXTURES_INVALID"


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return loaded


def _validate_metadata(fixtures_dir: Path) -> tuple[dict[str, Any], list[str]]:
    path = fixtures_dir / METADATA_FILE
    errors: list[str] = []
    if not path.exists():
        return {}, [f"missing metadata: {METADATA_FILE}"]
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}, [f"{METADATA_FILE} must contain a JSON object"]

    expected_false = [
        "runtime_dispatch_enabled",
        "runtime_physical_dispatch_allowed",
        "buz29_execution_allowed",
        "pkn_behavior_change_allowed",
        "penny_shaped_runtime_enabled",
    ]
    if loaded.get("phase") != "11.11F":
        errors.append("metadata phase must be 11.11F")
    if loaded.get("fixture_type") != "limited_gate_runtime_integration_contract":
        errors.append("metadata fixture_type mismatch")
    if loaded.get("limited_gate_mode_supported") is not True:
        errors.append("limited_gate_mode_supported must be true")
    for key in expected_false:
        if loaded.get(key) is not False:
            errors.append(f"{key} must be false")
    required_caveats = loaded.get("required_caveats")
    if not isinstance(required_caveats, list):
        errors.append("required_caveats must be a list")
    else:
        for caveat in [
            "PKN_DEFAULT_RETROCOMPATIBLE",
            "LIMITED_GATE_DIAGNOSTIC_ONLY",
            "DISPATCH_RUNTIME_ENABLED_TRUE_REJECTED",
            "PENNY_SHAPED_DIAGNOSTIC_ONLY",
            "BUZ29_EXECUTION_BLOCKED",
            "DIAGNOSTIC_OUTPUT_ISOLATED",
        ]:
            if caveat not in required_caveats:
                errors.append(f"missing required caveat: {caveat}")
    return loaded, errors


def _validate_fixture(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    data = _load_yaml(path)
    expected = _nested(data, "fixture", "expected")
    fracture = _nested(data, "lot", "fracture")
    if _nested(data, "fixture", "phase") != "11.11F":
        errors.append("fixture phase must be 11.11F")
    if not _nested(data, "fixture", "id"):
        errors.append("missing fixture.id")
    if not isinstance(expected, dict):
        errors.append("missing fixture.expected")
    if not isinstance(fracture, dict):
        errors.append("missing lot.fracture")
        return False, errors

    model = fracture.get("fracture_model")
    diagnostics = fracture.get("fracture_gate_diagnostics")

    if path.name == "limited_gate_disabled_default.yaml":
        if model != "PKN":
            errors.append("default-disabled fixture must use PKN")
        if diagnostics is not None:
            errors.append("default-disabled fixture must omit diagnostics block")
    else:
        if not isinstance(diagnostics, dict):
            errors.append("missing fracture_gate_diagnostics")
        else:
            if diagnostics.get("enabled") is not True:
                errors.append("diagnostics.enabled must be true")
            if diagnostics.get("mode") != "limited_gate":
                errors.append("diagnostics.mode must be limited_gate")
            dispatch = diagnostics.get("dispatch_runtime_enabled")
            if path.name == "limited_gate_dispatch_true_invalid.yaml":
                if dispatch is not True:
                    errors.append("dispatch-true fixture must set dispatch true")
            elif dispatch is not False:
                errors.append("dispatch_runtime_enabled must be false")

    if path.name == "limited_gate_enabled_penny.yaml":
        if model != "PENNY_SHAPED":
            errors.append("expected PENNY_SHAPED fracture_model")
        if isinstance(expected, dict):
            if expected.get("physically_validated") is not False:
                errors.append("PENNY_SHAPED fixture must be non-physical")
            if expected.get("legacy_equivalent") is not False:
                errors.append("PENNY_SHAPED fixture must not claim legacy equivalence")
            if expected.get("penny_shaped_runtime_enabled") is not False:
                errors.append("PENNY_SHAPED runtime must remain disabled")
    elif path.name == "limited_gate_invalid_model_blocked.yaml":
        if model == "PKN" or model == "PENNY_SHAPED":
            errors.append("invalid-model fixture must use unsupported model")
    elif model != "PKN":
        errors.append("expected PKN fracture_model")

    if isinstance(expected, dict):
        if expected.get("runtime_dispatch_enabled") is not False:
            errors.append("runtime dispatch must remain false")
        if expected.get("runtime_physical_dispatch_enabled") is not False:
            errors.append("runtime physical dispatch must remain false")
        if expected.get("buz29_execution_allowed") is not False:
            errors.append("BUZ29 execution must remain false")
        if expected.get("penny_shaped_runtime_enabled") is not False:
            errors.append("PENNY_SHAPED runtime must remain disabled")
    return not errors, errors


def validate_fixtures(fixtures_dir: Path) -> dict[str, Any]:
    coverage = {value: False for value in EXPECTED_FIXTURES.values()}
    details: dict[str, Any] = {}
    errors: list[str] = []

    if not fixtures_dir.exists() or not fixtures_dir.is_dir():
        errors.append(f"fixtures directory not found: {fixtures_dir}")

    metadata, metadata_errors = _validate_metadata(fixtures_dir)
    errors.extend(metadata_errors)

    for filename, coverage_key in EXPECTED_FIXTURES.items():
        path = fixtures_dir / filename
        if not path.exists():
            errors.append(f"missing fixture: {filename}")
            details[filename] = {"present": False, "valid": False}
            continue
        valid, fixture_errors = _validate_fixture(path)
        coverage[coverage_key] = valid
        details[filename] = {
            "present": True,
            "valid": valid,
            "errors": fixture_errors,
        }
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    yaml_count = len(list(fixtures_dir.glob("*.yaml"))) if fixtures_dir.exists() else 0
    if yaml_count < 6:
        errors.append("fixtures directory must contain at least 6 YAML fixtures")

    fixture_status = VALID_STATUS if not errors and all(coverage.values()) else INVALID_STATUS
    return {
        "phase": "11.11F",
        "fixture_status": fixture_status,
        "fixture_count": sum(1 for item in details.values() if item["present"]),
        "limited_gate_mode_supported": metadata.get("limited_gate_mode_supported") is True,
        **coverage,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "recommended_next_phase": "PHASE11_11G_VALIDATE_LIMITED_GATE_ON_CONTROLLED_CASES",
        "errors": errors,
        "fixtures": details,
        "metadata": metadata,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11F limited_gate fixtures",
        "",
        f"- phase: `{report['phase']}`",
        f"- fixture_status: `{report['fixture_status']}`",
        f"- fixture_count: `{report['fixture_count']}`",
        f"- limited_gate_mode_supported: `{report['limited_gate_mode_supported']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        f"- pkn_behavior_change_allowed: `{report['pkn_behavior_change_allowed']}`",
        f"- penny_shaped_runtime_enabled: `{report['penny_shaped_runtime_enabled']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Coverage",
        "",
    ]
    for key in EXPECTED_FIXTURES.values():
        lines.append(f"- {key}: `{report[key]}`")
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 11.11F limited_gate fixtures."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase11_11f"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = validate_fixtures(args.fixtures_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"fixture_status={report['fixture_status']}")
    print(f"fixture_count={report['fixture_count']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    for error in report["errors"]:
        print(f"error={error}")
    return 0 if report["fixture_status"] == VALID_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
