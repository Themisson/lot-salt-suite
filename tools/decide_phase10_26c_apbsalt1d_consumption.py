from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


PHASE = "10.26C"

DEFAULT_CAPABILITIES: dict[str, bool] = {
    "case_metadata_available": True,
    "radial_mesh_generation": True,
    "outer_radius_configurable": True,
    "radial_elements_configurable": True,
    "mesh_ratio_configurable": False,
    "integration_order_three_available": True,
    "wall_stress_diagnostics_available": True,
    "salt_wall_stress_runtime_provider_available": False,
    "legacy_elem0_sig_2_0_sampling_available": False,
    "lot_provider_can_consume_wall_stress": False,
}


REQUIRED_GEOMETRY_FIELDS = {
    "mode",
    "outer_radius",
    "radial_elements",
    "ratio",
    "integration_order",
    "sampling",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("YAML raiz deve ser objeto")
    return loaded


def _geometry_block(case_data: dict[str, Any]) -> dict[str, Any]:
    initiation = (
        case_data.get("lot", {})
        .get("fracture", {})
        .get("initiation", {})
    )
    if not isinstance(initiation, dict):
        raise ValueError("lot.fracture.initiation ausente ou invalido")
    geometry = initiation.get("sigma_theta_runtime_geometry")
    if not isinstance(geometry, dict):
        raise ValueError("sigma_theta_runtime_geometry ausente")
    missing = sorted(REQUIRED_GEOMETRY_FIELDS - set(geometry))
    if missing:
        raise ValueError(
            "sigma_theta_runtime_geometry sem campos obrigatorios: "
            + ", ".join(missing)
        )
    return geometry


def _geometry_summary(geometry: dict[str, Any]) -> dict[str, Any]:
    outer_radius = geometry.get("outer_radius", {})
    sampling = geometry.get("sampling", {})
    return {
        "mode": geometry.get("mode"),
        "outer_radius_m": outer_radius.get("value"),
        "radial_elements": geometry.get("radial_elements"),
        "ratio": geometry.get("ratio"),
        "integration_order": geometry.get("integration_order"),
        "sampling_mode": sampling.get("mode") if isinstance(sampling, dict) else None,
        "sampling_source": sampling.get("source") if isinstance(sampling, dict) else None,
        "consumption_status": geometry.get(
            "consumption_status", "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
        ),
    }


def decide(
    case_path: Path,
    capabilities: dict[str, bool] | None = None,
) -> dict[str, Any]:
    capabilities = dict(DEFAULT_CAPABILITIES if capabilities is None else capabilities)
    geometry = _geometry_summary(_geometry_block(_load_yaml(case_path)))

    missing_capabilities: list[str] = []
    if not capabilities.get("radial_mesh_generation", False):
        missing_capabilities.append("radial_mesh_generation")
    if not capabilities.get("outer_radius_configurable", False):
        missing_capabilities.append("outer_radius_configurable")
    if not capabilities.get("radial_elements_configurable", False):
        missing_capabilities.append("radial_elements_configurable")
    if not capabilities.get("mesh_ratio_configurable", False):
        missing_capabilities.append("mesh_ratio_configurable")
    if not capabilities.get("integration_order_three_available", False):
        missing_capabilities.append("integration_order_three_available")
    if not capabilities.get("wall_stress_diagnostics_available", False):
        missing_capabilities.append("wall_stress_diagnostics_available")
    if not capabilities.get("salt_wall_stress_runtime_provider_available", False):
        missing_capabilities.append("salt_wall_stress_runtime_provider_available")
    if not capabilities.get("legacy_elem0_sig_2_0_sampling_available", False):
        missing_capabilities.append("legacy_elem0_sig_2_0_sampling_available")
    if not capabilities.get("lot_provider_can_consume_wall_stress", False):
        missing_capabilities.append("lot_provider_can_consume_wall_stress")

    risk_flags = [
        "PRESSURE_SOURCE_TIMING_REMAINS_BLOCKED_BY_GEOMETRY",
        "NO_PHYSICAL_VALIDATION",
        "NO_DEFAULT_RUNTIME_CHANGE",
    ]

    if not capabilities.get("radial_mesh_generation", False):
        status = "APBSALT1D_REAL_CONSUMPTION_REQUIRES_RADIAL_SOLVER"
        next_phase = "NEXT_PHASE_KEEP_METADATA_ONLY_AND_DOCUMENT_NON_EQUIVALENCE"
        risk_flags.append("RADIAL_SOLVER_MISSING")
    elif (
        capabilities.get("radial_mesh_generation", False)
        and capabilities.get("outer_radius_configurable", False)
        and capabilities.get("radial_elements_configurable", False)
        and capabilities.get("mesh_ratio_configurable", False)
        and capabilities.get("integration_order_three_available", False)
        and capabilities.get("wall_stress_diagnostics_available", False)
        and capabilities.get("salt_wall_stress_runtime_provider_available", False)
        and capabilities.get("legacy_elem0_sig_2_0_sampling_available", False)
        and capabilities.get("lot_provider_can_consume_wall_stress", False)
    ):
        status = "APBSALT1D_REAL_CONSUMPTION_READY"
        next_phase = "NEXT_PHASE_IMPLEMENT_APBSALT1D_SAMPLER"
        risk_flags = ["IMPLEMENTATION_STILL_OPT_IN_ONLY", "NO_DEFAULT_RUNTIME_CHANGE"]
    elif not capabilities.get("wall_stress_diagnostics_available", False):
        status = "APBSALT1D_REAL_CONSUMPTION_REQUIRES_SALT_WALL_STRESS_RUNTIME"
        next_phase = "NEXT_PHASE_IMPLEMENT_SALT_WALL_STRESS_RUNTIME"
        risk_flags.append("SALT_WALL_STRESS_RUNTIME_MISSING")
    else:
        status = "APBSALT1D_METADATA_ONLY_CONFIRMED"
        next_phase = "NEXT_PHASE_IMPLEMENT_SAMPLING_BRIDGE"
        risk_flags.extend(
            [
                "MESH_RATIO_NOT_CONFIGURABLE",
                "LEGACY_SAMPLING_POINT_NOT_AVAILABLE",
                "LOT_PROVIDER_NOT_CONNECTED_TO_WALL_STRESS",
            ]
        )

    dependency_audit = {
        "would_couple_lot_to_coupling": True,
        "would_couple_lot_to_external_saltcreep": False,
        "requires_new_radial_solver": not capabilities.get("radial_mesh_generation", False),
        "requires_sampling_bridge": "legacy_elem0_sig_2_0_sampling_available"
        in missing_capabilities
        or "lot_provider_can_consume_wall_stress" in missing_capabilities,
        "requires_apbsalt1d_port": False,
        "circular_dependency_risk": True,
    }

    capability_rows = [
        {
            "capability": "radial_mesh_generation",
            "exists": capabilities.get("radial_mesh_generation", False),
            "location": "src/salt/SaltCreepTimeBridge.cpp::build_mesh_L3",
            "observation": "Modern bridge can build an L3 radial mesh.",
            "can_consume_apbsalt1d_metadata": True,
        },
        {
            "capability": "outer_radius_m",
            "exists": capabilities.get("outer_radius_configurable", False),
            "location": "SaltCreepTimeBridgeConfig / LotSaltBridgeConfigOptions",
            "observation": "Outer radius is configurable in bridge options.",
            "can_consume_apbsalt1d_metadata": True,
        },
        {
            "capability": "radial_elements",
            "exists": capabilities.get("radial_elements_configurable", False),
            "location": "SaltCreepTimeBridgeConfig / LotSaltBridgeConfigOptions",
            "observation": "Radial element count is configurable.",
            "can_consume_apbsalt1d_metadata": True,
        },
        {
            "capability": "ratio",
            "exists": capabilities.get("mesh_ratio_configurable", False),
            "location": "not implemented in modern bridge options",
            "observation": "APBSalt1D ratio=10 is not consumed by build_mesh_L3.",
            "can_consume_apbsalt1d_metadata": False,
        },
        {
            "capability": "integration_order",
            "exists": capabilities.get("integration_order_three_available", False),
            "location": "AxisymL3",
            "observation": "Three-point L3 integration exists but is not a YAML-selected option.",
            "can_consume_apbsalt1d_metadata": True,
        },
        {
            "capability": "legacy_elem0_sig_2_0_sampling",
            "exists": capabilities.get("legacy_elem0_sig_2_0_sampling_available", False),
            "location": "not implemented; current StressSampler samples wall/minimum radius",
            "observation": "No API maps legacy elem0/sig(2,0) to modern samples.",
            "can_consume_apbsalt1d_metadata": False,
        },
        {
            "capability": "SigmaThetaProvider wall-stress runtime",
            "exists": capabilities.get("lot_provider_can_consume_wall_stress", False),
            "location": "include/lot/SigmaThetaProvider.hpp supports provider contract only",
            "observation": "Current runtime provider is a time-series provider.",
            "can_consume_apbsalt1d_metadata": False,
        },
    ]

    return {
        "phase": PHASE,
        "case": str(case_path),
        "apbsalt1d_consumption_status": status,
        "next_phase_recommendation": next_phase,
        "geometry": geometry,
        "capabilities": capability_rows,
        "missing_capabilities": missing_capabilities,
        "dependency_audit": dependency_audit,
        "risk_flags": risk_flags,
        "pressure_source_timing_gate": (
            "BLOCKED_UNTIL_APBSALT1D_GEOMETRY_IS_CONSUMED_OR_REJECTED"
        ),
        "metadata_is_consumed": status == "APBSALT1D_REAL_CONSUMPTION_READY",
    }


def write_markdown(decision: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 10.26C APBSalt1D Consumption Decision",
        "",
        f"- Status: `{decision['apbsalt1d_consumption_status']}`",
        f"- Next phase: `{decision['next_phase_recommendation']}`",
        f"- Pressure/timing gate: `{decision['pressure_source_timing_gate']}`",
        "",
        "## Missing Capabilities",
        "",
    ]
    for item in decision["missing_capabilities"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Geometry", ""])
    for key, value in decision["geometry"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Caveat", ""])
    lines.append("Diagnostic decision only; no physical validation is claimed.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    decision = decide(args.case)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    write_markdown(decision, args.output_md)
    return decision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decide Phase 10.26C APBSalt1D sigma-theta metadata consumption path."
    )
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    decision = run(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": decision["phase"],
                "apbsalt1d_consumption_status": decision[
                    "apbsalt1d_consumption_status"
                ],
                "next_phase_recommendation": decision["next_phase_recommendation"],
                "pressure_source_timing_gate": decision["pressure_source_timing_gate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
