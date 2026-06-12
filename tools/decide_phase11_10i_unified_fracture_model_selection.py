#!/usr/bin/env python3
"""Decide the Phase 11.10I unified fracture-model selection architecture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10I"
DECISION = "UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED"
NEXT_PHASE = "PHASE11_10J_SPECIFY_FRACTURE_MODEL_SELECTOR_GUARD"

SUPPORTED_MODELS = ["PKN", "PENNY_SHAPED"]
EXPLICIT_OPT_IN_MODELS = ["PENNY_SHAPED"]
BLOCKED_MODELS = [
    "KGD",
    "KGD_CIRCULAR",
    "KGD_ELLIPTICAL",
    "RADIAL",
    "ELLIPTICAL",
    "UNKNOWN",
    "EXPLICIT_EMPTY",
]

DEFAULT_PATHS = {
    "minimal_case": Path("cases/validation/lot_pkn_minimal.yaml"),
    "leakoff_case": Path("cases/validation/lot_pkn_with_leakoff.yaml"),
    "buz67d_case": Path("cases/lot_tese_migrated/buz67d_pkn.yaml"),
    "penny_candidate": Path("cases/validation/non_pkn/buz29_penny_candidate.yaml"),
    "case_parser": Path("src/io/CaseParser.cpp"),
    "lot_sim": Path("apps/lot-sim.cpp"),
    "pkn_runner": Path("include/lot/PknRunner.hpp"),
    "gate_doc": Path("docs/82_non_pkn_diagnostic_runner_gate.md"),
}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _contains(path: Path, needle: str) -> bool:
    return needle in _read_text(path)


def audit_current_selection(paths: dict[str, Path]) -> dict[str, Any]:
    parser_text = _read_text(paths["case_parser"])
    lot_sim_text = _read_text(paths["lot_sim"])

    pkn_cases = [
        str(paths["minimal_case"]),
        str(paths["leakoff_case"]),
        str(paths["buz67d_case"]),
    ]
    cases_without_fracture_model = [
        case
        for case in pkn_cases
        if Path(case).exists() and "fracture_model" not in _read_text(Path(case))
    ]

    return {
        "pkn_selection_today": (
            "simulation.mode lot-pkn plus lot.model/fracture.geometry pkn validation"
        ),
        "current_selection_depends_on": ["simulation.mode", "lot.model", "lot.fracture.geometry"],
        "official_lot_pkn_cli_mode": "lot-pkn" if "--mode lot-pkn" in lot_sim_text or "lot-pkn" in lot_sim_text else "unknown",
        "fracture_model_field_exists_now": "fracture_model" in parser_text,
        "parser_checks_lot_pkn_geometry": "lot-pkn exige lot.model/fracture.geometry pkn" in parser_text,
        "pkn_cases_without_fracture_model": cases_without_fracture_model,
        "penny_candidate_uses_model_field": _contains(paths["penny_candidate"], "model: PENNY_SHAPED"),
        "future_low_impact_location": "lot.fracture.fracture_model",
        "parser_schema_change_now": False,
    }


def build_decision(paths: dict[str, Path] | None = None) -> dict[str, Any]:
    if paths is None:
        paths = DEFAULT_PATHS
    audit = audit_current_selection(paths)
    return {
        "phase": PHASE,
        "decision": DECISION,
        "required_classifications": [
            "PKN_DEFAULT_FRACTURE_MODEL",
            "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY",
            "UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED",
            "UNSUPPORTED_FRACTURE_MODELS_BLOCKED",
        ],
        "selection_field": "lot.fracture.fracture_model",
        "preferred_input_examples": [
            {"lot": {"fracture": {"enabled": True, "fracture_model": "PKN"}}},
            {"lot": {"fracture": {"enabled": True, "fracture_model": "PENNY_SHAPED"}}},
        ],
        "default_fracture_model": "PKN",
        "missing_fracture_model_behavior": "DEFAULT_TO_PKN",
        "supported_fracture_models": SUPPORTED_MODELS,
        "explicit_opt_in_models": EXPLICIT_OPT_IN_MODELS,
        "blocked_fracture_models": BLOCKED_MODELS,
        "pkn_runtime_status": "OFFICIAL_RUNTIME_AVAILABLE",
        "penny_shaped_runtime_status": "DIAGNOSTIC_ONLY_NOT_PHYSICALLY_VALIDATED",
        "fracture_initiation_gate_required": True,
        "fracture_initiation_gate_fields": [
            "wellbore_pressure_Pa",
            "sigma_theta_compression_positive_Pa",
            "fracture_initiation_gate",
            "fracture_model",
        ],
        "fracture_initiation_gate_states": [
            {
                "fracture_initiation_gate": "NOT_REACHED",
                "selected_fracture_model": "PKN",
                "runtime_status": "fracture_model_selected_but_not_executed",
            },
            {
                "fracture_initiation_gate": "REACHED",
                "selected_fracture_model": "PENNY_SHAPED",
                "runtime_status": "DIAGNOSTIC_ONLY",
            },
        ],
        "criterion_requires_sign_convention": True,
        "sigma_theta_sign_convention": (
            "sigma_theta_compression_positive_Pa must be compared with an "
            "explicit compression-positive algebra to avoid sign inversion"
        ),
        "runtime_implementation_allowed_now": False,
        "parser_schema_change_allowed_now": False,
        "buz29_penny_execution_allowed_now": False,
        "legacy_equivalence_claim_allowed_now": False,
        "lot_pkn_behavior_change_allowed_now": False,
        "current_selection_audit": audit,
        "reconciles_phase11_10h": (
            "The former non-PKN runner recommendation is narrowed to a future "
            "selector guard inside one unified LOT/fracture runtime, not a "
            "parallel official runtime path."
        ),
        "recommended_next_phase": NEXT_PHASE,
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10I Unified Fracture-Model Selection",
        "",
        f"- phase: `{result['phase']}`",
        f"- decision: `{result['decision']}`",
        f"- selection_field: `{result['selection_field']}`",
        f"- default_fracture_model: `{result['default_fracture_model']}`",
        f"- missing_fracture_model_behavior: `{result['missing_fracture_model_behavior']}`",
        f"- supported_fracture_models: `{', '.join(result['supported_fracture_models'])}`",
        f"- explicit_opt_in_models: `{', '.join(result['explicit_opt_in_models'])}`",
        f"- blocked_fracture_models: `{', '.join(result['blocked_fracture_models'])}`",
        f"- fracture_initiation_gate_required: `{str(result['fracture_initiation_gate_required']).lower()}`",
        f"- criterion_requires_sign_convention: `{str(result['criterion_requires_sign_convention']).lower()}`",
        f"- runtime_implementation_allowed_now: `{str(result['runtime_implementation_allowed_now']).lower()}`",
        f"- parser_schema_change_allowed_now: `{str(result['parser_schema_change_allowed_now']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Required Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in result["required_classifications"])
    lines.extend(
        [
            "",
            "## Current Selection Audit",
            "",
            f"- pkn_selection_today: `{result['current_selection_audit']['pkn_selection_today']}`",
            f"- current_selection_depends_on: `{', '.join(result['current_selection_audit']['current_selection_depends_on'])}`",
            f"- fracture_model_field_exists_now: `{str(result['current_selection_audit']['fracture_model_field_exists_now']).lower()}`",
            f"- future_low_impact_location: `{result['current_selection_audit']['future_low_impact_location']}`",
            "",
            "## Gate",
            "",
            result["reconciles_phase11_10h"],
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decide Phase 11.10I unified fracture-model selection."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = build_decision()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"DECISION={result['decision']}")
    print(f"DEFAULT_FRACTURE_MODEL={result['default_fracture_model']}")
    print(f"SELECTION_FIELD={result['selection_field']}")
    print(f"MISSING_FRACTURE_MODEL_BEHAVIOR={result['missing_fracture_model_behavior']}")
    print(f"SUPPORTED_FRACTURE_MODELS={','.join(result['supported_fracture_models'])}")
    print(f"EXPLICIT_OPT_IN_MODELS={','.join(result['explicit_opt_in_models'])}")
    print(f"RUNTIME_IMPLEMENTATION_ALLOWED_NOW={str(result['runtime_implementation_allowed_now']).lower()}")
    print(f"PARSER_SCHEMA_CHANGE_ALLOWED_NOW={str(result['parser_schema_change_allowed_now']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
