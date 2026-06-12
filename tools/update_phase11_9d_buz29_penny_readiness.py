#!/usr/bin/env python3
"""Update BUZ29 PennyShaped readiness using Phase 11.9C evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_phase11_9c_buz29_penny_evidence import audit_sources, default_sources


def update_readiness(evidence_result: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence_result = evidence_result or audit_sources(default_sources())
    evidence = evidence_result["evidence"]
    classification = evidence_result["classification"]

    pressure_ok = evidence["pressure_history"]["status"] == "FOUND" and evidence["pressure_history"]["consumable"]
    opening_ok = evidence["opening_time"]["status"] == "FOUND" and evidence["opening_time"]["consumable"]
    adapter_inputs_ok = evidence["penny_inputs"]["status"] == "FOUND" and evidence["penny_inputs"]["consumable"]

    if classification == "BUZ29_PENNY_EVIDENCE_COMPLETE":
        updated = "BUZ29_PENNY_CANDIDATE_READY"
        can_start = True
        gate = "BUZ29_PENNY_READY_START_11_10A"
        next_phase = "PHASE11_10A_BUZ29_PENNY_DIAGNOSTIC_ROUTE"
    elif classification == "BUZ29_PENNY_EVIDENCE_PARTIAL" and pressure_ok and opening_ok and adapter_inputs_ok:
        updated = "BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE"
        can_start = True
        gate = "BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A"
        next_phase = "PHASE11_10A_BUZ29_PENNY_DIAGNOSTIC_ROUTE"
    elif classification == "BUZ29_PENNY_EVIDENCE_PARTIAL":
        updated = "BUZ29_PENNY_CANDIDATE_PARTIAL"
        can_start = False
        gate = "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
        next_phase = "PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE"
    elif classification in {"BUZ29_PENNY_EVIDENCE_BLOCKED", "BUZ29_PENNY_EVIDENCE_NOT_FOUND"}:
        updated = "BUZ29_PENNY_CANDIDATE_BLOCKED"
        can_start = False
        gate = "BUZ29_PENNY_BLOCKED_DO_NOT_START_11_10A"
        next_phase = "PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE"
    else:
        updated = "BUZ29_PENNY_CANDIDATE_INCONCLUSIVE"
        can_start = False
        gate = "BUZ29_PENNY_INCONCLUSIVE_DO_NOT_START_11_10A"
        next_phase = "PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE"

    return {
        "phase": "11.9D",
        "previous_readiness": "BUZ29_PENNY_CANDIDATE_PARTIAL",
        "evidence_classification": classification,
        "updated_readiness": updated,
        "can_start_11_10A": can_start,
        "gate": gate,
        "blocking_gaps": evidence_result["blocking_gaps"],
        "recommended_next_phase": next_phase,
        "pressure_history_consumable": pressure_ok,
        "opening_time_consumable": opening_ok,
        "adapter_inputs_consumable": adapter_inputs_ok,
        "physical_validation": False,
        "legacy_equivalence": False,
        "caveats": [
            "The readiness update does not validate BUZ29.",
            "Phase 11.10A must remain blocked when pressure history or opening time is not consumable.",
            "No BUZ29 candidate YAML is created by Phase 11.9D.",
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.9D BUZ29 PennyShaped Readiness Update",
        "",
        f"- previous_readiness: `{result['previous_readiness']}`",
        f"- evidence_classification: `{result['evidence_classification']}`",
        f"- updated_readiness: `{result['updated_readiness']}`",
        f"- can_start_11_10A: `{str(result['can_start_11_10A']).lower()}`",
        f"- gate: `{result['gate']}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Blocking Gaps",
        "",
    ]
    lines.extend(f"- `{gap}`" for gap in result["blocking_gaps"] or ["none"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update BUZ29 PennyShaped readiness using Phase 11.9C evidence."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = update_readiness()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)
    print("PHASE=11.9D")
    print(f"UPDATED_READINESS={result['updated_readiness']}")
    print(f"CAN_START_11_10A={str(result['can_start_11_10A']).lower()}")
    print(f"GATE={result['gate']}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
