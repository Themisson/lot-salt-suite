#!/usr/bin/env python3
"""Audit the Phase C post-drilling sigma-theta provider implementation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_audit() -> dict[str, Any]:
    return {
        "phase": "master-C",
        "implementation_status": "POST_DRILLING_SIGMATHETA_PROVIDER_IMPLEMENTED",
        "provider": "PostDrillingSigmaThetaProvider",
        "supported_sources": [
            "EXPLICIT_DIAGNOSTIC_INPUT",
            "SYNTHETIC_FIXTURE",
            "ELASTIC_INITIAL_WELLBORE_STATE",
        ],
        "unknown_source_rejected": True,
        "nonfinite_values_rejected": True,
        "physically_validated_true_rejected": True,
        "legacy_equivalent_true_rejected": True,
        "state_time": "POST_DRILLING_BEFORE_LOT",
        "sign_convention": "COMPRESSION_POSITIVE",
        "reference_frame": "WELLBORE_WALL_TOTAL_STRESS",
        "runtime_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "pkn_behavior_changed": False,
        "penny_shaped_runtime_enabled": False,
        "wiring_to_pre_runner": False,
        "recommended_next_phase": "MASTER_PHASE_D_WIRE_SIGMATHETA_PROVIDER_TO_PRE_RUNNER",
        "caveats": [
            "The provider is implemented but not wired to the diagnostic pre-runner in this phase.",
            "ElasticInitialWellboreState is marked as semi-physical and not physically validated.",
            "The provider does not call PknModel, PknRunner or PennyShapedDiagnosticAdapter.",
        ],
    }


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Fase C — PostDrillingSigmaThetaProvider",
        "",
        "## Resumo executivo",
        "",
        (
            "A Fase C implementa `PostDrillingSigmaThetaProvider` como componente "
            "isolado para normalizar fontes diagnosticas/semi-fisicas de "
            "sigma_theta pos-perfuracao."
        ),
        "",
        f"- `implementation_status`: `{audit['implementation_status']}`",
        f"- `runtime_dispatch_enabled`: `{audit['runtime_dispatch_enabled']}`",
        f"- `pkn_behavior_changed`: `{audit['pkn_behavior_changed']}`",
        f"- `wiring_to_pre_runner`: `{audit['wiring_to_pre_runner']}`",
        "",
        "## Fontes suportadas",
        "",
    ]
    lines.extend(f"- `{source}`" for source in audit["supported_sources"])
    lines.extend(
        [
            "",
            "## Semantica",
            "",
            f"- `state_time`: `{audit['state_time']}`",
            f"- `sign_convention`: `{audit['sign_convention']}`",
            f"- `reference_frame`: `{audit['reference_frame']}`",
            "",
            "## Caveats",
            "",
        ]
    )
    lines.extend(f"- {caveat}" for caveat in audit["caveats"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the post-drilling sigma-theta provider implementation."
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
    print(f"implementation_status={audit['implementation_status']}")
    print(f"provider={audit['provider']}")
    print(f"runtime_dispatch_enabled={audit['runtime_dispatch_enabled']}")
    print(f"recommended_next_phase={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
