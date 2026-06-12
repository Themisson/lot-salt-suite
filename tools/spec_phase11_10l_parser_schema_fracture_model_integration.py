#!/usr/bin/env python3
"""Specify the Phase 11.10L parser/schema integration for fracture_model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10L"
SPECIFIED = "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_SPECIFIED"
PARTIAL = "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_PARTIAL"
BLOCKED = "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_BLOCKED"
INCONCLUSIVE = "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_INCONCLUSIVE"
NEXT_PHASE = "PHASE11_10M_INTEGRATE_FRACTURE_MODEL_IN_PARSER_SCHEMA"


def build_spec() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "integration_spec_status": SPECIFIED,
        "field": "lot.fracture.fracture_model",
        "default_fracture_model": "PKN",
        "missing_field_behavior": "DEFAULT_TO_PKN",
        "explicit_empty_behavior": "ERROR_EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED",
        "unsupported_model_behavior": "ERROR_UNSUPPORTED_FRACTURE_MODEL",
        "schema_policy": "SCHEMA_STRICT_CANONICAL_ONLY",
        "allowed_canonical_values": ["PKN", "PENNY_SHAPED"],
        "parser_integration_allowed_next": True,
        "schema_integration_allowed_next": True,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "lot_pkn_behavior_change_allowed": False,
        "recommended_next_phase": NEXT_PHASE,
        "current_parser_audit": {
            "yaml_reader": "src/io/CaseParser.cpp::parse_yaml",
            "case_parser_header": "include/io/CaseParser.hpp",
            "case_data": "include/core/types.hpp::LotConfig",
            "schema": "schemas/lot_case.schema.yaml",
            "lot_fracture_processing": "src/io/CaseParser.cpp reads lot.fracture.geometry",
            "current_lot_pkn_validation": (
                "simulation.mode lot-pkn requires lot.model/fracture.geometry pkn"
            ),
            "current_correlated_fields": ["lot.model", "lot.fracture.geometry"],
            "fracture_model_field_exists_now": False,
        },
        "future_parser_behavior": [
            {
                "yaml": "lot.fracture.fracture_model absent",
                "selected_fracture_model": "PKN",
                "selection_source": "DEFAULTED",
                "validation_error": False,
                "backward_compatible": True,
            },
            {
                "yaml": "lot.fracture.fracture_model: PKN",
                "selected_fracture_model": "PKN",
                "selection_source": "EXPLICIT",
                "validation_error": False,
                "backward_compatible": True,
            },
            {
                "yaml": "lot.fracture.fracture_model: PENNY_SHAPED",
                "selected_fracture_model": "PENNY_SHAPED",
                "selection_source": "EXPLICIT",
                "diagnostic_only": True,
                "runtime_supported_now": False,
            },
            {
                "yaml": 'lot.fracture.fracture_model: ""',
                "error": "EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED",
            },
            {
                "yaml": "lot.fracture.fracture_model: KGD",
                "error": "UNSUPPORTED_FRACTURE_MODEL",
            },
        ],
        "future_schema_policy": {
            "recommended_policy": "SCHEMA_STRICT_CANONICAL_ONLY",
            "field_optional": True,
            "allowed_values": ["PKN", "PENNY_SHAPED"],
            "explicit_empty_allowed": False,
            "aliases_allowed_in_official_yaml": False,
            "alias_handling": (
                "aliases remain accepted by FractureModelSelector helper/tests, "
                "but official YAML should use canonical values unless a later "
                "phase explicitly chooses permissive schema behavior"
            ),
        },
        "future_tests": [
            "existing PKN cases without fracture_model remain valid",
            "explicit fracture_model: PKN remains valid",
            "explicit fracture_model: PENNY_SHAPED is accepted only as non-runtime diagnostic state",
            "explicit empty fracture_model is rejected",
            "unsupported KGD/RADIAL/UNKNOWN are rejected",
            "lot-pkn behavior and outputs remain unchanged",
        ],
        "required_statuses": [
            "PHASE11_10L_FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_SPECIFIED",
            "FRACTURE_MODEL_FIELD_LOT_FRACTURE_FRACTURE_MODEL",
            "PKN_DEFAULT_PARSER_BEHAVIOR_REQUIRED",
            "EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED",
            "UNSUPPORTED_FRACTURE_MODELS_BLOCKED",
            "PARSER_SCHEMA_INTEGRATION_ALLOWED_NEXT",
            "RUNTIME_EXECUTION_NOT_ALLOWED_NEXT",
            "BUZ29_EXECUTION_NOT_ALLOWED_NEXT",
        ],
        "caveats": [
            "Phase 11.10L is specification only.",
            "No parser, schema, C++, CLI or runtime files are changed.",
            "Parser/schema integration does not authorize BUZ29-PENNY execution.",
            "PENNY_SHAPED remains diagnostic, not physically validated and not legacy-equivalent.",
        ],
    }


def write_markdown(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10L Parser/Schema Integration Spec",
        "",
        f"- phase: `{spec['phase']}`",
        f"- integration_spec_status: `{spec['integration_spec_status']}`",
        f"- field: `{spec['field']}`",
        f"- default_fracture_model: `{spec['default_fracture_model']}`",
        f"- missing_field_behavior: `{spec['missing_field_behavior']}`",
        f"- explicit_empty_behavior: `{spec['explicit_empty_behavior']}`",
        f"- unsupported_model_behavior: `{spec['unsupported_model_behavior']}`",
        f"- schema_policy: `{spec['schema_policy']}`",
        f"- allowed_canonical_values: `{', '.join(spec['allowed_canonical_values'])}`",
        f"- parser_integration_allowed_next: `{str(spec['parser_integration_allowed_next']).lower()}`",
        f"- schema_integration_allowed_next: `{str(spec['schema_integration_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(spec['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(spec['buz29_execution_allowed_next']).lower()}`",
        f"- lot_pkn_behavior_change_allowed: `{str(spec['lot_pkn_behavior_change_allowed']).lower()}`",
        f"- recommended_next_phase: `{spec['recommended_next_phase']}`",
        "",
        "## Current Parser Audit",
        "",
    ]
    for key, value in spec["current_parser_audit"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Required Statuses", ""])
    lines.extend(f"- `{status}`" for status in spec["required_statuses"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in spec["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Specify Phase 11.10L parser/schema integration for fracture_model."
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
    print(f"INTEGRATION_SPEC_STATUS={spec['integration_spec_status']}")
    print(f"FIELD={spec['field']}")
    print(f"DEFAULT_FRACTURE_MODEL={spec['default_fracture_model']}")
    print(f"MISSING_FIELD_BEHAVIOR={spec['missing_field_behavior']}")
    print(f"EXPLICIT_EMPTY_BEHAVIOR={spec['explicit_empty_behavior']}")
    print(f"UNSUPPORTED_MODEL_BEHAVIOR={spec['unsupported_model_behavior']}")
    print(f"SCHEMA_POLICY={spec['schema_policy']}")
    print(f"ALLOWED_CANONICAL_VALUES={','.join(spec['allowed_canonical_values'])}")
    print(f"PARSER_INTEGRATION_ALLOWED_NEXT={str(spec['parser_integration_allowed_next']).lower()}")
    print(f"SCHEMA_INTEGRATION_ALLOWED_NEXT={str(spec['schema_integration_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(spec['runtime_execution_allowed_next']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(spec['buz29_execution_allowed_next']).lower()}")
    print(f"LOT_PKN_BEHAVIOR_CHANGE_ALLOWED={str(spec['lot_pkn_behavior_change_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={spec['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
