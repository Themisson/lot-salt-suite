#!/usr/bin/env python3
"""Plan the sigma-theta source solution after the root-cause diagnosis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "master-B"
STATUS = "SIGMATHETA_SOURCE_SOLUTION_PLAN_READY"
SELECTED_PATH = "SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE"


def build_plan() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "solution_plan_status": STATUS,
        "selected_solution_path": SELECTED_PATH,
        "proposed_component": "PostDrillingSigmaThetaProvider",
        "provider_scope": "diagnostic_and_semi_physical_normalization",
        "implementation_allowed_next": True,
        "runtime_dispatch_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "pkn_behavior_change_allowed": False,
        "penny_shaped_runtime_enabled": False,
        "source_policy": {
            "explicit_diagnostic_input": "allowed_diagnostic_only",
            "synthetic_fixture": "allowed_diagnostic_only",
            "elastic_initial_wellbore_state": "allowed_semi_physical_with_caveat",
            "unknown": "rejected",
        },
        "required_result_semantics": {
            "state_time": "POST_DRILLING_BEFORE_LOT",
            "sign_convention": "COMPRESSION_POSITIVE",
            "reference_frame": "WELLBORE_WALL_TOTAL_STRESS",
            "physically_validated_default": False,
            "legacy_equivalent_default": False,
        },
        "implementation_steps": [
            "Create include/lot/PostDrillingSigmaThetaProvider.hpp.",
            "Create src/lot/PostDrillingSigmaThetaProvider.cpp.",
            "Add focused Catch2 tests for finite values, source rejection and caveats.",
            "Add the provider source to CMake without changing PKN solver behavior.",
            "Keep wiring to the diagnostic pre-runner for the next phase.",
        ],
        "blocking_rules": [
            "Reject physically_validated=true in the provider input.",
            "Reject legacy_equivalent=true in the provider input.",
            "Reject non-finite or non-positive sigma-theta values.",
            "Reject unknown source.",
            "Do not enable physical dispatch.",
        ],
        "recommended_next_phase": "MASTER_PHASE_C_IMPLEMENT_POST_DRILLING_SIGMATHETA_PROVIDER",
        "caveats": [
            "The plan does not claim physical validation.",
            "ElasticInitialWellboreState is semi-physical until a validated elastic derivation is added.",
            "PKN output compatibility remains a hard gate.",
        ],
    }


def write_markdown(path: Path, plan: dict[str, Any]) -> None:
    lines = [
        "# Fase B — plano de solucao da fonte sigma_theta",
        "",
        "## Resumo executivo",
        "",
        (
            "A solucao escolhida e implementar um `PostDrillingSigmaThetaProvider` "
            "pequeno, isolado e sem dispatch fisico. O provider centraliza a "
            "normalizacao de fonte, sinal, referencial e caveats antes de qualquer "
            "wiring no diagnostic pre-runner."
        ),
        "",
        f"- `solution_plan_status`: `{plan['solution_plan_status']}`",
        f"- `selected_solution_path`: `{plan['selected_solution_path']}`",
        f"- `proposed_component`: `{plan['proposed_component']}`",
        f"- `implementation_allowed_next`: `{plan['implementation_allowed_next']}`",
        f"- `runtime_dispatch_allowed_next`: `{plan['runtime_dispatch_allowed_next']}`",
        "",
        "## Semantica obrigatoria",
        "",
    ]
    for key, value in plan["required_result_semantics"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Passos de implementacao", ""])
    lines.extend(f"- {step}" for step in plan["implementation_steps"])
    lines.extend(["", "## Regras de bloqueio", ""])
    lines.extend(f"- {rule}" for rule in plan["blocking_rules"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in plan["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan the sigma-theta source solution for the limited gate."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    plan = build_plan()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, plan)

    print(f"phase={plan['phase']}")
    print(f"solution_plan_status={plan['solution_plan_status']}")
    print(f"selected_solution_path={plan['selected_solution_path']}")
    print(f"proposed_component={plan['proposed_component']}")
    print(f"implementation_allowed_next={plan['implementation_allowed_next']}")
    print(f"runtime_dispatch_allowed_next={plan['runtime_dispatch_allowed_next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
