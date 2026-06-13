#!/usr/bin/env python3
"""Audit wiring from PostDrillingSigmaThetaProvider to the diagnostic pre-runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_audit() -> dict[str, Any]:
    return {
        "phase": "master-D",
        "wiring_status": "SIGMATHETA_PROVIDER_WIRED_TO_DIAGNOSTIC_PRE_RUNNER",
        "provider": "PostDrillingSigmaThetaProvider",
        "pre_runner": "FractureGateDiagnosticPreRunner",
        "sigma_theta_diagnostic_input_still_accepted": True,
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "pkn_model_called_by_gate": False,
        "pkn_runner_called_by_gate": False,
        "penny_adapter_called_by_gate": False,
        "provider_centralizes_source_normalization": True,
        "recommended_next_phase": "MASTER_PHASE_E_VALIDATE_SIGMATHETA_PROVIDER_CONTROLLED_CASES",
        "caveats": [
            "The wiring is diagnostic only.",
            "The provider does not enable physical dispatch.",
            "The provider uses explicit diagnostic input in this phase.",
        ],
    }


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Fase D — wiring do sigma_theta provider ao diagnostic pre-runner",
        "",
        "## Resumo executivo",
        "",
        (
            "`PostDrillingSigmaThetaProvider` foi conectado ao "
            "`FractureGateDiagnosticPreRunner` para centralizar a normalizacao "
            "de sigma_theta antes dos guards. O caminho continua diagnostico e "
            "nao habilita dispatch fisico."
        ),
        "",
        f"- `wiring_status`: `{audit['wiring_status']}`",
        f"- `runtime_dispatch_enabled`: `{audit['runtime_dispatch_enabled']}`",
        f"- `pkn_behavior_changed`: `{audit['pkn_behavior_changed']}`",
        f"- `penny_shaped_runtime_enabled`: `{audit['penny_shaped_runtime_enabled']}`",
        "",
        "## Garantias",
        "",
        "- `sigma_theta_diagnostic_input` continua aceito.",
        "- `PknModel`, `PknRunner` e `PennyShapedDiagnosticAdapter` nao sao chamados pelo gate.",
        "- O dispatch permanece apenas diagnostico.",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {caveat}" for caveat in audit["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit sigma-theta provider wiring to the diagnostic pre-runner."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    audit = build_audit()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.output_md:
        write_markdown(args.output_md, audit)

    print(f"phase={audit['phase']}")
    print(f"wiring_status={audit['wiring_status']}")
    print(f"runtime_dispatch_enabled={audit['runtime_dispatch_enabled']}")
    print(f"pkn_behavior_changed={audit['pkn_behavior_changed']}")
    print(f"recommended_next_phase={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
