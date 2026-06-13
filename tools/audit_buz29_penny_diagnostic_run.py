#!/usr/bin/env python3
"""Audit the BUZ29/PENNY diagnostic run attempt without enabling runtime dispatch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_COMPARISON"
COMPLETED_STATUS = "BUZ29_PENNY_DIAGNOSTIC_RUN_COMPLETED"
BLOCKED_STATUS = "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED"
DEFAULT_SUMMARY = Path(
    "tests/fixtures/comparison/phase_buz29_penny_diagnostic_run/"
    "buz29_penny_diagnostic_run_summary.json"
)
REQUIRED_CAVEATS = {
    "NO_PHYSICAL_VALIDATION",
    "NO_LEGACY_EQUIVALENCE",
    "NO_RUNTIME_DISPATCH",
}


def audit_diagnostic_run(summary_path: Path = DEFAULT_SUMMARY) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("phase") != PHASE:
        raise ValueError(f"unexpected phase: {summary.get('phase')}")

    execution_completed = summary.get("execution_completed") is True
    caveats = set(summary.get("blocking_caveats", []))
    safety_flags_ok = (
        summary.get("diagnostic_only") is True
        and summary.get("physically_validated") is False
        and summary.get("legacy_equivalent") is False
        and summary.get("runtime_dispatch_enabled") is False
        and summary.get("penny_shaped_runtime_enabled") is False
        and summary.get("pkn_behavior_changed") is False
        and summary.get("physical_validation_claimed") is False
        and summary.get("legacy_equivalence_claimed") is False
        and REQUIRED_CAVEATS.issubset(caveats)
    )
    if not safety_flags_ok:
        raise ValueError("diagnostic run summary violates required safety flags")

    blocked_reasons = list(summary.get("blocking_reasons", []))
    run_status = COMPLETED_STATUS if execution_completed else BLOCKED_STATUS
    recommended_next_phase = (
        "PHASE_DECIDE_BUZ29_PENNY_DIAGNOSTIC_RUN_READINESS"
        if execution_completed
        else "PHASE_FIX_BUZ29_PENNY_DIAGNOSTIC_RUNNER"
    )

    return {
        "phase": PHASE,
        "run_status": run_status,
        "execution_status": summary.get("execution_status", run_status),
        "execution_completed": execution_completed,
        "diagnostic_only": True,
        "physically_validated": False,
        "legacy_equivalent": False,
        "runtime_dispatch_enabled": False,
        "penny_shaped_runtime_enabled": False,
        "pkn_behavior_changed": False,
        "physical_validation_claimed": False,
        "legacy_equivalence_claimed": False,
        "diagnostic_route_located": summary.get("diagnostic_route_located") is True,
        "diagnostic_runner_available": summary.get("diagnostic_runner_available")
        is True,
        "adapter_ready": summary.get("adapter_ready") is True,
        "partial_adapter_ready": summary.get("partial_adapter_ready") is True,
        "writer_available": summary.get("writer_available") is True,
        "outputs_generated": list(summary.get("outputs_generated", [])),
        "blocking_reasons": blocked_reasons,
        "blocking_caveats": list(summary.get("blocking_caveats", [])),
        "recommended_next_phase": recommended_next_phase,
    }


def write_outputs(result: dict[str, Any], output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# BUZ29 Penny Diagnostic Run Audit",
            "",
            f"- phase: `{result['phase']}`",
            f"- run_status: `{result['run_status']}`",
            f"- execution_status: `{result['execution_status']}`",
            f"- execution_completed: `{str(result['execution_completed']).lower()}`",
            f"- diagnostic_only: `{str(result['diagnostic_only']).lower()}`",
            f"- physically_validated: `{str(result['physically_validated']).lower()}`",
            f"- legacy_equivalent: `{str(result['legacy_equivalent']).lower()}`",
            f"- runtime_dispatch_enabled: `{str(result['runtime_dispatch_enabled']).lower()}`",
            f"- pkn_behavior_changed: `{str(result['pkn_behavior_changed']).lower()}`",
            f"- recommended_next_phase: `{result['recommended_next_phase']}`",
            "",
            "## Blocking Reasons",
            "",
        ]
        lines.extend(f"- `{reason}`" for reason in result["blocking_reasons"] or ["none"])
        lines.extend(
            [
                "",
                "The diagnostic route remains non-physical. No BUZ29/PENNY runtime "
                "execution was performed and no legacy equivalence is claimed.",
                "",
            ]
        )
        output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the BUZ29/PENNY diagnostic run attempt."
    )
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = audit_diagnostic_run(args.summary)
    write_outputs(result, args.output_json, args.output_md)
    print(f"phase={result['phase']}")
    print(f"run_status={result['run_status']}")
    print(f"execution_completed={result['execution_completed']}")
    print(f"diagnostic_only={result['diagnostic_only']}")
    print(f"runtime_dispatch_enabled={result['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
