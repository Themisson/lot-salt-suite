#!/usr/bin/env python3
"""Inspect BUZ29 PennyShaped candidate inputs against the diagnostic adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PHASE = "11.10B"
CASE_ID = "buz29_penny_candidate"

CLASS_READY = "BUZ29_PENNY_ADAPTER_INPUTS_READY"
CLASS_PARTIAL = "BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL"
CLASS_BLOCKED = "BUZ29_PENNY_ADAPTER_INPUTS_BLOCKED"
CLASS_INCONCLUSIVE = "BUZ29_PENNY_ADAPTER_INPUTS_INCONCLUSIVE"

NEXT_MATH_AUDIT = "PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD"
NEXT_COMPLETE_INPUTS = "PHASE11_10C_COMPLETE_BUZ29_PENNY_ADAPTER_INPUTS"
NEXT_RESOLVE_SEMANTICS = "PHASE11_10C_RESOLVE_BUZ29_PENNY_INPUT_SEMANTICS"

AXISYMMETRIC_CAVEAT = "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED"
FUTURE_OUTPUT_REQUIREMENT = "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED"

REQUIRED_ADAPTER_FIELDS = [
    "young_modulus_Pa",
    "poisson_ratio",
    "viscosity_Pa_min",
    "flow_rate_m3_min",
    "elapsed_since_opening_min",
    "wellbore_pressure_Pa",
    "sigma_theta_compression_positive_Pa",
    "volume_multiplier",
]

ADAPTER_OUTPUT_FIELDS = [
    "plane_strain_modulus_Pa",
    "opening_m",
    "radius_m",
    "pressure_factor",
    "fracture_volume_proxy_m3",
]

DEFERRED_FIELDS = [
    "sigmaTheta",
    "pw",
    "margin",
    "opened",
    "full physical validation",
    "mathematical audit of PennyShapedModel",
    "runtime non-PKN runner",
    "explicit 1rad/2pi volume output conversion",
]


def load_candidate(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"candidate YAML not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("candidate YAML root must be a mapping")
    return data


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def mapping(
    adapter_field: str,
    status: str,
    source: str,
    source_field: str,
    unit: str,
    conversion: str,
    consumable: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "adapter_field": adapter_field,
        "status": status,
        "source": source,
        "source_field": source_field,
        "unit": unit,
        "conversion": conversion,
        "consumable": consumable,
        "notes": notes,
    }


def build_field_mapping(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = _section(candidate, "diagnostic_evidence")
    axisym = _section(candidate, "axisymmetric_interpretation")
    available_blocks = set(evidence.get("available_blocks") or [])

    pressure_status = evidence.get("pressure_history_status")
    opening_status = evidence.get("opening_time_status")

    rows = [
        mapping(
            "young_modulus_Pa",
            "MISSING",
            "candidate_yaml",
            "",
            "Pa",
            "none",
            False,
            "Elastic modulus is required by PennyShapedDiagnosticInput and is not present in the Phase 11.10A candidate.",
        ),
        mapping(
            "poisson_ratio",
            "MISSING",
            "candidate_yaml",
            "",
            "dimensionless",
            "none",
            False,
            "Poisson ratio is required by PennyShapedDiagnosticInput and is not present in the candidate.",
        ),
        mapping(
            "viscosity_Pa_min",
            "MISSING",
            "candidate_yaml",
            "",
            "Pa.min",
            "none",
            False,
            "Fluid viscosity is required by PennyShapedDiagnosticInput and is not present in the candidate.",
        ),
        mapping(
            "flow_rate_m3_min",
            "MISSING",
            "candidate_yaml",
            "",
            "m3/min",
            "none",
            False,
            "Injection flow rate is required by PennyShapedDiagnosticInput and is not present in the candidate.",
        ),
        mapping(
            "elapsed_since_opening_min",
            "FOUND_NEEDS_SEMANTIC_REVIEW" if opening_status == "OPENING_TIME_FOUND_CONSUMABLE" else "MISSING",
            "candidate_yaml",
            "diagnostic_evidence.opening_time_min",
            "min",
            "elapsed_since_opening_min requires a future time origin relative to opening; opening_time_min alone is an event marker.",
            False,
            "The legacy opening marker is consumable, but adapter elapsed time is a post-opening duration, not the absolute opening time.",
        ),
        mapping(
            "wellbore_pressure_Pa",
            "FOUND_NEEDS_SEMANTIC_REVIEW" if pressure_status == "PRESSURE_HISTORY_FOUND_CONSUMABLE" else "MISSING",
            "legacy_output",
            "dP pressure history",
            "Pa",
            "Pressure conversion is documented by legacy visualizer, but adapter needs a wellbore pressure sample at diagnostic time.",
            False,
            "Pressure history exists but no single adapter-ready wellbore pressure value is selected in the candidate.",
        ),
        mapping(
            "sigma_theta_compression_positive_Pa",
            "MISSING",
            "legacy_output",
            "sigmaTheta",
            "Pa",
            "none",
            False,
            "BUZ29 sigmaTheta is not directly exported by the legacy output.",
        ),
        mapping(
            "volume_multiplier",
            "INFERRED",
            "PennyShapedDiagnosticInput default",
            "volume_multiplier",
            "dimensionless",
            "default = 10.0",
            False,
            "The adapter has a default multiplier, but the candidate does not explicitly declare that this legacy factor is accepted for BUZ29.",
        ),
        mapping(
            "netPressure_Pa",
            "NOT_APPLICABLE",
            "API audit",
            "PennyShapedDiagnosticInput",
            "Pa",
            "none",
            False,
            "The current adapter does not consume netPressure_Pa; it consumes wellbore_pressure_Pa and sigma_theta_compression_positive_Pa.",
        ),
        mapping(
            "characteristicRadius_m",
            "NOT_APPLICABLE",
            "API audit",
            "PennyShapedInput",
            "m",
            "none",
            False,
            "The current adapter computes radius_m; it does not consume characteristicRadius_m.",
        ),
        mapping(
            "opening_time_min",
            "FOUND_CONSUMABLE" if opening_status == "OPENING_TIME_FOUND_CONSUMABLE" else "MISSING",
            "candidate_yaml",
            "diagnostic_evidence.opening_time_min",
            "min",
            "none",
            opening_status == "OPENING_TIME_FOUND_CONSUMABLE",
            "Legacy opening marker is available for diagnostic preparation.",
        ),
        mapping(
            "pressure_history",
            "FOUND_NEEDS_CONVERSION" if pressure_status == "PRESSURE_HISTORY_FOUND_CONSUMABLE" else "MISSING",
            "legacy_output",
            "dP",
            "Pa",
            "Legacy visualizer documents pressure conversion; adapter-ready sampling remains future work.",
            pressure_status == "PRESSURE_HISTORY_FOUND_CONSUMABLE",
            "Pressure history is available as evidence, not as a selected adapter input.",
        ),
        mapping(
            "leakoff_history",
            "FOUND_CONSUMABLE" if "dV_leakoff" in available_blocks else "MISSING",
            "legacy_output",
            "dV_leakoff",
            "m3/rad or legacy output basis",
            "none in this phase",
            "dV_leakoff" in available_blocks,
            "Leakoff history is evidence only; the adapter does not consume it directly.",
        ),
        mapping(
            "outflow_history",
            "FOUND_CONSUMABLE" if "V_outflow" in available_blocks else "MISSING",
            "legacy_output",
            "V_outflow",
            "legacy output basis",
            "none in this phase",
            "V_outflow" in available_blocks,
            "Outflow history is evidence only; the adapter does not consume it directly.",
        ),
        mapping(
            "axisymmetric_angle_rad",
            "FOUND_CONSUMABLE" if axisym.get("angle_rad") == 1.0 else "MISSING",
            "candidate_yaml",
            "axisymmetric_interpretation.angle_rad",
            "rad",
            "none",
            axisym.get("angle_rad") == 1.0,
            "The 1 rad interpretation is explicitly declared.",
        ),
    ]
    return rows


def inspect_adapter_ready_inputs(path: Path) -> dict[str, Any]:
    candidate = load_candidate(path)
    case = _section(candidate, "case")
    diagnostics = _section(candidate, "diagnostics")
    axisym = _section(candidate, "axisymmetric_interpretation")
    track = _section(candidate, "track")
    evidence = _section(candidate, "diagnostic_evidence")

    blocking_gaps: list[str] = []
    severe_ambiguities: list[str] = []

    if case.get("active") is True:
        blocking_gaps.append("case.active")
    if diagnostics.get("physically_validated") is not False:
        blocking_gaps.append("diagnostics.physically_validated")
    if diagnostics.get("legacy_equivalent") is not False:
        blocking_gaps.append("diagnostics.legacy_equivalent")
    if diagnostics.get("active_simulation_case") is not False:
        blocking_gaps.append("diagnostics.active_simulation_case")
    if track.get("gate") != "BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A":
        blocking_gaps.append("track.gate")
    if axisym.get("caveat") != AXISYMMETRIC_CAVEAT:
        blocking_gaps.append("axisymmetric_interpretation.caveat")
    if axisym.get("future_output_requirement") != FUTURE_OUTPUT_REQUIREMENT:
        blocking_gaps.append("axisymmetric_interpretation.future_output_requirement")

    field_mapping = build_field_mapping(candidate)
    status_by_field = {row["adapter_field"]: row["status"] for row in field_mapping}

    pressure_opening_ok = (
        evidence.get("pressure_history_status") == "PRESSURE_HISTORY_FOUND_CONSUMABLE"
        and evidence.get("opening_time_status") == "OPENING_TIME_FOUND_CONSUMABLE"
    )
    if not pressure_opening_ok:
        blocking_gaps.append("pressure_or_opening_evidence")

    missing_required = [
        field
        for field in REQUIRED_ADAPTER_FIELDS
        if status_by_field.get(field) in {"MISSING", "DEFERRED"}
    ]
    semantic_review = [
        field
        for field in REQUIRED_ADAPTER_FIELDS
        if status_by_field.get(field) == "FOUND_NEEDS_SEMANTIC_REVIEW"
    ]

    ambiguous_units = [
        row["adapter_field"]
        for row in field_mapping
        if row["status"] == "FOUND_NEEDS_CONVERSION" and "ambiguous" in row["notes"].lower()
    ]
    severe_ambiguities.extend(ambiguous_units)

    if severe_ambiguities:
        classification = CLASS_INCONCLUSIVE
        adapter_ready = False
        partial_adapter_ready = False
        recommended_next_phase = NEXT_RESOLVE_SEMANTICS
    elif blocking_gaps and not pressure_opening_ok:
        classification = CLASS_BLOCKED
        adapter_ready = False
        partial_adapter_ready = False
        recommended_next_phase = NEXT_COMPLETE_INPUTS
    elif pressure_opening_ok and (missing_required or semantic_review or blocking_gaps):
        classification = CLASS_PARTIAL
        adapter_ready = False
        partial_adapter_ready = True
        recommended_next_phase = NEXT_MATH_AUDIT
    else:
        classification = CLASS_READY
        adapter_ready = True
        partial_adapter_ready = False
        recommended_next_phase = NEXT_MATH_AUDIT

    return {
        "phase": PHASE,
        "case": CASE_ID,
        "case_file": str(path),
        "classification": classification,
        "adapter_ready": adapter_ready,
        "partial_adapter_ready": partial_adapter_ready,
        "physically_validated": False,
        "legacy_equivalent": False,
        "active_simulation_case": False,
        "required_adapter_fields": REQUIRED_ADAPTER_FIELDS,
        "adapter_output_fields": ADAPTER_OUTPUT_FIELDS,
        "field_mapping": field_mapping,
        "missing_fields": missing_required,
        "semantic_review_fields": semantic_review,
        "deferred_fields": DEFERRED_FIELDS,
        "axisymmetric_interpretation": axisym.get("caveat"),
        "future_output_requirement": axisym.get("future_output_requirement"),
        "blocking_gaps": blocking_gaps,
        "severe_ambiguities": severe_ambiguities,
        "recommended_next_phase": recommended_next_phase,
        "caveats": [
            "NOT_PHYSICALLY_VALIDATED",
            "NOT_LEGACY_EQUIVALENT",
            "NOT_ACTIVE_SIMULATION_CASE",
            "MATH_AUDIT_REQUIRED_BEFORE_DIAGNOSTIC_EXECUTION",
            AXISYMMETRIC_CAVEAT,
            FUTURE_OUTPUT_REQUIREMENT,
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10B BUZ29 PennyShaped Adapter-Ready Input Inspection",
        "",
        f"- classification: `{result['classification']}`",
        f"- adapter_ready: `{str(result['adapter_ready']).lower()}`",
        f"- partial_adapter_ready: `{str(result['partial_adapter_ready']).lower()}`",
        "- physically_validated: `false`",
        "- legacy_equivalent: `false`",
        "- active_simulation_case: `false`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Required Adapter Fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in result["required_adapter_fields"])
    lines.extend(["", "## Field Mapping", "", "| Field | Status | Source | Source field | Consumable | Notes |", "|---|---|---|---|---:|---|"])
    for row in result["field_mapping"]:
        lines.append(
            f"| `{row['adapter_field']}` | `{row['status']}` | `{row['source']}` | `{row['source_field']}` | `{str(row['consumable']).lower()}` | {row['notes']} |"
        )
    lines.extend(["", "## Missing Fields", ""])
    lines.extend(f"- `{field}`" for field in result["missing_fields"] or ["none"])
    lines.extend(["", "## Semantic Review Fields", ""])
    lines.extend(f"- `{field}`" for field in result["semantic_review_fields"] or ["none"])
    lines.extend(["", "## Deferred Fields", ""])
    lines.extend(f"- `{field}`" for field in result["deferred_fields"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- `{item}`" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Phase 11.10B BUZ29 PennyShaped adapter-ready inputs."
    )
    parser.add_argument("--case", required=True, type=Path, help="BUZ29 Penny candidate YAML.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = inspect_adapter_ready_inputs(args.case)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"CLASSIFICATION={result['classification']}")
    print(f"ADAPTER_READY={str(result['adapter_ready']).lower()}")
    print(f"PARTIAL_ADAPTER_READY={str(result['partial_adapter_ready']).lower()}")
    print("PHYSICALLY_VALIDATED=false")
    print("LEGACY_EQUIVALENT=false")
    print("ACTIVE_SIMULATION_CASE=false")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0 if result["classification"] != CLASS_BLOCKED else 2


if __name__ == "__main__":
    raise SystemExit(main())
