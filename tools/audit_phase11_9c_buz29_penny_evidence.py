#!/usr/bin/env python3
"""Audit BUZ29 evidence for a future PennyShaped diagnostic route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CRITICAL_FIELDS = {
    "pressure_history",
    "sigmaTheta_history",
    "opening_time",
    "time_since_opening",
    "penny_inputs",
}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _entry(status: str, source: str, consumable: bool, notes: str) -> dict[str, Any]:
    return {
        "status": status,
        "source": source,
        "consumable": consumable,
        "notes": notes,
    }


def default_sources() -> dict[str, Path]:
    return {
        "first_well_source": Path("legance/LOT_Tese/BUZ29-VISCO-first-well.cpp"),
        "first_well_audit": Path("docs/57_buz29_visco_first_well_audit.md"),
        "roadmap": Path("docs/58_non_pkn_model_roadmap.md"),
        "math_audit": Path("docs/61_selected_non_pkn_model_math_audit.md"),
        "yaml_spec": Path("docs/62_selected_non_pkn_model_yaml_io_spec.md"),
        "minimal_impl": Path("docs/63_selected_non_pkn_model_minimal_implementation.md"),
        "adapter_spec": Path("docs/65_penny_diagnostic_adapter_spec.md"),
        "adapter_impl": Path("docs/66_penny_diagnostic_adapter_implementation.md"),
        "synthetic_case_doc": Path("docs/67_penny_synthetic_minimal_case.md"),
        "readiness_doc": Path("docs/68_buz29_penny_candidate_readiness.md"),
        "synthetic_case": Path("cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml"),
        "pressure_visualizer": Path("legance/LOT_Tese/PressureDataVisualizer29D-RAA.py"),
    }


def audit_sources(sources: dict[str, Path]) -> dict[str, Any]:
    first_well = _read(sources["first_well_source"])
    first_well_audit = _read(sources["first_well_audit"])
    math_audit = _read(sources["math_audit"])
    adapter_impl = _read(sources["adapter_impl"])
    synthetic_case = _read(sources["synthetic_case"])
    readiness = _read(sources["readiness_doc"])
    pressure_visualizer = _read(sources["pressure_visualizer"])

    source_statuses = []
    if sources["first_well_source"].exists() and "penny-shaped" in first_well:
        source_statuses.append("BUZ29_EXACT_SOURCE_FOUND")
    if "results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat" in first_well_audit:
        source_statuses.append("BUZ29_CANDIDATE_SOURCE_FOUND")
    if pressure_visualizer and "dP" in pressure_visualizer:
        source_statuses.append("BUZ29_EVIDENCE_SOURCE_FOUND")
    if not source_statuses:
        source_statuses.append("BUZ29_EVIDENCE_SOURCE_NOT_FOUND")

    evidence = {
        "pressure_history": _entry(
            "PARTIAL" if pressure_visualizer else "MISSING",
            "legance/LOT_Tese/PressureDataVisualizer29D-RAA.py"
            if pressure_visualizer
            else "not found",
            False,
            "There is a legacy plotting/parser script for 29D pressure outputs, but no versioned BUZ29 pressure history is mapped to the PennyShaped adapter contract.",
        ),
        "sigmaTheta_history": _entry(
            "MISSING",
            "docs/68_buz29_penny_candidate_readiness.md",
            False,
            "No BUZ29 sigmaTheta time history consumable by the adapter was found.",
        ),
        "opening_time": _entry(
            "MISSING",
            "docs/68_buz29_penny_candidate_readiness.md",
            False,
            "No traceable BUZ29 opening/fracture time was found.",
        ),
        "time_since_opening": _entry(
            "MISSING",
            "docs/68_buz29_penny_candidate_readiness.md",
            False,
            "The PennyShaped adapter requires elapsed_since_opening_min, but BUZ29 does not yet provide a consumable opening-time reference.",
        ),
        "apb_salt_state": _entry(
            "PARTIAL" if "APB1da simulation" in first_well_audit else "MISSING",
            "docs/57_buz29_visco_first_well_audit.md",
            False,
            "The APB1da setup is documented, but a consumable APB/salt state trace aligned with the fracture criterion is not available.",
        ),
        "fracture_state": _entry(
            "PARTIAL" if "penny-shaped" in first_well_audit else "MISSING",
            "docs/57_buz29_visco_first_well_audit.md",
            False,
            "The active legacy fracture model is penny-shaped, but no modern diagnostic state history is available.",
        ),
        "leakoff_state": _entry(
            "PARTIAL" if "leakoff" in readiness.lower() or "setLeakoffProps" in first_well else "MISSING",
            "legance/LOT_Tese/BUZ29-VISCO-first-well.cpp",
            False,
            "Leakoff-related legacy setup can be located, but it is not converted into a consumable diagnostic series.",
        ),
        "fluid_state": _entry(
            "PARTIAL" if "setPFluid" in first_well_audit else "MISSING",
            "docs/57_buz29_visco_first_well_audit.md",
            False,
            "Fluid density/compressibility/alpha were audited, but viscosity and all adapter fluid inputs are not yet complete in a BUZ29 contract.",
        ),
        "wellbore_geometry": _entry(
            "PARTIAL" if "Intervalo principal" in first_well_audit else "MISSING",
            "docs/57_buz29_visco_first_well_audit.md",
            False,
            "Depth interval evidence exists, but a full consumable geometry contract for BUZ29-PENNY is not assembled.",
        ),
        "elastic_properties": _entry(
            "PARTIAL" if "Penny" in math_audit or "penny" in math_audit else "MISSING",
            "docs/61_selected_non_pkn_model_math_audit.md",
            False,
            "Penny-shaped formulas and required elastic inputs are documented, but BUZ29-specific values are not yet packaged as a candidate case.",
        ),
        "penny_inputs": _entry(
            "PARTIAL"
            if "PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED" in adapter_impl
            and "Synthetic diagnostic case only" in synthetic_case
            else "MISSING",
            "docs/66_penny_diagnostic_adapter_implementation.md; cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml",
            False,
            "The adapter and synthetic inputs exist, but BUZ29 lacks pressure, sigmaTheta and elapsed-opening-time fields needed for a consumable diagnostic input.",
        ),
        "legacy_trace": _entry(
            "PARTIAL" if "results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat" in first_well_audit else "MISSING",
            "docs/57_buz29_visco_first_well_audit.md",
            False,
            "A legacy output filename is documented, but the trace has not been normalized into a versioned, adapter-ready evidence package.",
        ),
    }

    blocking_gaps = [
        key
        for key in sorted(CRITICAL_FIELDS)
        if evidence[key]["status"] != "FOUND" or not evidence[key]["consumable"]
    ]

    if not sources["first_well_source"].exists():
        classification = "BUZ29_PENNY_EVIDENCE_NOT_FOUND"
    elif all(evidence[key]["status"] == "FOUND" and evidence[key]["consumable"] for key in CRITICAL_FIELDS):
        classification = "BUZ29_PENNY_EVIDENCE_COMPLETE"
    elif "penny-shaped" in first_well_audit and "PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED" in adapter_impl:
        classification = "BUZ29_PENNY_EVIDENCE_PARTIAL"
    else:
        classification = "BUZ29_PENNY_EVIDENCE_BLOCKED"

    return {
        "phase": "11.9C",
        "case": "BUZ29-VISCO-first-well",
        "track": "PENNY_SHAPED",
        "classification": classification,
        "source_statuses": source_statuses,
        "evidence": evidence,
        "blocking_gaps": blocking_gaps,
        "can_update_readiness": classification in {
            "BUZ29_PENNY_EVIDENCE_COMPLETE",
            "BUZ29_PENNY_EVIDENCE_PARTIAL",
            "BUZ29_PENNY_EVIDENCE_BLOCKED",
        },
        "can_start_11_10a": False,
        "recommended_next_phase": "PHASE11_9D_UPDATE_BUZ29_PENNY_READINESS",
        "physical_validation": False,
        "legacy_equivalence": False,
        "simulation_executed": False,
        "caveats": [
            "Phase 11.9C does not start the BUZ29-PENNY route and does not run simulation.",
            "Partial legacy evidence is not equivalent to consumable adapter inputs.",
            "BUZ29 must not advance to Phase 11.10A unless Phase 11.9D explicitly opens that gate.",
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.9C BUZ29 PennyShaped Evidence Audit",
        "",
        f"- classification: `{result['classification']}`",
        f"- can_update_readiness: `{str(result['can_update_readiness']).lower()}`",
        f"- can_start_11_10a: `{str(result['can_start_11_10a']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Source Statuses",
        "",
    ]
    lines.extend(f"- `{item}`" for item in result["source_statuses"])
    lines.extend(
        [
            "",
            "## Evidence Map",
            "",
            "| Field | Status | Consumable | Source | Notes |",
            "|---|---|---:|---|---|",
        ]
    )
    for field, item in result["evidence"].items():
        notes = str(item["notes"]).replace("|", "/")
        source = str(item["source"]).replace("|", "/")
        lines.append(
            f"| `{field}` | `{item['status']}` | `{str(item['consumable']).lower()}` | `{source}` | {notes} |"
        )
    lines.extend(["", "## Blocking Gaps", ""])
    lines.extend(f"- `{item}`" for item in result["blocking_gaps"] or ["none"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit BUZ29 evidence for a future PennyShaped diagnostic route."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = audit_sources(default_sources())
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)
    print("PHASE=11.9C")
    print(f"CLASSIFICATION={result['classification']}")
    print(f"CAN_UPDATE_READINESS={str(result['can_update_readiness']).lower()}")
    print(f"CAN_START_11_10A={str(result['can_start_11_10a']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
