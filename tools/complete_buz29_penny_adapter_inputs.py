#!/usr/bin/env python3
"""Evaluate whether BUZ29/PENNY adapter inputs are complete and safe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_COMPLETE_BUZ29_PENNY_ADAPTER_INPUTS"
SAFE_STATUSES = {
    "AVAILABLE_DIRECT",
    "AVAILABLE_DERIVED_SAFE",
    "AVAILABLE_FROM_DIAGNOSTIC_SOURCE",
    "AVAILABLE_FROM_PROVIDER",
}
AMBIGUOUS_STATUS = "AMBIGUOUS_SEMANTICS"
MISSING_STATUSES = {"MISSING", "BLOCKED"}

STATUS_COMPLETE = "BUZ29_PENNY_ADAPTER_INPUTS_COMPLETE"
STATUS_COMPLETED_DIAGNOSTIC = (
    "BUZ29_PENNY_ADAPTER_INPUTS_COMPLETED_FROM_DIAGNOSTIC_SOURCES"
)
STATUS_PARTIAL = "BUZ29_PENNY_ADAPTER_INPUTS_STILL_PARTIAL"
STATUS_BLOCKED_UNAVAILABLE = (
    "BUZ29_PENNY_ADAPTER_INPUTS_BLOCKED_BY_UNAVAILABLE_SOURCE"
)
STATUS_BLOCKED_AMBIGUOUS = (
    "BUZ29_PENNY_ADAPTER_INPUTS_BLOCKED_BY_AMBIGUOUS_SEMANTICS"
)


def _load_matrix(path: Path) -> dict[str, Any]:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(matrix, dict):
        raise ValueError("input matrix must be a JSON object")
    if matrix.get("phase") != PHASE:
        raise ValueError(f"unexpected phase: {matrix.get('phase')}")
    return matrix


def _required_fields(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    fields = matrix.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("matrix.fields must be a non-empty list")
    required: list[dict[str, Any]] = []
    for field in fields:
        if not isinstance(field, dict) or not field.get("name"):
            raise ValueError("each field entry must be an object with a name")
        if field.get("required") is True:
            required.append(field)
    if not required:
        raise ValueError("matrix must define at least one required field")
    return required


def evaluate_matrix(matrix_path: Path) -> dict[str, Any]:
    matrix = _load_matrix(matrix_path)
    if matrix.get("diagnostic_only") is not True:
        raise ValueError("diagnostic_only must be true")
    if matrix.get("physically_validated") is not False:
        raise ValueError("physically_validated must be false")
    if matrix.get("legacy_equivalent") is not False:
        raise ValueError("legacy_equivalent must be false")
    if matrix.get("runtime_dispatch_enabled") is not False:
        raise ValueError("runtime_dispatch_enabled must be false")

    required = _required_fields(matrix)
    blocking_fields = [
        str(field["name"])
        for field in required
        if field.get("status") in MISSING_STATUSES
        or field.get("can_use_for_buz29_diagnostic") is not True
        and field.get("status") not in {AMBIGUOUS_STATUS}
    ]
    ambiguous_fields = [
        str(field["name"])
        for field in required
        if field.get("status") == AMBIGUOUS_STATUS
    ]
    safe_fields = [
        str(field["name"])
        for field in required
        if field.get("status") in SAFE_STATUSES
        and field.get("can_use_for_buz29_diagnostic") is True
    ]
    diagnostic_source_fields = [
        str(field["name"])
        for field in required
        if field.get("status") == "AVAILABLE_FROM_DIAGNOSTIC_SOURCE"
        and field.get("can_use_for_buz29_diagnostic") is True
    ]

    all_required_inputs_complete = len(safe_fields) == len(required)
    if all_required_inputs_complete and diagnostic_source_fields:
        input_status = STATUS_COMPLETED_DIAGNOSTIC
        recommended_next_phase = "PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_WITH_RUNNER"
    elif all_required_inputs_complete:
        input_status = STATUS_COMPLETE
        recommended_next_phase = "PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_WITH_RUNNER"
    elif ambiguous_fields and not blocking_fields:
        input_status = STATUS_BLOCKED_AMBIGUOUS
        recommended_next_phase = "PHASE_RESOLVE_BUZ29_PENNY_AMBIGUOUS_ADAPTER_FIELDS"
    elif blocking_fields:
        input_status = STATUS_PARTIAL
        recommended_next_phase = "PHASE_RESOLVE_BUZ29_PENNY_BLOCKING_ADAPTER_FIELDS"
    else:
        input_status = STATUS_BLOCKED_UNAVAILABLE
        recommended_next_phase = "PHASE_RESOLVE_BUZ29_PENNY_BLOCKING_ADAPTER_FIELDS"

    resolved_input_created = (
        matrix.get("resolved_input_created") is True and all_required_inputs_complete
    )
    return {
        "phase": PHASE,
        "case_id": matrix.get("case_id", "BUZ29_PENNY_DIAGNOSTIC"),
        "adapter": matrix.get("adapter", "PennyShapedDiagnosticAdapter"),
        "input_status": input_status,
        "all_required_inputs_complete": all_required_inputs_complete,
        "resolved_input_created": resolved_input_created,
        "diagnostic_only": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "safe_fields": safe_fields,
        "blocking_fields": blocking_fields,
        "ambiguous_fields": ambiguous_fields,
        "safe_fields_count": len(safe_fields),
        "blocking_fields_count": len(blocking_fields),
        "ambiguous_fields_count": len(ambiguous_fields),
        "required_fields_count": len(required),
        "matrix": str(matrix_path),
        "recommended_next_phase": recommended_next_phase,
        "forbidden_substitutions": list(matrix.get("forbidden_substitutions", [])),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# BUZ29 Penny adapter input completion",
        "",
        f"- phase: `{report['phase']}`",
        f"- input_status: `{report['input_status']}`",
        f"- all_required_inputs_complete: `{report['all_required_inputs_complete']}`",
        f"- resolved_input_created: `{report['resolved_input_created']}`",
        f"- diagnostic_only: `{report['diagnostic_only']}`",
        f"- physically_validated: `{report['physically_validated']}`",
        f"- legacy_equivalent: `{report['legacy_equivalent']}`",
        f"- runtime_dispatch_enabled: `{report['runtime_dispatch_enabled']}`",
        f"- recommended_next_phase: `{report['recommended_next_phase']}`",
        "",
        "## Safe Fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in report["safe_fields"] or ["none"])
    lines.extend(["", "## Blocking Fields", ""])
    lines.extend(f"- `{field}`" for field in report["blocking_fields"] or ["none"])
    lines.extend(["", "## Ambiguous Fields", ""])
    lines.extend(f"- `{field}`" for field in report["ambiguous_fields"] or ["none"])
    lines.extend(["", "## Forbidden Substitutions", ""])
    lines.extend(
        f"- {item}" for item in report["forbidden_substitutions"] or ["none"]
    )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate BUZ29/PENNY PennyShapedDiagnosticAdapter input completeness."
    )
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = evaluate_matrix(args.matrix)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"input_status={report['input_status']}")
    print(f"all_required_inputs_complete={report['all_required_inputs_complete']}")
    print(f"blocking_fields_count={report['blocking_fields_count']}")
    print(f"ambiguous_fields_count={report['ambiguous_fields_count']}")
    print(f"recommended_next_phase={report['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
