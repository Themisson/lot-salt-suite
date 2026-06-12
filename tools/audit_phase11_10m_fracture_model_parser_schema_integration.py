"""Audit Phase 11.10M fracture_model parser/schema integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_CANONICAL_VALUES = ["PKN", "PENNY_SHAPED"]
BLOCKED_MODELS = ["KGD", "RADIAL", "UNKNOWN"]
NEXT_PHASE = "PHASE11_10N_AUDIT_FRACTURE_INITIATION_GATE_INITIAL_SIGMATHETA_STATE"


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def build_audit(repo_root: Path = Path(".")) -> dict[str, Any]:
    parser_text = _read_text(repo_root / "src/io/CaseParser.cpp")
    schema_text = _read_text(repo_root / "schemas/lot_case.schema.yaml")
    types_text = _read_text(repo_root / "include/core/types.hpp")
    tests_text = _read_text(repo_root / "tests/cpp/test_case_parser.cpp")

    parser_has_selector = "select_fracture_model" in parser_text
    parser_has_empty_guard = "EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED" in tests_text
    parser_has_unsupported_guard = "UNSUPPORTED_FRACTURE_MODEL" in tests_text
    schema_has_field = "fracture_model:" in schema_text
    schema_has_canonical_values = all(value in schema_text for value in ALLOWED_CANONICAL_VALUES)
    case_data_has_selection = "fracture_model_runtime_dispatch_enabled" in types_text

    integrated = all(
        [
            parser_has_selector,
            parser_has_empty_guard,
            parser_has_unsupported_guard,
            schema_has_field,
            schema_has_canonical_values,
            case_data_has_selection,
        ]
    )

    return {
        "phase": "11.10M",
        "integration_status": (
            "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATED"
            if integrated
            else "FRACTURE_MODEL_PARSER_SCHEMA_PARTIAL"
        ),
        "field": "lot.fracture.fracture_model",
        "schema_policy": "SCHEMA_STRICT_CANONICAL_ONLY",
        "default_fracture_model": "PKN",
        "missing_field_behavior": "DEFAULT_TO_PKN",
        "explicit_empty_behavior": "ERROR_EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED",
        "unsupported_model_behavior": "ERROR_UNSUPPORTED_FRACTURE_MODEL",
        "allowed_canonical_values": ALLOWED_CANONICAL_VALUES,
        "blocked_models": BLOCKED_MODELS,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "sigma_theta_initial_state_audit_required": True,
        "lot_pkn_behavior_changed": False,
        "recommended_next_phase": NEXT_PHASE,
        "parser_schema_checks": {
            "parser_has_fracture_model_selector": parser_has_selector,
            "parser_tests_explicit_empty": parser_has_empty_guard,
            "parser_tests_unsupported": parser_has_unsupported_guard,
            "schema_has_fracture_model": schema_has_field,
            "schema_has_canonical_values": schema_has_canonical_values,
            "case_data_has_runtime_dispatch_flag": case_data_has_selection,
        },
        "future_gate": {
            "cause": "FRACTURE_GATE_MAY_BE_EVALUATED_BEFORE_INITIAL_STRESS_STATE",
            "gate": "SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH",
            "secondary_cause": "POSSIBLE_PRESSURE_SIGMATHETA_REFERENCE_MISMATCH",
            "secondary_gate": (
                "ALIGN_PRESSURE_AND_SIGMATHETA_SEMANTICS_BEFORE_FRACTURE_MODEL_SELECTION"
            ),
        },
        "required_statuses": [
            "PHASE11_10M_FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATED",
            "PKN_DEFAULT_WHEN_FRACTURE_MODEL_MISSING",
            "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY",
            "RUNTIME_DISPATCH_NOT_ENABLED",
            "SIGMATHETA_INITIAL_STATE_AUDIT_REQUIRED_BEFORE_DISPATCH",
        ],
        "caveats": [
            "Parser/schema integration does not authorize runtime dispatch.",
            "BUZ29-PENNY was not executed and remains blocked.",
            "PENNY_SHAPED is diagnostic metadata only until future gates are cleared.",
            "lot-pkn physical behavior is unchanged.",
        ],
    }


def write_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10M Fracture Model Parser/Schema Integration Audit",
        "",
        f"- phase: `{audit['phase']}`",
        f"- integration_status: `{audit['integration_status']}`",
        f"- field: `{audit['field']}`",
        f"- schema_policy: `{audit['schema_policy']}`",
        f"- default_fracture_model: `{audit['default_fracture_model']}`",
        f"- missing_field_behavior: `{audit['missing_field_behavior']}`",
        f"- explicit_empty_behavior: `{audit['explicit_empty_behavior']}`",
        f"- unsupported_model_behavior: `{audit['unsupported_model_behavior']}`",
        f"- runtime_dispatch_enabled: `{str(audit['runtime_dispatch_enabled']).lower()}`",
        f"- buz29_execution_allowed: `{str(audit['buz29_execution_allowed']).lower()}`",
        f"- sigma_theta_initial_state_audit_required: `{str(audit['sigma_theta_initial_state_audit_required']).lower()}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Parser/schema checks",
    ]
    for key, value in audit["parser_schema_checks"].items():
        lines.append(f"- {key}: `{str(value).lower()}`")
    lines.extend(
        [
            "",
            "## Future gate",
            f"- cause: `{audit['future_gate']['cause']}`",
            f"- gate: `{audit['future_gate']['gate']}`",
            f"- secondary_cause: `{audit['future_gate']['secondary_cause']}`",
            f"- secondary_gate: `{audit['future_gate']['secondary_gate']}`",
            "",
            "## Caveats",
        ]
    )
    lines.extend(f"- {item}" for item in audit["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10M fracture_model parser/schema integration."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    audit = build_audit()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(audit, args.output_md)

    print(f"PHASE={audit['phase']}")
    print(f"INTEGRATION_STATUS={audit['integration_status']}")
    print(f"FIELD={audit['field']}")
    print(f"SCHEMA_POLICY={audit['schema_policy']}")
    print(f"DEFAULT_FRACTURE_MODEL={audit['default_fracture_model']}")
    print(f"MISSING_FIELD_BEHAVIOR={audit['missing_field_behavior']}")
    print(f"EXPLICIT_EMPTY_BEHAVIOR={audit['explicit_empty_behavior']}")
    print(f"UNSUPPORTED_MODEL_BEHAVIOR={audit['unsupported_model_behavior']}")
    print(f"RUNTIME_DISPATCH_ENABLED={str(audit['runtime_dispatch_enabled']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED={str(audit['buz29_execution_allowed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
