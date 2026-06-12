#!/usr/bin/env python3
"""Decide the Phase 11.10H non-PKN diagnostic runner gate."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PHASE = "11.10H"
SPEC_ALLOWED = "NON_PKN_DIAGNOSTIC_RUNNER_SPEC_ALLOWED"
SPEC_PARTIAL = "NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL"
BLOCKED_BY_INPUTS = "NON_PKN_DIAGNOSTIC_RUNNER_BLOCKED_BY_INPUTS"
BLOCKED_BY_SEMANTICS = "NON_PKN_DIAGNOSTIC_RUNNER_BLOCKED_BY_SEMANTICS"
INCONCLUSIVE = "NON_PKN_DIAGNOSTIC_RUNNER_INCONCLUSIVE"

NEXT_SPEC = "PHASE11_10I_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER"
NEXT_COMPLETE_INPUTS = "PHASE11_10I_COMPLETE_NON_PKN_RUNNER_INPUTS"
NEXT_RESOLVE_SEMANTICS = "PHASE11_10I_RESOLVE_NON_PKN_RUNNER_SEMANTICS"
NEXT_REAUDIT = "PHASE11_10I_REAUDIT_NON_PKN_RUNNER_GATE"

ADAPTER_REQUIRED_INPUTS = [
    "young_modulus_Pa",
    "poisson_ratio",
    "viscosity_Pa_min",
    "flow_rate_m3_min",
    "elapsed_since_opening_min",
    "wellbore_pressure_Pa",
    "sigma_theta_compression_positive_Pa",
    "volume_multiplier",
]

ADAPTER_OUTPUTS = [
    "plane_strain_modulus_Pa",
    "opening_m",
    "radius_m",
    "pressure_factor",
    "fracture_volume_proxy_m3",
]

WRITER_REQUIRED_INPUTS = [
    "case_id",
    "phase",
    "track",
    "model",
    "axisymmetric_angle_rad",
    "volume_conversion_factor_1rad_to_2pi",
    "volume_multiplier",
    "volume_multiplier_semantics",
    "volume_multiplier_is_2pi",
    "fracture_volume_proxy_1rad_m3",
    "solid_volume_1rad_m3",
    "fracture_volume_equivalent_2pi_source",
    "solid_volume_equivalent_2pi_source",
    "required_caveats",
]

WRITER_OUTPUTS = [
    "json_string",
    "csv_header",
    "csv_row",
    "fracture_volume_equivalent_2pi_m3",
    "solid_volume_equivalent_2pi_m3",
]

REQUIRED_CONSTRAINTS = [
    "runner must remain opt-in and diagnostic only",
    "runner must not alter lot-pkn, PknModel, PknRunner, parser, schemas or CLI",
    "runner must not execute BUZ29-PENNY as physical validation",
    "runner must preserve physically_validated=false and legacy_equivalent=false",
    "runner must preserve active_simulation_case=false unless a future explicit gate changes it",
    "runner must preserve 1rad fields and 2pi equivalent sources",
    "runner must keep volume_multiplier empirical and not 2pi",
]

DEFAULT_PATHS = {
    "adapter_header": Path("include/lot/PennyShapedDiagnosticAdapter.hpp"),
    "adapter_source": Path("src/lot/PennyShapedDiagnosticAdapter.cpp"),
    "writer_header": Path("include/lot/PennyShapedDiagnosticWriter.hpp"),
    "writer_source": Path("src/lot/PennyShapedDiagnosticWriter.cpp"),
    "candidate": Path("cases/validation/non_pkn/buz29_penny_candidate.yaml"),
    "adapter_doc": Path("docs/75_buz29_penny_adapter_ready_inputs.md"),
    "writer_doc": Path("docs/81_penny_diagnostic_writer_implementation.md"),
}


def _exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _read_text(path: Path) -> str:
    if not _exists(path):
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _has_bool_assignment(text: str, name: str, value: bool) -> bool:
    expected = "true" if value else "false"
    pattern = rf"(?m)^\s*{re.escape(name)}\s*[:=]\s*{expected}\b"
    return re.search(pattern, text) is not None


def detect_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    adapter_available = _exists(paths["adapter_header"]) and _exists(paths["adapter_source"])
    writer_available = _exists(paths["writer_header"]) and _exists(paths["writer_source"])
    candidate_available = _exists(paths["candidate"])

    adapter_doc_text = _read_text(paths["adapter_doc"])
    candidate_text = _read_text(paths["candidate"])
    writer_doc_text = _read_text(paths["writer_doc"])

    adapter_ready = _has_bool_assignment(adapter_doc_text, "adapter_ready", True) or _has_bool_assignment(
        candidate_text, "adapter_ready", True
    )
    partial_adapter_ready = (
        "partial_adapter_ready = true" in adapter_doc_text
        or "adapter_ready: partial" in candidate_text
        or "BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL" in adapter_doc_text
    )
    semantic_blockers = [
        blocker
        for blocker in [
            "elapsed_since_opening_min requires semantic review",
            "wellbore_pressure_Pa sample selection remains deferred",
            "sigma_theta_compression_positive_Pa is absent from direct legacy output",
            "volume proxy remains axisymmetric 1rad diagnostic output",
        ]
    ]
    missing_inputs = [
        field
        for field in [
            "young_modulus_Pa",
            "poisson_ratio",
            "viscosity_Pa_min",
            "flow_rate_m3_min",
            "sigma_theta_compression_positive_Pa",
        ]
        if field in adapter_doc_text
    ]

    writer_has_required_status = "PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN" in writer_doc_text

    return {
        "adapter_available": adapter_available,
        "writer_available": writer_available,
        "candidate_available": candidate_available,
        "adapter_ready": adapter_ready,
        "partial_adapter_ready": partial_adapter_ready,
        "writer_has_required_status": writer_has_required_status,
        "missing_inputs": sorted(set(missing_inputs)),
        "semantic_blockers": semantic_blockers,
    }


def decide_gate(
    *,
    adapter_available: bool,
    writer_available: bool,
    candidate_available: bool,
    adapter_ready: bool,
    partial_adapter_ready: bool,
    semantic_blocker: bool,
    missing_inputs: list[str] | None = None,
) -> tuple[str, str]:
    if not adapter_available or not writer_available or not candidate_available:
        return INCONCLUSIVE, NEXT_REAUDIT
    if semantic_blocker and not (adapter_ready or partial_adapter_ready):
        return BLOCKED_BY_SEMANTICS, NEXT_RESOLVE_SEMANTICS
    if not adapter_ready and not partial_adapter_ready:
        return BLOCKED_BY_INPUTS, NEXT_COMPLETE_INPUTS
    if semantic_blocker and not partial_adapter_ready:
        return BLOCKED_BY_SEMANTICS, NEXT_RESOLVE_SEMANTICS
    if adapter_ready and not semantic_blocker and not missing_inputs:
        return SPEC_ALLOWED, NEXT_SPEC
    return SPEC_PARTIAL, NEXT_SPEC


def build_decision(paths: dict[str, Path]) -> dict[str, Any]:
    artifacts = detect_artifacts(paths)
    missing_inputs = artifacts["missing_inputs"]
    semantic_blocker = bool(artifacts["semantic_blockers"])
    decision, next_phase = decide_gate(
        adapter_available=artifacts["adapter_available"],
        writer_available=artifacts["writer_available"],
        candidate_available=artifacts["candidate_available"],
        adapter_ready=artifacts["adapter_ready"],
        partial_adapter_ready=artifacts["partial_adapter_ready"],
        semantic_blocker=semantic_blocker,
        missing_inputs=missing_inputs,
    )

    blocking_gaps = []
    if missing_inputs:
        blocking_gaps.append("BUZ29 candidate remains missing adapter-ready inputs")
    if semantic_blocker:
        blocking_gaps.append("BUZ29 pressure/time/sigmaTheta semantics remain deferred for runtime execution")
    if not artifacts["writer_has_required_status"]:
        blocking_gaps.append("Writer implementation status marker not found in documentation")

    return {
        "phase": PHASE,
        "decision": decision,
        "adapter_available": artifacts["adapter_available"],
        "writer_available": artifacts["writer_available"],
        "candidate_available": artifacts["candidate_available"],
        "adapter_ready": artifacts["adapter_ready"],
        "partial_adapter_ready": artifacts["partial_adapter_ready"],
        "runner_implementation_allowed_now": False,
        "buz29_runtime_execution_allowed": False,
        "lot_pkn_impact_allowed": False,
        "physical_validation_allowed": False,
        "legacy_equivalence_allowed": False,
        "official_lot_sim_route_allowed": False,
        "adapter_required_inputs": ADAPTER_REQUIRED_INPUTS,
        "adapter_outputs": ADAPTER_OUTPUTS,
        "writer_required_inputs": WRITER_REQUIRED_INPUTS,
        "writer_outputs": WRITER_OUTPUTS,
        "required_future_runner_constraints": REQUIRED_CONSTRAINTS,
        "blocking_gaps": blocking_gaps,
        "missing_or_deferred_adapter_inputs": missing_inputs,
        "semantic_blockers": artifacts["semantic_blockers"],
        "deferred_items": [
            "non-PKN runner implementation",
            "BUZ29-PENNY runtime execution",
            "BUZ29 physical validation",
            "LOT_Tese equivalence claim",
            "parser/schema/CLI route",
        ],
        "recommended_next_phase": next_phase,
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10H Non-PKN Diagnostic Runner Gate",
        "",
        f"- phase: `{result['phase']}`",
        f"- decision: `{result['decision']}`",
        f"- adapter_available: `{str(result['adapter_available']).lower()}`",
        f"- writer_available: `{str(result['writer_available']).lower()}`",
        f"- adapter_ready: `{str(result['adapter_ready']).lower()}`",
        f"- partial_adapter_ready: `{str(result['partial_adapter_ready']).lower()}`",
        f"- runner_implementation_allowed_now: `{str(result['runner_implementation_allowed_now']).lower()}`",
        f"- buz29_runtime_execution_allowed: `{str(result['buz29_runtime_execution_allowed']).lower()}`",
        f"- lot_pkn_impact_allowed: `{str(result['lot_pkn_impact_allowed']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Required future runner constraints",
        "",
    ]
    lines.extend(f"- {item}" for item in result["required_future_runner_constraints"])
    lines.extend(["", "## Blocking gaps", ""])
    lines.extend(f"- {item}" for item in result["blocking_gaps"] or ["none"])
    lines.extend(["", "## Deferred items", ""])
    lines.extend(f"- {item}" for item in result["deferred_items"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.10H non-PKN diagnostic runner gate."
    )
    parser.add_argument("--adapter-header", type=Path, default=DEFAULT_PATHS["adapter_header"])
    parser.add_argument("--adapter-source", type=Path, default=DEFAULT_PATHS["adapter_source"])
    parser.add_argument("--writer-header", type=Path, default=DEFAULT_PATHS["writer_header"])
    parser.add_argument("--writer-source", type=Path, default=DEFAULT_PATHS["writer_source"])
    parser.add_argument("--candidate", type=Path, default=DEFAULT_PATHS["candidate"])
    parser.add_argument("--adapter-doc", type=Path, default=DEFAULT_PATHS["adapter_doc"])
    parser.add_argument("--writer-doc", type=Path, default=DEFAULT_PATHS["writer_doc"])
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = {
        "adapter_header": args.adapter_header,
        "adapter_source": args.adapter_source,
        "writer_header": args.writer_header,
        "writer_source": args.writer_source,
        "candidate": args.candidate,
        "adapter_doc": args.adapter_doc,
        "writer_doc": args.writer_doc,
    }
    result = build_decision(paths)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"DECISION={result['decision']}")
    print(f"ADAPTER_AVAILABLE={str(result['adapter_available']).lower()}")
    print(f"WRITER_AVAILABLE={str(result['writer_available']).lower()}")
    print(f"RUNNER_IMPLEMENTATION_ALLOWED_NOW={str(result['runner_implementation_allowed_now']).lower()}")
    print(f"BUZ29_RUNTIME_EXECUTION_ALLOWED={str(result['buz29_runtime_execution_allowed']).lower()}")
    print(f"LOT_PKN_IMPACT_ALLOWED={str(result['lot_pkn_impact_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
