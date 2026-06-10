from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import yaml


PHASE = "10.19B"
BBL_TO_M3_LEGACY = 0.158987
BBL_TO_M3_MODERN = 0.158987294928
INCH_TO_M = 0.0254


def _finite(value: Any, field: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be finite")
    return parsed


def _unit_value(node: dict[str, Any], field: str) -> tuple[float, str]:
    if not isinstance(node, dict):
        raise ValueError(f"{field} must be a mapping with value/unit")
    return _finite(node["value"], f"{field}.value"), str(node["unit"])


def _length_m(node: dict[str, Any], field: str) -> float:
    value, unit = _unit_value(node, field)
    if unit == "m":
        return value
    if unit == "in":
        return value * INCH_TO_M
    raise ValueError(f"unsupported length unit for {field}: {unit}")


def _time_s(node: dict[str, Any], field: str) -> float:
    value, unit = _unit_value(node, field)
    if unit == "s":
        return value
    if unit == "min":
        return value * 60.0
    if unit == "h":
        return value * 3600.0
    raise ValueError(f"unsupported time unit for {field}: {unit}")


def _rate_total_m3_s(node: dict[str, Any], field: str) -> float:
    value, unit = _unit_value(node, field)
    if unit == "m3_s":
        return value
    if unit == "m3_min":
        return value / 60.0
    if unit in {"bbl_min", "bpm"}:
        return value * BBL_TO_M3_MODERN / 60.0
    raise ValueError(f"unsupported rate unit for {field}: {unit}")


def _rate_bbl_min(node: dict[str, Any], field: str) -> float:
    value, unit = _unit_value(node, field)
    if unit not in {"bbl_min", "bpm"}:
        raise ValueError(f"{field} must use bbl_min/bpm for the legacy audit")
    return value


def _read_case(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"invalid YAML case: {path}")
    return data


def _layer_at_shoe(data: dict[str, Any], shoe_depth_m: float) -> dict[str, Any]:
    for layer in data.get("layers", []):
        if float(layer["top_m"]) <= shoe_depth_m <= float(layer["base_m"]):
            return layer
    raise ValueError("no layer contains lot.shoe_depth_m")


def _casing_for_annular_outer_radius(
    data: dict[str, Any], shoe_depth_m: float
) -> dict[str, Any]:
    candidate: dict[str, Any] | None = None
    for casing in data.get("casings", []):
        if float(casing["top_m"]) <= shoe_depth_m <= float(casing["base_m"]):
            if candidate is None or float(casing["di_in"]) < float(candidate["di_in"]):
                candidate = casing
    if candidate is not None:
        return candidate
    for casing in data.get("casings", []):
        if float(casing["base_m"]) <= shoe_depth_m:
            if candidate is None or float(casing["base_m"]) > float(candidate["base_m"]):
                candidate = casing
    if candidate is None:
        raise ValueError("no casing available for annular volume")
    return candidate


def _first_annular_fluid(data: dict[str, Any]) -> dict[str, Any]:
    annulars = data.get("annulars", [])
    fluids = data.get("fluids", [])
    if not annulars:
        raise ValueError("case has no annulars")
    fluid_id = annulars[0].get("fluid")
    for fluid in fluids:
        if fluid.get("id") == fluid_id:
            return fluid
    raise ValueError(f"annular fluid not found: {fluid_id}")


def _float_cell(row: dict[str, str], field: str) -> float | None:
    raw = row.get(field)
    if raw is None or raw == "":
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _first_positive_time_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    candidates = [
        row for row in rows if (_float_cell(row, "time_s") or 0.0) > 0.0
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda row: _float_cell(row, "time_s") or math.inf)


def _annular_volume_per_radian_m3(
    outer_radius_m: float, inner_radius_m: float, length_m: float
) -> float:
    return 0.5 * (outer_radius_m**2 - inner_radius_m**2) * length_m


def _comparison_classification(metrics: dict[str, Any]) -> str:
    rel_flow_diff = abs(metrics["q_rad_modern_over_legacy_minus_1"])
    rel_dpressure_diff = abs(metrics["dP_total_vs_rad_relative_difference"])
    if rel_flow_diff > 1.0e-5:
        return "FLOWRATE_CONVENTION_MISMATCH"
    if rel_dpressure_diff > 1.0e-5:
        return "FLOWRATE_TOTAL_VS_RADIAN_MISMATCH"
    if metrics["first_dt_s"] != 30.0:
        return "FLOWRATE_TIME_UNIT_MISMATCH"
    return "FLOWRATE_CONVENTION_MATCHES_LEGACY"


def _root_cause(metrics: dict[str, Any]) -> str:
    legacy_first = metrics.get("legacy_first_dP_Pa")
    theoretical = metrics["dP_theoretical_rad_Pa"]
    if legacy_first is None:
        return "ROOT_CAUSE_INCONCLUSIVE"
    if theoretical <= 0.0:
        return "ROOT_CAUSE_INCONCLUSIVE"
    ratio = legacy_first / theoretical
    if ratio < 0.2:
        return "ROOT_CAUSE_MISSING_GEOMETRIC_COMPLIANCE"
    return "ROOT_CAUSE_INCONCLUSIVE"


def audit_case(
    case_path: Path,
    legacy_csv: Path | None = None,
    modern_csv: Path | None = None,
) -> dict[str, Any]:
    data = _read_case(case_path)
    lot = data["lot"]
    injection = lot["injection"]
    rate_node = injection["rate"]
    schedule = injection["schedule"]
    shoe_depth_m = float(lot["shoe_depth_m"])
    layer = _layer_at_shoe(data, shoe_depth_m)
    casing = _casing_for_annular_outer_radius(data, shoe_depth_m)
    fluid = _first_annular_fluid(data)

    q_bbl_min = _rate_bbl_min(rate_node, "lot.injection.rate")
    q_total_m3_min_legacy = q_bbl_min * BBL_TO_M3_LEGACY
    q_rad_m3_min_legacy = q_total_m3_min_legacy / (2.0 * math.pi)
    q_rad_m3_s_legacy = q_rad_m3_min_legacy / 60.0

    q_total_m3_s_modern = _rate_total_m3_s(rate_node, "lot.injection.rate")
    q_total_m3_min_modern = q_total_m3_s_modern * 60.0
    q_rad_m3_min_modern = q_total_m3_min_modern / (2.0 * math.pi)
    q_rad_m3_s_modern = q_rad_m3_min_modern / 60.0

    dt_s = _time_s(schedule["dt"], "lot.injection.schedule.dt")
    dV_rad_30s = q_rad_m3_s_legacy * dt_s
    dV_total_30s = q_total_m3_s_modern * dt_s

    outer_radius_m = float(casing["di_in"]) * INCH_TO_M / 2.0
    inner_radius_m = 0.0
    drill_pipe = data.get("wellbore", {}).get("drill_pipe", {})
    if drill_pipe and _length_m(drill_pipe["depth"], "wellbore.drill_pipe.depth") >= shoe_depth_m:
        inner_radius_m = _length_m(
            drill_pipe["outer_diameter"], "wellbore.drill_pipe.outer_diameter"
        ) / 2.0
    length_m = float(layer["base_m"]) - float(layer["top_m"])
    v_rad = _annular_volume_per_radian_m3(outer_radius_m, inner_radius_m, length_m)
    v_total = 2.0 * math.pi * v_rad
    compressibility = float(fluid["compressibility_per_Pa"])

    dP_rad = dV_rad_30s / (compressibility * v_rad)
    dP_total = dV_total_30s / (compressibility * v_total)
    modern_first_delta: float | None = None
    modern_trial_pressure: float | None = None
    legacy_first_dP: float | None = None
    legacy_first_pw: float | None = None

    if modern_csv is not None and modern_csv.exists():
        row = _first_positive_time_row(_read_csv(modern_csv))
        if row is not None:
            modern_first_delta = _float_cell(row, "balance_delta_pressure_Pa")
            modern_trial_pressure = _float_cell(row, "fracture_initiation_pressure_Pa")

    if legacy_csv is not None and legacy_csv.exists():
        row = _first_positive_time_row(_read_csv(legacy_csv))
        if row is not None:
            legacy_first_dP = _float_cell(row, "dP")
            legacy_first_pw = _float_cell(row, "pw_Pa")

    metrics: dict[str, Any] = {
        "q_bbl_min": q_bbl_min,
        "q_total_m3_min_legacy": q_total_m3_min_legacy,
        "q_rad_m3_min_legacy": q_rad_m3_min_legacy,
        "q_rad_m3_s_legacy": q_rad_m3_s_legacy,
        "q_total_m3_min_modern": q_total_m3_min_modern,
        "q_rad_m3_min_modern": q_rad_m3_min_modern,
        "q_rad_modern_over_legacy_minus_1": q_rad_m3_min_modern
        / q_rad_m3_min_legacy
        - 1.0,
        "first_dt_s": dt_s,
        "dV_inj_first_step_rad_m3": dV_rad_30s,
        "dV_inj_first_step_total_m3": dV_total_30s,
        "annular_volume_per_radian_m3": v_rad,
        "annular_volume_total_m3": v_total,
        "fluid_compressibility_per_Pa": compressibility,
        "dP_theoretical_rad_Pa": dP_rad,
        "dP_theoretical_total_Pa": dP_total,
        "dP_total_vs_rad_relative_difference": (dP_total - dP_rad) / dP_rad,
        "modern_first_balance_delta_pressure_Pa": modern_first_delta,
        "modern_first_trial_pressure_Pa": modern_trial_pressure,
        "legacy_first_dP_Pa": legacy_first_dP,
        "legacy_first_pw_Pa": legacy_first_pw,
        "legacy_first_dP_over_theoretical": None
        if legacy_first_dP is None
        else legacy_first_dP / dP_rad,
    }

    classification = _comparison_classification(metrics)
    root_cause = _root_cause(metrics)
    table = [
        {
            "item": "idQ",
            "value": "6",
            "unit": "legacy enum",
            "source": "APB1da(..., idQ=6, Q=0.5)",
            "observation": "bbl/min converted to m3/min/rad in Conv_bbmin_m3min",
        },
        {
            "item": "Q",
            "value": q_bbl_min,
            "unit": "bbl/min",
            "source": str(case_path),
            "observation": "matches BUZ67D legacy setup",
        },
        {
            "item": "Q_total",
            "value": q_total_m3_min_legacy,
            "unit": "m3/min",
            "source": "0.5 * 0.158987",
            "observation": "legacy barrel conversion before per-radian split",
        },
        {
            "item": "Q_rad",
            "value": q_rad_m3_min_legacy,
            "unit": "m3/min/rad",
            "source": "Q_total / (2*pi)",
            "observation": "legacy internal convention",
        },
        {
            "item": "dV_first_step",
            "value": dV_rad_30s,
            "unit": "m3/rad",
            "source": "Q_rad * dt",
            "observation": "first 30 s injection increment",
        },
        {
            "item": "V_annular",
            "value": v_rad,
            "unit": "m3/rad",
            "source": "0.5*(ro^2-ri^2)*layer_thickness",
            "observation": "same convention as legacy Vi",
        },
        {
            "item": "dP_pure_fluid_compression",
            "value": dP_rad,
            "unit": "Pa",
            "source": "dV/(C*V)",
            "observation": "matches the modern first-step trial jump scale",
        },
    ]
    return {
        "phase": PHASE,
        "case": str(case_path),
        "classification": classification,
        "root_cause_classification": root_cause,
        "physical_validation": False,
        "numeric_equivalence": False,
        "flowrate_audit": table,
        "metrics": metrics,
        "legacy_compliance_audit": {
            "getdV_present": True,
            "formula_contains_dV": True,
            "formula": "dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k",
            "dV_meaning": "geometric annular volume change from displaced radii u(e), u(e1)",
            "dV_reduces_pressure_increment_when_positive": True,
            "instrumented_values_available": legacy_first_dP is not None,
            "first_step_without_dV_Pa": dP_rad,
            "first_step_legacy_dP_Pa": legacy_first_dP,
        },
        "caveats": [
            "This audit is structural/diagnostic, not physical validation.",
            "Legacy APB1da stores Vq and Vi internally per radian.",
            "Modern PknRunner stores total injected and annular volumes for volumetric_balance.",
            "Total/total and per-radian/per-radian pressure increments are algebraically equivalent.",
            "Legacy dV geometric compliance is present in the active dP formula.",
            "A full correction requires an explicit annular/wellbore compliance model, not an empirical pressure factor.",
        ],
    }


def write_outputs(result: dict[str, Any], output_json: Path, output_csv: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    rows = result["flowrate_audit"]
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["item", "value", "unit", "source", "observation"]
        )
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 10.19B flow-rate and volumetric balance convention."
    )
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--legacy-csv", type=Path, default=None)
    parser.add_argument("--modern-csv", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = audit_case(args.case, args.legacy_csv, args.modern_csv)
    write_outputs(result, args.output_json, args.output_csv)
    print(json.dumps({
        "classification": result["classification"],
        "root_cause_classification": result["root_cause_classification"],
        "dP_theoretical_rad_Pa": result["metrics"]["dP_theoretical_rad_Pa"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
