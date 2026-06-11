#!/usr/bin/env python3
"""Decide the Phase 11.8B PennyShapedModel integration path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


PHASE = "11.8B"
STATUS = "PENNY_ADAPTER_OPT_IN_SELECTED"
CORE_STATUS = "PENNY_SHAPED_MINIMAL_CORE_IMPLEMENTED"
SELECTED_PATH = "diagnostic_adapter"
NEXT_PHASE = "PHASE11_8C_PENNY_ADAPTER_SPEC"


def build_decision() -> dict:
    integration_options = [
        {
            "option": "PENNY_CORE_REMAINS_DIAGNOSTIC_LIBRARY",
            "status": "AVAILABLE",
            "risk": "low",
            "reason": "Keeps the 11.8A core isolated, but does not exercise a structured integration contract.",
        },
        {
            "option": "PENNY_ADAPTER_OPT_IN_SELECTED",
            "status": "SELECTED",
            "risk": "low",
            "reason": "Allows a diagnostic adapter around PennyShapedModel without changing lot-pkn, parser, schemas, or protected cases.",
        },
        {
            "option": "PENNY_LOT_SIM_MODE_SELECTED",
            "status": "BLOCKED",
            "risk": "high",
            "reason": "A lot-sim route would require CLI/parser/schema decisions before BUZ29 readiness exists.",
        },
        {
            "option": "PENNY_YAML_ROUTE_SELECTED",
            "status": "DEFERRED",
            "risk": "medium",
            "reason": "The 11.7C YAML is fixture-only, not a runtime schema.",
        },
    ]
    return {
        "phase": PHASE,
        "status": STATUS,
        "current_core_status": CORE_STATUS,
        "api_current": {
            "header": "include/lot/PennyShapedModel.hpp",
            "source": "src/lot/PennyShapedModel.cpp",
            "inputs": [
                "young_modulus_Pa",
                "poisson_ratio",
                "viscosity_Pa_min",
                "flow_rate_m3_min",
                "elapsed_since_opening_min",
                "wellbore_pressure_Pa",
                "sigma_theta_compression_positive_Pa",
                "volume_multiplier",
            ],
            "outputs": [
                "plane_strain_modulus_Pa",
                "opening_m",
                "radius_m",
                "pressure_factor",
                "fracture_volume_proxy_m3",
            ],
            "validations": [
                "finite numeric inputs",
                "positive elastic modulus",
                "poisson_ratio in [0, 0.5)",
                "positive viscosity",
                "non-negative flow rate and elapsed time",
                "positive sigma theta",
            ],
        },
        "integration_options": integration_options,
        "selected_integration_path": SELECTED_PATH,
        "blocked_options": [
            "PENNY_LOT_SIM_MODE_SELECTED",
            "PENNY_YAML_ROUTE_SELECTED",
        ],
        "required_next_artifacts": [
            "docs/65_penny_diagnostic_adapter_spec.md",
            "tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml",
            "tools/validate_phase11_8c_penny_adapter_spec.py",
        ],
        "recommended_next_phase": NEXT_PHASE,
        "physical_validation": False,
        "legacy_equivalence": False,
        "buz29_validation": False,
        "lot_pkn_behavior_changed": False,
        "caveats": [
            "Phase 11.8B does not validate BUZ29.",
            "Phase 11.8B does not declare legacy equivalence.",
            "The selected adapter path must remain opt-in and diagnostic.",
            "lot-pkn, parser, schemas, PknModel, and PknRunner must remain unchanged in the next specification phase.",
        ],
    }


def write_markdown(path: Path, decision: dict) -> None:
    lines = [
        "# Phase 11.8B PennyShaped integration decision",
        "",
        "## Summary",
        "",
        f"- `phase`: `{decision['phase']}`",
        f"- `status`: `{decision['status']}`",
        f"- `current_core_status`: `{decision['current_core_status']}`",
        f"- `selected_integration_path`: `{decision['selected_integration_path']}`",
        f"- `recommended_next_phase`: `{decision['recommended_next_phase']}`",
        "",
        "A decisão da 11.8B não valida BUZ29, não declara equivalência com o legado e não transforma o núcleo penny-shaped em rota oficial do lot-sim. Ela apenas seleciona o caminho de integração diagnóstica.",
        "",
        "## Current API",
        "",
        f"- Header: `{decision['api_current']['header']}`",
        f"- Source: `{decision['api_current']['source']}`",
        "",
        "### Inputs",
        "",
    ]
    lines.extend(f"- `{item}`" for item in decision["api_current"]["inputs"])
    lines.extend(["", "### Outputs", ""])
    lines.extend(f"- `{item}`" for item in decision["api_current"]["outputs"])
    lines.extend(["", "## Integration options", "", "| Option | Status | Risk | Reason |", "|---|---|---|---|"])
    for option in decision["integration_options"]:
        lines.append(
            f"| `{option['option']}` | `{option['status']}` | `{option['risk']}` | {option['reason']} |"
        )
    lines.extend(["", "## Required next artifacts", ""])
    lines.extend(f"- `{item}`" for item in decision["required_next_artifacts"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in decision["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision = build_decision()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, decision)
    print(f"PHASE={decision['phase']}")
    print(f"STATUS={decision['status']}")
    print(f"CURRENT_CORE_STATUS={decision['current_core_status']}")
    print(f"SELECTED_INTEGRATION_PATH={decision['selected_integration_path']}")
    print(f"NEXT_PHASE={decision['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
