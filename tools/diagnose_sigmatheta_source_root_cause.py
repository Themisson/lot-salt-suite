#!/usr/bin/env python3
"""Diagnose the current sigma-theta runtime source gap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "master-A"
STATUS = "SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE"


def build_diagnosis() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "diagnosis_status": STATUS,
        "sigma_theta_initial_runtime_available": False,
        "sigma_theta_current_runtime_available": False,
        "wellbore_pressure_runtime_available": True,
        "pressure_semantics_resolved": False,
        "sign_convention_resolved": False,
        "reference_frame_resolved": False,
        "elastic_provider_implementable": True,
        "diagnostic_source_available": True,
        "recommended_solution_path": STATUS,
        "implementation_allowed_next": True,
        "proposed_component": "PostDrillingSigmaThetaProvider",
        "source_evidence": {
            "diagnostic_input": "lot.fracture.sigma_theta_diagnostic_input",
            "gate_wiring": "FractureGateDiagnosticPreRunner",
            "pressure_runtime": "PknResult.wellbore_pressure_series_Pa",
            "existing_sigma_theta_runtime": "not available as physical runtime state",
        },
        "required_constraints": [
            "runtime_dispatch_enabled remains false",
            "BUZ29-PENNY remains blocked",
            "PKN physical outputs must remain unchanged",
            "PENNY_SHAPED remains diagnostic-only",
        ],
        "answers": {
            "initial_sigma_theta_runtime": "No physical runtime initial sigma-theta source exists.",
            "current_sigma_theta_runtime": "No physical runtime current sigma-theta source exists.",
            "elastic_state_reusable": (
                "No completed elastic wellbore state is wired, but a small provider can "
                "normalize explicit/semi-physical inputs safely."
            ),
            "wellbore_pressure_semantics": (
                "wellbore_pressure_Pa is available in PKN outputs; real-gate semantics "
                "are still not resolved for physical validation."
            ),
            "geometry_material_sufficiency": (
                "CaseData has geometry/material context, but a validated elastic "
                "sigma-theta derivation is not yet implemented."
            ),
            "implementation_shape": (
                "Add a PostDrillingSigmaThetaProvider and wire it to the diagnostic "
                "pre-runner before any real physical dispatch."
            ),
        },
        "files_likely_to_change": [
            "include/lot/PostDrillingSigmaThetaProvider.hpp",
            "src/lot/PostDrillingSigmaThetaProvider.cpp",
            "src/lot/FractureGateDiagnosticPreRunner.cpp",
            "tests/cpp/test_post_drilling_sigma_theta_provider.cpp",
            "tools/audit_post_drilling_sigma_theta_provider.py",
            "docs/119_post_drilling_sigma_theta_provider_implementation.md",
        ],
        "caveats": [
            "The diagnosis does not validate a physical fracture event.",
            "The first implementation should be diagnostic/semi-physical only.",
            "Legacy traces remain audit references, not physical runtime sources.",
        ],
    }


def write_markdown(path: Path, diagnosis: dict[str, Any]) -> None:
    lines = [
        "# Fase A — diagnostico da causa raiz da fonte sigma_theta",
        "",
        "## Resumo executivo",
        "",
        (
            "O limited_gate ja pode ser alimentado por "
            "`sigma_theta_diagnostic_input`, mas o runtime moderno ainda nao possui "
            "uma fonte fisica de `sigma_theta_initial` ou `sigma_theta_current`."
        ),
        "",
        f"Diagnostico: `{diagnosis['diagnosis_status']}`.",
        "",
        "## Evidencia",
        "",
        "| Item | Status | Evidencia |",
        "|---|---:|---|",
        (
            "| sigma_theta inicial runtime | nao disponivel | "
            "`FractureGateDiagnosticPreRunner` usa entrada diagnostica explicita |"
        ),
        (
            "| sigma_theta current runtime | nao disponivel | "
            "nao ha estado fisico corrente exposto ao gate |"
        ),
        (
            "| pressao de poco runtime | disponivel | "
            "`PknResult.wellbore_pressure_series_Pa` e writer moderno |"
        ),
        (
            "| provider elastico inicial | implementavel | "
            "pode normalizar fonte semi-fisica/diagnostica sem dispatch fisico |"
        ),
        "",
        "## Respostas objetivas",
        "",
    ]
    for key, value in diagnosis["answers"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            f"- `recommended_solution_path`: `{diagnosis['recommended_solution_path']}`",
            f"- `implementation_allowed_next`: `{diagnosis['implementation_allowed_next']}`",
            f"- `proposed_component`: `{diagnosis['proposed_component']}`",
            "",
            "## Arquivos provaveis da solucao",
            "",
        ]
    )
    lines.extend(f"- `{name}`" for name in diagnosis["files_likely_to_change"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in diagnosis["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose the sigma-theta source root cause for the limited fracture gate."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    diagnosis = build_diagnosis()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(diagnosis, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, diagnosis)

    print(f"phase={diagnosis['phase']}")
    print(f"diagnosis_status={diagnosis['diagnosis_status']}")
    print(
        "sigma_theta_initial_runtime_available="
        f"{diagnosis['sigma_theta_initial_runtime_available']}"
    )
    print(
        "sigma_theta_current_runtime_available="
        f"{diagnosis['sigma_theta_current_runtime_available']}"
    )
    print(f"wellbore_pressure_runtime_available={diagnosis['wellbore_pressure_runtime_available']}")
    print(f"elastic_provider_implementable={diagnosis['elastic_provider_implementable']}")
    print(f"implementation_allowed_next={diagnosis['implementation_allowed_next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
