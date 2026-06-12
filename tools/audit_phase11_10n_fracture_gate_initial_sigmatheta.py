"""Audit Phase 11.10N fracture gate initial sigma-theta state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "11.10N"
SIGMATHETA_INITIAL_STATE = "SIGMATHETA_INITIAL_STATE_MISSING"
FRACTURE_GATE_STATUS = "FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING"
PRESSURE_SEMANTICS = "PRESSURE_SIGMATHETA_SEMANTICS_PARTIAL_REQUIRES_ALIGNMENT"
SIGN_CONVENTION = "SIGN_CONVENTION_REQUIRES_REVIEW"
NEXT_PHASE = "PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING"


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def build_audit(repo_root: Path = Path(".")) -> dict[str, Any]:
    pkn_model = _read_text(repo_root / "src/lot/PknModel.cpp")
    pkn_runner = _read_text(repo_root / "src/lot/PknRunner.cpp")
    parser = _read_text(repo_root / "src/io/CaseParser.cpp")
    provider_header = _read_text(repo_root / "include/lot/SigmaThetaProvider.hpp")
    result_header = _read_text(repo_root / "include/lot/PknResult.hpp")
    salt_bridge = _read_text(repo_root / "src/salt/SaltCreepTimeBridge.cpp")
    wall_stress_header = _read_text(repo_root / "include/salt/SaltWallStressDiagnostics.hpp")
    breakdown = _read_text(repo_root / "src/coupling/LotSaltSigmaThetaBreakdown.cpp")
    known_issues = _read_text(repo_root / "docs/08_known_issues.md")
    phase_87 = _read_text(repo_root / "docs/87_fracture_model_parser_schema_integration.md")

    pkn_consumes_static = _contains_all(
        pkn_model,
        [
            "FractureInitiationCriterion::SigmaThetaStatic",
            "trial_pressure_Pa - sigma_theta_Pa",
            "sigma_theta_compression_positive_Pa",
        ],
    )
    pkn_consumes_provider = _contains_all(
        pkn_model,
        [
            "FractureInitiationCriterion::SigmaThetaProviderRuntime",
            "sigma_theta_provider->sample",
            "validate_sigma_theta_point",
        ],
    )
    parser_reads_static = _contains_all(
        parser,
        [
            "sigma_theta_static",
            "lot.fracture.initiation.sigma_theta.compression_positive",
        ],
    )
    parser_reads_time_series = _contains_all(
        parser,
        [
            "sigma_theta_time_series",
            "sigma_theta_series",
            "sigma_theta_compression_positive",
        ],
    )
    runner_builds_provider = _contains_all(
        pkn_runner,
        [
            "SigmaThetaTimeSeriesProvider",
            "parse_fracture_initiation",
            "sigma_theta_provider",
        ],
    )
    salt_wall_stress_available = _contains_all(
        salt_bridge + wall_stress_header,
        [
            "wall_stress_diagnostics",
            "sigma_theta_compression_positive_Pa",
        ],
    )
    coupling_diagnostic_available = _contains_all(
        breakdown,
        [
            "evaluate_sigma_theta_breakdown_point",
            "pressure_Pa - layer.sigma_theta_compression_positive_Pa",
        ],
    )
    compression_positive_documented = (
        "compressão POSITIVA" in known_issues
        or "compressao positiva" in known_issues
        or "compression_positive" in provider_header
    )
    initial_state_gate_recorded = (
        "SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH" in phase_87
    )

    # This phase is intentionally conservative: existing code can consume
    # static/time-series/provider sigma-theta values, but there is no audited
    # proof that the runtime value is initialized from a post-drilling
    # geomechanical state before the fracture gate.
    blocking_gaps = [
        "No verified sigma_theta_initial_after_drilling is wired into PknModel.",
        "Current sigma_theta_static and sigma_theta_time_series inputs are diagnostic YAML/provider values.",
        "SaltWallStressDiagnostics exists as an opt-in diagnostic route, not as default fracture gate runtime.",
        "The LOT t=0 state is not proven to include post-drilling elastic/geomechanical redistribution.",
        "Pressure source and sigma_theta reference are only partially aligned for future dispatch.",
        "Compression-positive sign convention is documented, but future model dispatch still needs an explicit gate contract.",
    ]

    return {
        "phase": PHASE,
        "sigmatheta_initial_state": SIGMATHETA_INITIAL_STATE,
        "fracture_gate_status": FRACTURE_GATE_STATUS,
        "pressure_semantics": PRESSURE_SEMANTICS,
        "sign_convention": SIGN_CONVENTION,
        "t0_lot_vs_drilling_distinction": True,
        "dispatch_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "blocking_gaps": blocking_gaps,
        "recommended_next_phase": NEXT_PHASE,
        "audit_checks": {
            "pkn_model_consumes_sigma_theta_static": pkn_consumes_static,
            "pkn_model_consumes_sigma_theta_provider_runtime": pkn_consumes_provider,
            "parser_reads_sigma_theta_static": parser_reads_static,
            "parser_reads_sigma_theta_time_series": parser_reads_time_series,
            "pkn_runner_builds_time_series_provider": runner_builds_provider,
            "salt_wall_stress_diagnostics_available_opt_in": salt_wall_stress_available,
            "coupling_sigma_theta_diagnostic_available": coupling_diagnostic_available,
            "compression_positive_documented": compression_positive_documented,
            "initial_state_gate_recorded_by_phase_11_10m": initial_state_gate_recorded,
        },
        "sigma_theta_sources": [
            {
                "source": "YAML sigma_theta_static",
                "path": "src/io/CaseParser.cpp -> CaseData.lot.sigma_theta_fracture -> PknRunner -> PknModel",
                "status": "DIAGNOSTIC_INPUT_NOT_POST_DRILLING_STATE_PROOF",
            },
            {
                "source": "YAML sigma_theta_time_series",
                "path": "CaseParser -> SigmaThetaTimeSeriesProvider -> PknModel",
                "status": "DIAGNOSTIC_TIMESERIES_NOT_RUNTIME_GEOMECHANICAL_INITIALIZATION",
            },
            {
                "source": "SaltWallStressDiagnostics",
                "path": "SaltCreepTimeBridge -> SaltWallStressDiagnostics -> LotSaltSigmaThetaDiagnostic",
                "status": "OPT_IN_DIAGNOSTIC_NOT_DEFAULT_FRACTURE_GATE_RUNTIME",
            },
        ],
        "pressure_audit": {
            "wellbore_pressure_trial_Pa": "Used by sigma_theta_time_series/provider gate.",
            "wellbore_pressure_Pa": "Required by sigma_theta_static parser validation.",
            "constant_pressure_breakdown": "Compares trial pressure increment above initial_pressure_Pa.",
            "risk": "Total pressure can be compared against an incremental or non-initialized stress unless the gate contract is explicit.",
        },
        "sign_audit": {
            "documented_convention": "compression-positive geomechanics",
            "diagnostic_algebra": "margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa",
            "risk": "Future dispatch must state whether sigma_theta is total compression-positive, effective stress, or pressure-equivalent threshold.",
        },
        "required_statuses": [
            "PHASE11_10N_FRACTURE_GATE_INITIAL_SIGMATHETA_AUDITED",
            "SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH",
            "T0_LOT_DISTINCT_FROM_T0_DRILLING",
            "PRESSURE_SIGMATHETA_SEMANTICS_REQUIRED",
            "SIGMATHETA_SIGN_CONVENTION_REQUIRED",
            "DISPATCH_REMAINS_BLOCKED_UNTIL_GATE_SAFE",
        ],
    }


def write_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10N fracture gate initial sigma-theta audit",
        "",
        f"- phase: `{audit['phase']}`",
        f"- sigmatheta_initial_state: `{audit['sigmatheta_initial_state']}`",
        f"- fracture_gate_status: `{audit['fracture_gate_status']}`",
        f"- pressure_semantics: `{audit['pressure_semantics']}`",
        f"- sign_convention: `{audit['sign_convention']}`",
        f"- dispatch_allowed_next: `{str(audit['dispatch_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(audit['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(audit['buz29_execution_allowed_next']).lower()}`",
        f"- recommended_next_phase: `{audit['recommended_next_phase']}`",
        "",
        "## Audit checks",
    ]
    for key, value in audit["audit_checks"].items():
        lines.append(f"- {key}: `{str(value).lower()}`")
    lines.extend(["", "## Sigma-theta sources"])
    for source in audit["sigma_theta_sources"]:
        lines.append(f"- `{source['source']}`: {source['status']} ({source['path']})")
    lines.extend(["", "## Blocking gaps"])
    lines.extend(f"- {gap}" for gap in audit["blocking_gaps"])
    lines.extend(["", "## Required statuses"])
    lines.extend(f"- `{status}`" for status in audit["required_statuses"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10N fracture gate initial sigma-theta state."
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
    print(f"SIGMATHETA_INITIAL_STATE={audit['sigmatheta_initial_state']}")
    print(f"FRACTURE_GATE_STATUS={audit['fracture_gate_status']}")
    print(f"PRESSURE_SEMANTICS={audit['pressure_semantics']}")
    print(f"SIGN_CONVENTION={audit['sign_convention']}")
    print(f"DISPATCH_ALLOWED_NEXT={str(audit['dispatch_allowed_next']).lower()}")
    print(f"RUNTIME_EXECUTION_ALLOWED_NEXT={str(audit['runtime_execution_allowed_next']).lower()}")
    print(f"BUZ29_EXECUTION_ALLOWED_NEXT={str(audit['buz29_execution_allowed_next']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
