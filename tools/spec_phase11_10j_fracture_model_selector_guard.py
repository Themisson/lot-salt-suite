#!/usr/bin/env python3
"""Specify the Phase 11.10J fracture_model selector guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10J"
GUARD_SPEC_STATUS = "FRACTURE_MODEL_SELECTOR_GUARD_SPECIFIED"
PARTIAL_STATUS = "FRACTURE_MODEL_SELECTOR_GUARD_SPEC_PARTIAL"
BLOCKED_STATUS = "FRACTURE_MODEL_SELECTOR_GUARD_BLOCKED"
INCONCLUSIVE_STATUS = "FRACTURE_MODEL_SELECTOR_GUARD_INCONCLUSIVE"

NEXT_IMPLEMENT = "PHASE11_10K_IMPLEMENT_FRACTURE_MODEL_SELECTOR_GUARD"
NEXT_DECIDE_PARSER = "PHASE11_10K_DECIDE_PARSER_SCHEMA_INTEGRATION_FOR_FRACTURE_MODEL"
NEXT_RECONCILE_PKN = "PHASE11_10K_RECONCILE_PKN_DEFAULT_BEHAVIOR"

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


def normalization_rules() -> list[dict[str, str]]:
    return [
        {"input": "PKN", "canonical": "PKN"},
        {"input": "pkn", "canonical": "PKN"},
        {"input": "lot-pkn", "canonical": "PKN"},
        {"input": "lot_pkn", "canonical": "PKN"},
        {"input": "PENNY_SHAPED", "canonical": "PENNY_SHAPED"},
        {"input": "penny_shaped", "canonical": "PENNY_SHAPED"},
        {"input": "penny-shaped", "canonical": "PENNY_SHAPED"},
        {"input": "penny", "canonical": "PENNY_SHAPED"},
    ]


def selector_cases() -> list[dict[str, Any]]:
    return [
        {
            "case": "field_absent",
            "input": None,
            "canonical_model": "PKN",
            "status": "DEFAULT_TO_PKN",
            "error": False,
        },
        {
            "case": "explicit_pkn",
            "input": "PKN",
            "canonical_model": "PKN",
            "status": "EXPLICIT_PKN_ACCEPTED",
            "error": False,
        },
        {
            "case": "explicit_penny_shaped",
            "input": "PENNY_SHAPED",
            "canonical_model": "PENNY_SHAPED",
            "status": "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY",
            "error": False,
        },
        {
            "case": "explicit_empty",
            "input": "",
            "canonical_model": None,
            "status": "EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED",
            "error": True,
        },
        {
            "case": "unsupported_kgd",
            "input": "KGD",
            "canonical_model": None,
            "status": "UNSUPPORTED_FRACTURE_MODEL_REJECTED",
            "error": True,
        },
    ]


def selection_execution_states() -> list[dict[str, str]]:
    return [
        {
            "selection_state": "PKN_SELECTED_BY_ABSENCE",
            "execution_state": "OFFICIAL_LOT_PKN_RUNTIME",
            "meaning": "Existing cases without fracture_model preserve historical PKN behavior.",
        },
        {
            "selection_state": "PKN_SELECTED_EXPLICITLY",
            "execution_state": "OFFICIAL_LOT_PKN_RUNTIME",
            "meaning": "Explicit PKN is accepted but must remain behavior-compatible with absent field.",
        },
        {
            "selection_state": "PENNY_SHAPED_SELECTED_EXPLICITLY",
            "execution_state": "DIAGNOSTIC_OPT_IN_ONLY",
            "meaning": "Selection is allowed only behind fracture_initiation and sign-convention gates.",
        },
        {
            "selection_state": "UNSUPPORTED_SELECTED",
            "execution_state": "BLOCKED",
            "meaning": "Unsupported models fail before any solver dispatch.",
        },
    ]


def decide_guard(
    *,
    default_specified: bool = True,
    explicit_specified: bool = True,
    unsupported_specified: bool = True,
    parser_ambiguity: bool = False,
) -> tuple[str, str]:
    if not default_specified:
        return BLOCKED_STATUS, NEXT_RECONCILE_PKN
    if parser_ambiguity:
        return PARTIAL_STATUS, NEXT_DECIDE_PARSER
    if default_specified and explicit_specified and unsupported_specified:
        return GUARD_SPEC_STATUS, NEXT_IMPLEMENT
    return PARTIAL_STATUS, NEXT_DECIDE_PARSER


def build_spec() -> dict[str, Any]:
    status, next_phase = decide_guard()
    return {
        "phase": PHASE,
        "guard_spec_status": status,
        "selection_field": "lot.fracture.fracture_model",
        "default_fracture_model": "PKN",
        "missing_field_behavior": "DEFAULT_TO_PKN",
        "explicit_empty_behavior": "REJECT_AS_INVALID",
        "supported_models": SUPPORTED_MODELS,
        "explicit_opt_in_models": EXPLICIT_OPT_IN_MODELS,
        "blocked_models": BLOCKED_MODELS,
        "normalization_rules": normalization_rules(),
        "selector_cases": selector_cases(),
        "selection_execution_states": selection_execution_states(),
        "pkn_status": "DEFAULT_AND_EXPLICIT_SUPPORTED",
        "penny_shaped_status": "EXPLICIT_OPT_IN_DIAGNOSTIC_ONLY",
        "fracture_initiation_gate_required": True,
        "criterion_requires_sign_convention": True,
        "runtime_implementation_allowed_now": False,
        "parser_schema_change_allowed_now": False,
        "buz29_penny_execution_allowed_now": False,
        "lot_pkn_behavior_change_allowed_now": False,
        "required_statuses": [
            "FRACTURE_MODEL_SELECTOR_GUARD_SPECIFIED",
            "PKN_DEFAULT_WHEN_ABSENT",
            "EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED",
            "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY",
            "UNSUPPORTED_FRACTURE_MODELS_BLOCKED",
            "FRACTURE_INITIATION_GATE_REQUIRED",
            "SIGMATHETA_SIGN_CONVENTION_REQUIRED",
            "NO_RUNTIME_CHANGE_IN_11_10J",
        ],
        "blocked_runtime_actions": [
            "do_not_implement_parser_or_schema_in_phase11_10j",
            "do_not_execute_buz29_penny_in_phase11_10j",
            "do_not_change_lot_pkn_default_behavior",
            "do_not_dispatch_penny_shaped_without_explicit_gate",
        ],
        "recommended_next_phase": next_phase,
        "caveats": [
            "Phase 11.10J is specification only.",
            "The selector guard is not implemented in parser, schema, C++ or CLI.",
            "PENNY_SHAPED remains diagnostic, opt-in, not physically validated and not legacy-equivalent.",
            "Selection does not imply execution; fracture_initiation and sigmaTheta sign gates remain required.",
        ],
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10J Fracture-Model Selector Guard",
        "",
        f"- phase: `{spec['phase']}`",
        f"- guard_spec_status: `{spec['guard_spec_status']}`",
        f"- selection_field: `{spec['selection_field']}`",
        f"- default_fracture_model: `{spec['default_fracture_model']}`",
        f"- missing_field_behavior: `{spec['missing_field_behavior']}`",
        f"- explicit_empty_behavior: `{spec['explicit_empty_behavior']}`",
        f"- supported_models: `{', '.join(spec['supported_models'])}`",
        f"- explicit_opt_in_models: `{', '.join(spec['explicit_opt_in_models'])}`",
        f"- blocked_models: `{', '.join(spec['blocked_models'])}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Selector Cases",
        "",
        "| Case | Input | Canonical model | Status | Error |",
        "|---|---:|---|---|---|",
    ]
    for item in spec["selector_cases"]:
        input_value = "<absent>" if item["input"] is None else str(item["input"])
        canonical = item["canonical_model"] or "<none>"
        lines.append(
            f"| `{item['case']}` | `{input_value}` | `{canonical}` | `{item['status']}` | `{item['error']}` |"
        )

    lines.extend(
        [
            "",
            "## Required Statuses",
            "",
        ]
    )
    lines.extend(f"- `{status}`" for status in spec["required_statuses"])
    lines.extend(
        [
            "",
            "## Caveats",
            "",
        ]
    )
    lines.extend(f"- {caveat}" for caveat in spec["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10J fracture_model selector guard."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = build_spec()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(spec, args.output_md)

    print(f"PHASE={spec['phase']}")
    print(f"GUARD_SPEC_STATUS={spec['guard_spec_status']}")
    print(f"SELECTION_FIELD={spec['selection_field']}")
    print(f"DEFAULT_FRACTURE_MODEL={spec['default_fracture_model']}")
    print(f"MISSING_FIELD_BEHAVIOR={spec['missing_field_behavior']}")
    print(f"EXPLICIT_EMPTY_BEHAVIOR={spec['explicit_empty_behavior']}")
    print(f"SUPPORTED_MODELS={','.join(spec['supported_models'])}")
    print(f"EXPLICIT_OPT_IN_MODELS={','.join(spec['explicit_opt_in_models'])}")
    print(f"FRACTURE_INITIATION_GATE_REQUIRED={str(spec['fracture_initiation_gate_required']).lower()}")
    print(f"CRITERION_REQUIRES_SIGN_CONVENTION={str(spec['criterion_requires_sign_convention']).lower()}")
    print(f"RUNTIME_IMPLEMENTATION_ALLOWED_NOW={str(spec['runtime_implementation_allowed_now']).lower()}")
    print(f"PARSER_SCHEMA_CHANGE_ALLOWED_NOW={str(spec['parser_schema_change_allowed_now']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
