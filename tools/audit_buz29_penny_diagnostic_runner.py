#!/usr/bin/env python3
"""Audit the isolated BUZ29/PENNY diagnostic runner contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_FIX_BUZ29_PENNY_DIAGNOSTIC_RUNNER"
FIXTURE_DIR = Path(
    "tests/fixtures/comparison/phase_buz29_penny_diagnostic_runner"
)
RUNNER_STATUS = "BUZ29_PENNY_DIAGNOSTIC_RUNNER_IMPLEMENTED_INPUTS_PARTIAL"
REQUIRED_FIXTURES = {
    "runner_valid_complete_inputs.json": "synthetic_complete_case_runs",
    "runner_partial_inputs_blocked.json": "partial_inputs_blocked",
    "runner_invalid_physically_validated_true.json": "invalid_physically_validated_rejected",
    "runner_invalid_legacy_equivalent_true.json": "invalid_legacy_equivalent_rejected",
    "runner_invalid_runtime_dispatch_true.json": "invalid_runtime_dispatch_rejected",
    "runner_invalid_model_pkn.json": "unsupported_model_rejected",
}
REQUIRED_CAVEATS = {
    "DIAGNOSTIC_ONLY",
    "NOT_PHYSICALLY_VALIDATED",
    "NOT_LEGACY_EQUIVALENT",
    "NO_RUNTIME_DISPATCH",
    "PENNY_SHAPED_DIAGNOSTIC_ONLY",
    "BUZ29_REAL_INPUTS_NOT_IMPROVISED",
}


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def _fixture_valid(name: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if data.get("phase") != PHASE:
        errors.append("phase mismatch")
    if data.get("diagnostic_only") is not True:
        errors.append("diagnostic_only must be true")
    if data.get("penny_shaped_runtime_enabled") is not False:
        errors.append("penny_shaped_runtime_enabled must be false")
    if data.get("pkn_behavior_changed") is not False:
        errors.append("pkn_behavior_changed must be false")

    if name == "runner_valid_complete_inputs.json":
        if data.get("expected_status") != "BUZ29_PENNY_DIAGNOSTIC_RUN_COMPLETED":
            errors.append("complete fixture expected status mismatch")
        if data.get("adapter_inputs_complete") is not True:
            errors.append("complete fixture must have adapter inputs complete")
        if data.get("fracture_model") != "PENNY_SHAPED":
            errors.append("complete fixture must use PENNY_SHAPED")
        if not REQUIRED_CAVEATS.issubset(set(data.get("caveats", []))):
            errors.append("complete fixture missing required caveats")
    elif name == "runner_partial_inputs_blocked.json":
        if data.get("expected_status") != (
            "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED_BY_PARTIAL_INPUTS"
        ):
            errors.append("partial fixture expected status mismatch")
        if data.get("adapter_inputs_complete") is not False:
            errors.append("partial fixture must have incomplete adapter inputs")
        if not data.get("missing_adapter_fields"):
            errors.append("partial fixture must list missing adapter fields")
    elif name == "runner_invalid_model_pkn.json":
        if data.get("expected_status") != (
            "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_UNSUPPORTED_MODEL"
        ):
            errors.append("unsupported-model expected status mismatch")
        if data.get("fracture_model") == "PENNY_SHAPED":
            errors.append("unsupported-model fixture must not use PENNY_SHAPED")
    else:
        if data.get("expected_status") != (
            "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_INVALID_FLAGS"
        ):
            errors.append("invalid-flag expected status mismatch")
        if name == "runner_invalid_physically_validated_true.json" and (
            data.get("physically_validated") is not True
        ):
            errors.append("physically_validated invalid fixture must set true")
        if name == "runner_invalid_legacy_equivalent_true.json" and (
            data.get("legacy_equivalent") is not True
        ):
            errors.append("legacy_equivalent invalid fixture must set true")
        if name == "runner_invalid_runtime_dispatch_true.json" and (
            data.get("runtime_dispatch_enabled") is not True
        ):
            errors.append("runtime dispatch invalid fixture must set true")
    return not errors, errors


def audit_runner(fixtures_dir: Path = FIXTURE_DIR) -> dict[str, Any]:
    errors: list[str] = []
    coverage = {key: False for key in REQUIRED_FIXTURES.values()}
    fixtures: dict[str, Any] = {}

    if not fixtures_dir.exists() or not fixtures_dir.is_dir():
      errors.append(f"fixtures directory not found: {fixtures_dir}")

    for filename, coverage_key in REQUIRED_FIXTURES.items():
        path = fixtures_dir / filename
        if not path.exists():
            errors.append(f"missing fixture: {filename}")
            fixtures[filename] = {"present": False, "valid": False}
            continue
        data = _load_json(path)
        valid, fixture_errors = _fixture_valid(filename, data)
        coverage[coverage_key] = valid
        fixtures[filename] = {
            "present": True,
            "valid": valid,
            "expected_status": data.get("expected_status"),
            "errors": fixture_errors,
        }
        errors.extend(f"{filename}: {error}" for error in fixture_errors)

    invalid_flags_rejected = (
        coverage["invalid_physically_validated_rejected"]
        and coverage["invalid_legacy_equivalent_rejected"]
        and coverage["invalid_runtime_dispatch_rejected"]
    )
    buz29_candidate_inputs_complete = False
    status = (
        RUNNER_STATUS
        if coverage["synthetic_complete_case_runs"]
        and coverage["partial_inputs_blocked"]
        and invalid_flags_rejected
        and coverage["unsupported_model_rejected"]
        and not errors
        else "BUZ29_PENNY_DIAGNOSTIC_RUNNER_INCONCLUSIVE"
    )

    return {
        "phase": PHASE,
        "runner_status": status,
        "synthetic_complete_case_runs": coverage["synthetic_complete_case_runs"],
        "partial_inputs_blocked": coverage["partial_inputs_blocked"],
        "invalid_flags_rejected": invalid_flags_rejected,
        "unsupported_model_rejected": coverage["unsupported_model_rejected"],
        "diagnostic_only": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "penny_shaped_runtime_enabled": False,
        "pkn_behavior_changed": False,
        "physical_validation_claimed": False,
        "legacy_equivalence_claimed": False,
        "buz29_candidate_inputs_complete": buz29_candidate_inputs_complete,
        "recommended_next_phase": "PHASE_COMPLETE_BUZ29_PENNY_ADAPTER_INPUTS",
        "required_caveats": sorted(REQUIRED_CAVEATS),
        "fixtures": fixtures,
        "errors": errors,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# BUZ29 Penny Diagnostic Runner Audit",
        "",
        f"- phase: `{report['phase']}`",
        f"- runner_status: `{report['runner_status']}`",
        f"- synthetic_complete_case_runs: `{report['synthetic_complete_case_runs']}`",
        f"- partial_inputs_blocked: `{report['partial_inputs_blocked']}`",
        f"- invalid_flags_rejected: `{report['invalid_flags_rejected']}`",
        f"- unsupported_model_rejected: `{report['unsupported_model_rejected']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- penny_shaped_runtime_enabled: `{report['penny_shaped_runtime_enabled']}`",
        f"- buz29_candidate_inputs_complete: `{report['buz29_candidate_inputs_complete']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- `{caveat}`" for caveat in report["required_caveats"])
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the isolated BUZ29/PENNY diagnostic runner contract."
    )
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = audit_runner(args.fixtures_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"runner_status={report['runner_status']}")
    print(f"synthetic_complete_case_runs={report['synthetic_complete_case_runs']}")
    print(f"partial_inputs_blocked={report['partial_inputs_blocked']}")
    print(f"runtime_dispatch_enabled={report['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    for error in report["errors"]:
        print(f"error={error}")
    return 0 if report["runner_status"] == RUNNER_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
