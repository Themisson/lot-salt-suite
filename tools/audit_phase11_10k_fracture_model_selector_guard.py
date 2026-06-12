#!/usr/bin/env python3
"""Audit the Phase 11.10K isolated fracture_model selector guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10K"
IMPLEMENTED = "FRACTURE_MODEL_SELECTOR_GUARD_IMPLEMENTED"
PARTIAL = "FRACTURE_MODEL_SELECTOR_GUARD_PARTIAL"
BLOCKED = "FRACTURE_MODEL_SELECTOR_GUARD_BLOCKED"
INCONCLUSIVE = "FRACTURE_MODEL_SELECTOR_GUARD_INCONCLUSIVE"
NEXT_PHASE = "PHASE11_10L_SPECIFY_PARSER_SCHEMA_INTEGRATION_FOR_FRACTURE_MODEL"


def build_audit() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "implementation_status": IMPLEMENTED,
        "default_fracture_model": "PKN",
        "missing_field_behavior": "DEFAULT_TO_PKN",
        "explicit_empty_behavior": "ERROR_EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED",
        "supported_models": ["PKN", "PENNY_SHAPED"],
        "explicit_opt_in_models": ["PENNY_SHAPED"],
        "blocked_models": [
            "KGD",
            "KGD_CIRCULAR",
            "KGD_ELLIPTICAL",
            "RADIAL",
            "ELLIPTICAL",
            "UNKNOWN",
        ],
        "normalization_rules": [
            {"input": "PKN", "canonical": "PKN"},
            {"input": "pkn", "canonical": "PKN"},
            {"input": "lot-pkn", "canonical": "PKN"},
            {"input": "lot_pkn", "canonical": "PKN"},
            {"input": "PENNY_SHAPED", "canonical": "PENNY_SHAPED"},
            {"input": "penny_shaped", "canonical": "PENNY_SHAPED"},
            {"input": "penny-shaped", "canonical": "PENNY_SHAPED"},
            {"input": "penny", "canonical": "PENNY_SHAPED"},
        ],
        "parser_integrated": False,
        "schema_integrated": False,
        "runtime_integrated": False,
        "buz29_executed": False,
        "lot_pkn_behavior_changed": False,
        "fracture_initiation_gate_required": True,
        "sigma_theta_sign_convention_required": True,
        "pkn_status": {
            "diagnostic_only": False,
            "runtime_supported_now": True,
            "source_when_missing": "Defaulted",
        },
        "penny_shaped_status": {
            "diagnostic_only": True,
            "physically_validated": False,
            "legacy_equivalent": False,
            "runtime_supported_now": False,
            "source": "Explicit",
        },
        "classifications": [
            IMPLEMENTED,
            "PKN_DEFAULT_WHEN_FRACTURE_MODEL_MISSING",
            "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY",
            "EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED",
            "UNSUPPORTED_FRACTURE_MODELS_BLOCKED",
            "PARSER_SCHEMA_RUNTIME_NOT_INTEGRATED",
        ],
        "recommended_next_phase": NEXT_PHASE,
        "caveats": [
            "The guard is implemented as an isolated C++ helper.",
            "The guard is not integrated into parser, schema, CLI or official runtime.",
            "BUZ29-PENNY is not executed.",
            "PENNY_SHAPED remains diagnostic, not physically validated and not legacy-equivalent.",
        ],
    }


def write_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10K Fracture-Model Selector Guard Audit",
        "",
        f"- phase: `{audit['phase']}`",
        f"- implementation_status: `{audit['implementation_status']}`",
        f"- default_fracture_model: `{audit['default_fracture_model']}`",
        f"- missing_field_behavior: `{audit['missing_field_behavior']}`",
        f"- explicit_empty_behavior: `{audit['explicit_empty_behavior']}`",
        f"- supported_models: `{', '.join(audit['supported_models'])}`",
        f"- explicit_opt_in_models: `{', '.join(audit['explicit_opt_in_models'])}`",
        f"- blocked_models: `{', '.join(audit['blocked_models'])}`",
        f"- parser_integrated: `{str(audit['parser_integrated']).lower()}`",
        f"- schema_integrated: `{str(audit['schema_integrated']).lower()}`",
        f"- runtime_integrated: `{str(audit['runtime_integrated']).lower()}`",
        f"- buz29_executed: `{str(audit['buz29_executed']).lower()}`",
        f"- lot_pkn_behavior_changed: `{str(audit['lot_pkn_behavior_changed']).lower()}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in audit["classifications"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in audit["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10K fracture_model selector guard implementation."
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
    print(f"IMPLEMENTATION_STATUS={audit['implementation_status']}")
    print(f"DEFAULT_FRACTURE_MODEL={audit['default_fracture_model']}")
    print(f"MISSING_FIELD_BEHAVIOR={audit['missing_field_behavior']}")
    print(f"EXPLICIT_EMPTY_BEHAVIOR={audit['explicit_empty_behavior']}")
    print(f"SUPPORTED_MODELS={','.join(audit['supported_models'])}")
    print(f"PARSER_INTEGRATED={str(audit['parser_integrated']).lower()}")
    print(f"SCHEMA_INTEGRATED={str(audit['schema_integrated']).lower()}")
    print(f"RUNTIME_INTEGRATED={str(audit['runtime_integrated']).lower()}")
    print(f"BUZ29_EXECUTED={str(audit['buz29_executed']).lower()}")
    print(f"LOT_PKN_BEHAVIOR_CHANGED={str(audit['lot_pkn_behavior_changed']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
