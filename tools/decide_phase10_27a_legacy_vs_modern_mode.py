from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "10.27A"
SOURCE = "DOCUMENTED_PHASE_SUMMARY"


PHASE_SUMMARY: dict[str, dict[str, Any]] = {
    "10.19C": {
        "classification": "COMPLIANCE_EFFECTIVE",
        "C_fluid_1_per_Pa": 6.4e-10,
        "C_geom_1_per_Pa": 1.8571966938610005e-8,
        "C_eff_1_per_Pa": 1.9211966938610006e-8,
        "relative_error_max_pressure": -0.02468924338685035,
    },
    "10.20C": {
        "classification": "ELASTIC_COMPLIANCE_UNDERCOMPLIANT",
        "modern_first_dP_elastic_compliance_Pa": 43639672.35675542,
        "legacy_first_dP_Pa": 1845413.7784679066,
    },
    "10.22C": {
        "classification": "UNIFIED_TRACE_COMPLETE_OPENING_AND_SINK_CONFIRMED",
        "first_opened_time_s": 510.0,
        "first_sink_positive_time_s": 540.0,
        "sink_delay_s": 30.0,
        "first_pw_Pa": 66769500.0,
        "first_sigmaTheta_Pa": 66666600.0,
        "first_margin_Pa": 102865.0,
    },
    "10.23A": {
        "classification": "NEXT_STEP_SINK_EFFECTIVE",
        "relative_error_max_pressure": 0.00204,
    },
    "10.23B": {
        "classification": "COMBINED_DIAGNOSTIC_PRESSURE_OK_OPENING_SHIFTED",
        "relative_error_max_pressure": -0.02468924338685035,
    },
    "10.23C": {
        "classification": "NEXT_MODEL_SIGMA_THETA_RUNTIME",
        "pressure_tabulated_geometric": "blocked",
    },
    "10.25B": {
        "classification": "SIGMA_THETA_REFINED_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED",
        "number_of_sigmaTheta_points": 44,
        "legacy_first_opened_time_s": 510.0,
        "modern_fracture_initiation_time_s": 660.0,
        "opening_time_error_s": 150.0,
        "modern_sink_delay_s": 30.0,
        "relative_error_max_pressure": -0.02468924338685035,
    },
    "10.25C": {
        "classification": "NEXT_MODEL_PRESSURE_SOURCE_TIMING_REVIEW",
    },
    "10.26A": {
        "cause": "SIGMATHETA_MESH_OR_DOMAIN_MISMATCH",
        "gate": "LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING",
        "pressure_source_timing_gate_before_geometry_gate": "MODERN_TRACE_EXPORT_REQUIRED",
    },
    "10.26B": {
        "classification": "APBSALT1D_EQUIVALENCE_METADATA_ONLY",
        "outer_radius_m": 8.0,
        "radial_elements": 15,
        "ratio": 10.0,
        "integration_order": 3,
        "sampling": "legacy_elem0_sig_2_0",
        "consumption_status": "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED",
    },
    "10.26C": {
        "classification": "APBSALT1D_METADATA_ONLY_CONFIRMED",
        "next_phase_recommendation": "NEXT_PHASE_IMPLEMENT_SAMPLING_BRIDGE",
    },
    "10.26D": {
        "classification": "APBSALT1D_SAMPLING_BRIDGE_METADATA_ONLY",
        "gate": "APBSALT1D_SAMPLING_BRIDGE_BLOCKED_NO_SPATIAL_SAMPLES",
    },
}


CLASSIFICATIONS = [
    "LEGACY_EQUIVALENCE_MODE_REQUIRED_FOR_REGRESSION",
    "MODERN_REFINED_MODE_ACCEPTABLE_FOR_ANALYSIS",
    "MODERN_REFINED_MODE_NOT_LEGACY_EQUIVALENT",
    "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY",
    "APBSALT1D_SAMPLING_BRIDGE_BLOCKED",
    "APBSALT1D_SOLVER_EQUIVALENCE_REQUIRED_FOR_STRICT_MATCH",
    "CONSTANT_GEOMETRIC_REMAINS_DIAGNOSTIC_BASELINE",
    "SIGMATHETA_RUNTIME_STILL_FUTURE_WORK",
]


def decision_matrix() -> list[dict[str, str]]:
    return [
        {
            "aspect": "radial_domain",
            "legacy_equivalence_mode": "APBSalt1D outer_radius_m = 8 m",
            "modern_refined_mode": "modern bridge/default outer_radius_m = 1.556 m",
            "current_status": "different domains",
            "risk": "forcing one mode into the other hides geometry assumptions",
            "recommended_use": "legacy-equivalence for regression; modern-refined for analysis",
            "blocking_gate": "LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING",
            "next_action": "choose mode explicitly before comparing opening time",
        },
        {
            "aspect": "radial_mesh",
            "legacy_equivalence_mode": "15 APBSalt1D radial elements",
            "modern_refined_mode": "40 radial elements in current bridge defaults",
            "current_status": "not equivalent",
            "risk": "opening shift can reflect mesh/domain difference",
            "recommended_use": "do not treat 660 s as error without equivalence",
            "blocking_gate": "LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING",
            "next_action": "implement radial solver equivalence only for strict regression",
        },
        {
            "aspect": "mesh_ratio",
            "legacy_equivalence_mode": "ratio = 10",
            "modern_refined_mode": "ratio not consumed by current bridge",
            "current_status": "metadata-only",
            "risk": "declared metadata may be mistaken for consumed geometry",
            "recommended_use": "report explicitly as not consumed",
            "blocking_gate": "APBSALT1D_METADATA_ONLY_CONFIRMED",
            "next_action": "add real mesh-ratio support only if strict match is required",
        },
        {
            "aspect": "integration_order",
            "legacy_equivalence_mode": "integration_order = 3",
            "modern_refined_mode": "AxisymL3 uses three-point integration internally",
            "current_status": "partially aligned",
            "risk": "same order does not imply same sampling point",
            "recommended_use": "document but do not claim equivalence",
            "blocking_gate": "LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING",
            "next_action": "tie order to explicit sampling only in equivalence mode",
        },
        {
            "aspect": "sigmaTheta_sampling_point",
            "legacy_equivalence_mode": "mdl->getElem(0)->getSigmaTheta(); sig(2,0)",
            "modern_refined_mode": "time-series provider has no spatial samples",
            "current_status": "blocked",
            "risk": "legacy elem0 cannot be mapped from scalar time series",
            "recommended_use": "do not claim APBSalt1D consumption",
            "blocking_gate": "APBSALT1D_SAMPLING_BRIDGE_BLOCKED",
            "next_action": "create wall-stress spatial sampling provider if needed",
        },
        {
            "aspect": "sigmaTheta_source",
            "legacy_equivalence_mode": "APBSalt1D criterion trace",
            "modern_refined_mode": "refined sigma_theta_time_series",
            "current_status": "diagnostic source only",
            "risk": "time-series is not a runtime salt stress source",
            "recommended_use": "acceptable for controlled diagnostic cases",
            "blocking_gate": "SIGMATHETA_RUNTIME_STILL_FUTURE_WORK",
            "next_action": "implement SaltWallStressDiagnostics provider for physical route",
        },
        {
            "aspect": "pressure_source_timing",
            "legacy_equivalence_mode": "pw from pi + dP at legacy criterion timing",
            "modern_refined_mode": "wellbore_pressure_trial_Pa in diagnostic case",
            "current_status": "blocked by geometry",
            "risk": "adjusting timing may compensate for mesh mismatch",
            "recommended_use": "do not tune until geometry decision is made",
            "blocking_gate": "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY",
            "next_action": "return only after geometry consumed or rejected",
        },
        {
            "aspect": "compliance_model",
            "legacy_equivalence_mode": "equivalent legacy behavior inferred diagnostically",
            "modern_refined_mode": "constant_geometric opt-in diagnostic baseline",
            "current_status": "pressure scale acceptable but diagnostic",
            "risk": "constant compliance is not physical validation",
            "recommended_use": "keep as comparison baseline",
            "blocking_gate": "CONSTANT_GEOMETRIC_REMAINS_DIAGNOSTIC_BASELINE",
            "next_action": "do not replace with elastic simple model for BUZ67D",
        },
        {
            "aspect": "sink_timing",
            "legacy_equivalence_mode": "sink positive one step after opening",
            "modern_refined_mode": "sink_timing: next_step",
            "current_status": "aligned for diagnostic",
            "risk": "sink match does not validate fracture physics",
            "recommended_use": "retain as diagnostic setting",
            "blocking_gate": "none for Level 1 structural diagnostic",
            "next_action": "preserve until physical coupling is defined",
        },
        {
            "aspect": "thermal_term",
            "legacy_equivalence_mode": "thermal and compressibility terms embedded in balance",
            "modern_refined_mode": "not a validated tabulated pressure model",
            "current_status": "pressure_tabulated_geometric blocked",
            "risk": "thermal correction sign ambiguity",
            "recommended_use": "document only",
            "blocking_gate": "PRESSURE_TABULATED_STILL_BLOCKED",
            "next_action": "do not implement in this route",
        },
        {
            "aspect": "dMl_leakoff_terms",
            "legacy_equivalence_mode": "legacy balance includes dMl/leakoff terms",
            "modern_refined_mode": "diagnostic sink/leakoff handling",
            "current_status": "partially audited",
            "risk": "termwise equivalence remains incomplete",
            "recommended_use": "avoid physical validation claims",
            "blocking_gate": "UNIFIED_TRACE_REQUIRED_FOR_TERMWISE_MATCH",
            "next_action": "keep Level 1 gate closed",
        },
        {
            "aspect": "runtime_salt_coupling",
            "legacy_equivalence_mode": "APBSalt1D legacy path",
            "modern_refined_mode": "SaltWallStressDiagnostics exists but not LOT runtime default",
            "current_status": "future work",
            "risk": "dependency cycle if LOT knows salt/coupling directly",
            "recommended_use": "opt-in provider bridge only",
            "blocking_gate": "SIGMATHETA_RUNTIME_STILL_FUTURE_WORK",
            "next_action": "design provider without changing default lot-pkn",
        },
        {
            "aspect": "validation_status",
            "legacy_equivalence_mode": "regression target only when geometry is matched",
            "modern_refined_mode": "analysis mode, not legacy regression",
            "current_status": "decision recorded",
            "risk": "confusing legacy match with physical truth",
            "recommended_use": "separate reports and labels",
            "blocking_gate": "LEGACY_EQUIVALENCE_VS_MODERN_REFINED_DECISION_RECORDED",
            "next_action": "choose next phase according to project goal",
        },
    ]


def decide(objective: str = "modern_refined") -> dict[str, Any]:
    objective = objective.strip().lower()
    if objective == "strict_legacy":
        next_phase = "NEXT_PHASE_LEGACY_EQUIVALENCE_RADIAL_SOLVER"
        rationale = (
            "Strict LOT_Tese reproduction requires a radial solver/sampler that consumes "
            "APBSalt1D domain, mesh ratio and elem0/sig(2,0) sampling."
        )
    elif objective == "salt_wall_stress_runtime":
        next_phase = "NEXT_PHASE_IMPLEMENT_SALT_WALL_STRESS_RUNTIME"
        rationale = (
            "Physical modern analysis should prioritize an opt-in SaltWallStressDiagnostics "
            "provider instead of forcing legacy mesh equivalence."
        )
    elif objective == "return_to_pressure_timing":
        next_phase = "NEXT_PHASE_RETURN_TO_PRESSURE_SOURCE_TIMING"
        rationale = (
            "This is allowed only after a formal decision to ignore legacy geometry "
            "equivalence or after real geometric equivalence is implemented."
        )
    elif objective == "modern_refined":
        next_phase = "NEXT_PHASE_MODERN_REFINED_DOCUMENTATION_AND_VALIDATION"
        rationale = (
            "Modern-refined mode may accept the 660 s opening as a non-regression result "
            "because domain, mesh and sampling differ from APBSalt1D."
        )
    else:
        next_phase = "NEXT_PHASE_INCONCLUSIVE"
        rationale = "Unknown objective; cannot choose between regression and modern analysis."

    return {
        "phase": PHASE,
        "source": SOURCE,
        "objective": objective,
        "main_decision": next_phase,
        "rationale": rationale,
        "classifications": CLASSIFICATIONS,
        "pressure_source_timing_allowed": next_phase == "NEXT_PHASE_RETURN_TO_PRESSURE_SOURCE_TIMING",
        "pressure_source_timing_gate": "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY",
        "apbsalt1d_status": {
            "metadata": "APBSALT1D_METADATA_ONLY_CONFIRMED",
            "sampling_bridge": "APBSALT1D_SAMPLING_BRIDGE_BLOCKED",
            "strict_solver_equivalence": "APBSALT1D_SOLVER_EQUIVALENCE_REQUIRED_FOR_STRICT_MATCH",
        },
        "phase_summary": PHASE_SUMMARY,
        "matrix": decision_matrix(),
        "caveats": [
            "Equivalencia com o legado nao e sinonimo de validacao fisica.",
            "Modern-refined mode is not legacy-equivalent until domain, mesh and sampling match.",
            "The 660 s modern opening must not be automatically classified as an error.",
            "pressure_source/timing review remains blocked by geometry unless explicitly overridden.",
            "results/ outputs are diagnostic artifacts and must not be versioned.",
        ],
    }


def _write_markdown(decision: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 10.27A legacy-equivalence vs modern-refined decision",
        "",
        f"- source: `{decision['source']}`",
        f"- objective: `{decision['objective']}`",
        f"- main_decision: `{decision['main_decision']}`",
        f"- pressure_source_timing_gate: `{decision['pressure_source_timing_gate']}`",
        "",
        decision["rationale"],
        "",
        "## Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in decision["classifications"])
    lines.extend(["", "## Matrix", ""])
    header = [
        "aspect",
        "legacy_equivalence_mode",
        "modern_refined_mode",
        "current_status",
        "risk",
        "recommended_use",
        "blocking_gate",
        "next_action",
    ]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in decision["matrix"]:
        lines.append("| " + " | ".join(str(row[column]) for column in header) + " |")
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in decision["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    decision = decide(args.objective)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    _write_markdown(decision, output_md)
    return decision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Decide Phase 10.27A legacy-equivalence versus modern-refined sigmaTheta mode."
        )
    )
    parser.add_argument(
        "--objective",
        choices=[
            "modern_refined",
            "strict_legacy",
            "salt_wall_stress_runtime",
            "return_to_pressure_timing",
            "unknown",
        ],
        default="modern_refined",
    )
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    decision = run(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": decision["phase"],
                "source": decision["source"],
                "objective": decision["objective"],
                "main_decision": decision["main_decision"],
                "pressure_source_timing_gate": decision["pressure_source_timing_gate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
