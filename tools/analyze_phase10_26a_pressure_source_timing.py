from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


LEGACY_OPENING_TIME_S = 510.0
PHASE = "10.26A"


LEGACY_GEOMETRY_AUDIT = {
    "source": "legance/LOT_Tese/include/apb/apb_salt_1d.h + src/apb/apb_salt_1d.cpp",
    "outer_diam_m": 16.0,
    "outer_radius_m": 8.0,
    "inner_radius_source": "(diam_in / 2) * 0.0254",
    "radial_elements": 15,
    "mesh_ratio": 10.0,
    "integration_order": 3,
    "mesh_rule": "geometric progression with q = ratio ** (1 / (nelem - 1))",
    "sigma_theta_source": "APBSalt1D::getSigmaTheta() -> mdl->getElem(0)->getSigmaTheta()",
    "sigma_theta_sampling": "Element 0, local Gauss point 0, sig(2, 0)",
}


MODERN_GEOMETRY_AUDIT = {
    "source": "include/salt/SaltCreepTimeBridge.hpp + src/coupling/LotSaltBridgeConfigBuilder.cpp",
    "default_outer_radius_m": 1.556,
    "builder_default_outer_radius_m": 1.556,
    "default_radial_elements": 40,
    "builder_default_radial_elements": 40,
    "integration_order": 3,
    "mesh_builder": "build_mesh_L3(inner_radius_m, outer_radius_m, radial_elements, height_m)",
    "wall_stress_sampling": "StressSampler::sample_wall_gauss_points selects Gauss point(s) with minimum r_m",
    "runtime_timeseries_source": "sigma_theta_time_series provider uses tabulated values, not SaltWallStressDiagnostics mesh",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if "`n" in text and "\n" not in text:
        text = text.replace("`n", "\n")
    return [dict(row) for row in csv.DictReader(text.splitlines())]


def _float(value: str | float | int | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _flag(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _time_sorted_unique(rows: list[dict[str, str]], value_field: str) -> list[tuple[float, float]]:
    by_time: dict[float, float] = {}
    for row in rows:
        time_s = _float(row.get("time_s"))
        value = _float(row.get(value_field))
        if time_s is not None and value is not None and value > 0.0:
            by_time[time_s] = value
    return sorted(by_time.items())


def _interp(points: list[tuple[float, float]], time_s: float) -> float | None:
    if not points:
        return None
    if time_s <= points[0][0]:
        return points[0][1]
    if time_s >= points[-1][0]:
        return points[-1][1]
    for (t0, y0), (t1, y1) in zip(points, points[1:]):
        if t0 <= time_s <= t1:
            if t1 == t0:
                return y1
            f = (time_s - t0) / (t1 - t0)
            return y0 + f * (y1 - y0)
    return None


def _legacy_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening_rows = [row for row in rows if _flag(row.get("opened"))]
    first_open = min(opening_rows, key=lambda row: _float(row.get("time_s")) or math.inf)
    sink_rows = [row for row in rows if _flag(row.get("sink_positive"))]
    first_sink = min(sink_rows, key=lambda row: _float(row.get("time_s")) or math.inf) if sink_rows else None
    return {
        "trace_rows": len(rows),
        "first_opened_time_s": _float(first_open.get("time_s")),
        "first_pw_Pa": _float(first_open.get("pw_Pa")),
        "first_sigmaTheta_Pa": _float(first_open.get("sigmaTheta_Pa")),
        "first_margin_Pa": _float(first_open.get("margin_Pa")),
        "first_sink_positive_time_s": _float(first_sink.get("time_s")) if first_sink else None,
    }


def _modern_fields(rows: list[dict[str, str]]) -> dict[str, bool]:
    fields = set(rows[0]) if rows else set()
    wanted = [
        "time_s",
        "wellbore_pressure_Pa",
        "wellbore_pressure_before_Pa",
        "wellbore_pressure_trial_Pa",
        "wellbore_pressure_after_Pa",
        "delta_pressure_Pa",
        "sigma_theta_compression_positive_Pa",
        "fracture_initiation_sigma_theta_Pa",
        "sigma_theta_margin_Pa",
        "fracture_initiation_margin_Pa",
        "fracture_initiated",
        "fracture_started_this_step",
        "fracture_initiation_time_s",
        "sink_active_this_step",
        "sink_deferred_this_step",
    ]
    return {field: field in fields for field in wanted}


def _modern_step_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    previous_pressure: float | None = None
    previous_time: float | None = None
    for row in rows:
        time_s = _float(row.get("time_s"))
        if time_s is None:
            continue
        pressure = _float(row.get("wellbore_pressure_Pa"))
        dt = time_s - previous_time if previous_time is not None else 0.0
        parsed.append(
            {
                "raw": row,
                "time_s": time_s,
                "dt_s": dt if dt > 0.0 else 0.0,
                "wellbore_pressure_Pa": pressure,
                "wellbore_pressure_before_derived_Pa": previous_pressure,
                "wellbore_pressure_after_derived_Pa": pressure,
            }
        )
        if pressure is not None:
            previous_pressure = pressure
        previous_time = time_s
    return parsed


def _pressure_value(step: dict[str, Any], name: str) -> tuple[float | None, str]:
    row = step["raw"]
    if name == "wellbore_pressure_before_Pa":
        explicit = _float(row.get(name))
        if explicit is not None:
            return explicit, "explicit"
        return step.get("wellbore_pressure_before_derived_Pa"), "derived_previous_wellbore_pressure_Pa"
    if name == "wellbore_pressure_after_Pa":
        explicit = _float(row.get(name))
        if explicit is not None:
            return explicit, "explicit"
        return step.get("wellbore_pressure_after_derived_Pa"), "derived_current_wellbore_pressure_Pa"
    explicit = _float(row.get(name))
    if explicit is not None:
        return explicit, "explicit"
    return None, "missing"


def _sigma_value(
    points: list[tuple[float, float]], step: dict[str, Any], mode: str
) -> tuple[float | None, str, float | None]:
    time_s = step["time_s"]
    dt_s = step["dt_s"] or 0.0
    if mode in {"sigmaTheta(time_i)", "sigmaTheta interpolated at pressure time"}:
        lookup = time_s
    elif mode == "sigmaTheta(time_i + dt)":
        lookup = time_s + dt_s
    elif mode == "sigmaTheta previous step":
        lookup = time_s - dt_s if dt_s > 0.0 else time_s
    else:
        return None, "unknown_mode", None
    return _interp(points, lookup), "legacy_trace_interpolated", lookup


def _record_time(step: dict[str, Any], mode: str) -> float:
    time_s = step["time_s"]
    dt_s = step["dt_s"] or 0.0
    if mode == "record_opening_at_step_start":
        return time_s - dt_s
    if mode == "record_opening_at_next_step":
        return time_s + dt_s
    return time_s


def _classify_opening(error_s: float | None) -> str:
    if error_s is None:
        return "INSUFFICIENT_FIELDS"
    if abs(error_s) <= 1.0e-6:
        return "MATCHES_LEGACY_OPENING"
    if abs(error_s) <= 30.0:
        return "CLOSE_TO_LEGACY_OPENING"
    if error_s < -30.0:
        return "OPENING_TOO_EARLY"
    return "OPENING_TOO_LATE"


def _candidate_rows(
    modern_steps: list[dict[str, Any]], sigma_points: list[tuple[float, float]]
) -> list[dict[str, Any]]:
    pressure_names = [
        "wellbore_pressure_before_Pa",
        "wellbore_pressure_trial_Pa",
        "wellbore_pressure_after_Pa",
        "wellbore_pressure_Pa",
    ]
    sigma_modes = [
        "sigmaTheta(time_i)",
        "sigmaTheta(time_i + dt)",
        "sigmaTheta interpolated at pressure time",
        "sigmaTheta previous step",
    ]
    record_modes = [
        "record_opening_at_step_start",
        "record_opening_at_step_end",
        "record_opening_at_next_step",
    ]
    candidates: list[dict[str, Any]] = []
    for pressure_name in pressure_names:
        for sigma_mode in sigma_modes:
            first: dict[str, Any] | None = None
            pressure_status = "missing"
            sigma_status = "missing"
            for step in modern_steps:
                pressure, pressure_status = _pressure_value(step, pressure_name)
                sigma, sigma_status, sigma_lookup_time_s = _sigma_value(sigma_points, step, sigma_mode)
                if pressure is None or sigma is None:
                    continue
                margin = pressure - sigma
                if margin > 0.0:
                    first = {
                        "pressure_Pa": pressure,
                        "sigmaTheta_Pa": sigma,
                        "margin_Pa": margin,
                        "time_s": step["time_s"],
                        "step_time_s": step["time_s"],
                        "dt_s": step["dt_s"],
                        "sigma_lookup_time_s": sigma_lookup_time_s,
                        "pressure_status": pressure_status,
                        "sigma_status": sigma_status,
                    }
                    break
            for record_mode in record_modes:
                if first is None:
                    row = {
                        "pressure_source": pressure_name,
                        "pressure_status": pressure_status,
                        "sigmaTheta_timing": sigma_mode,
                        "sigma_status": sigma_status,
                        "record_timing": record_mode,
                        "predicted_opening_time_s": None,
                        "opening_time_error_s": None,
                        "pressure_at_predicted_opening_Pa": None,
                        "sigmaTheta_at_predicted_opening_Pa": None,
                        "margin_at_predicted_opening_Pa": None,
                        "classification": "INSUFFICIENT_FIELDS",
                    }
                else:
                    predicted = _record_time(first, record_mode)
                    error = predicted - LEGACY_OPENING_TIME_S
                    row = {
                        "pressure_source": pressure_name,
                        "pressure_status": first["pressure_status"],
                        "sigmaTheta_timing": sigma_mode,
                        "sigma_status": first["sigma_status"],
                        "record_timing": record_mode,
                        "candidate_step_time_s": first["step_time_s"],
                        "sigma_lookup_time_s": first["sigma_lookup_time_s"],
                        "predicted_opening_time_s": predicted,
                        "opening_time_error_s": error,
                        "pressure_at_predicted_opening_Pa": first["pressure_Pa"],
                        "sigmaTheta_at_predicted_opening_Pa": first["sigmaTheta_Pa"],
                        "margin_at_predicted_opening_Pa": first["margin_Pa"],
                        "classification": _classify_opening(error),
                    }
                candidates.append(row)
    return candidates


def _best_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [row for row in candidates if row.get("opening_time_error_s") is not None]
    if not valid:
        return None
    return min(valid, key=lambda row: abs(float(row["opening_time_error_s"])))


def _cause_and_gate(
    fields: dict[str, bool], candidates: list[dict[str, Any]], best: dict[str, Any] | None
) -> tuple[str, str]:
    missing_pressure = not (
        fields.get("wellbore_pressure_before_Pa")
        and fields.get("wellbore_pressure_trial_Pa")
        and fields.get("wellbore_pressure_after_Pa")
    )
    missing_sigma = not (
        fields.get("sigma_theta_compression_positive_Pa")
        or fields.get("fracture_initiation_sigma_theta_Pa")
    )
    if best is None:
        if missing_pressure:
            return "MISSING_PRESSURE_TRACE_FIELDS", "MODERN_TRACE_EXPORT_REQUIRED"
        if missing_sigma:
            return "MISSING_SIGMATHETA_TRACE_FIELDS", "MODERN_TRACE_EXPORT_REQUIRED"
        return "TIMING_ANALYSIS_INCONCLUSIVE", "NO_FIX_UNTIL_RUNTIME_TRACE_COMPLETE"
    if best["classification"] in {"MATCHES_LEGACY_OPENING", "CLOSE_TO_LEGACY_OPENING"}:
        if "previous" in str(best.get("pressure_status", "")):
            return "PRESSURE_SOURCE_TIMING_MISMATCH", "PRESSURE_SOURCE_TIMING_FIX_READY"
        if "previous" in str(best.get("sigmaTheta_timing", "")):
            return "SIGMATHETA_LOOKUP_TIME_MISMATCH", "SIGMATHETA_LOOKUP_TIMING_FIX_READY"
        if best.get("record_timing") != "record_opening_at_step_end":
            return "OPENING_RECORD_TIME_MISMATCH", "OPENING_RECORD_TIMING_FIX_READY"
    if missing_pressure:
        return "MISSING_PRESSURE_TRACE_FIELDS", "MODERN_TRACE_EXPORT_REQUIRED"
    return "NO_COMBINATION_MATCHES_LEGACY", "NO_FIX_UNTIL_RUNTIME_TRACE_COMPLETE"


def _geometry_audit() -> dict[str, Any]:
    outer_radius_matches = (
        MODERN_GEOMETRY_AUDIT["builder_default_outer_radius_m"]
        == LEGACY_GEOMETRY_AUDIT["outer_radius_m"]
    )
    radial_elements_match = (
        MODERN_GEOMETRY_AUDIT["builder_default_radial_elements"]
        == LEGACY_GEOMETRY_AUDIT["radial_elements"]
    )
    integration_order_matches = (
        MODERN_GEOMETRY_AUDIT["integration_order"]
        == LEGACY_GEOMETRY_AUDIT["integration_order"]
    )
    sampling_is_equivalent = False
    classifications = [
        "SIGMATHETA_MESH_OR_DOMAIN_MISMATCH",
        "SIGMATHETA_SAMPLING_POINT_MISMATCH",
        "MODERN_MESH_NOT_LEGACY_EQUIVALENT",
        "LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING",
        "TIMING_ANALYSIS_INCONCLUSIVE",
    ]
    if not outer_radius_matches or not radial_elements_match:
        classifications.append("MODERN_REFINED_MESH_POTENTIALLY_MORE_REALISTIC")
    return {
        "legacy_apb_salt_1d": LEGACY_GEOMETRY_AUDIT,
        "modern_bridge_defaults": MODERN_GEOMETRY_AUDIT,
        "outer_radius_matches": outer_radius_matches,
        "radial_elements_match": radial_elements_match,
        "integration_order_matches": integration_order_matches,
        "sampling_point_equivalence_confirmed": sampling_is_equivalent,
        "geometry_equivalent": (
            outer_radius_matches
            and radial_elements_match
            and integration_order_matches
            and sampling_is_equivalent
        ),
        "classifications": classifications,
        "recommended_next_phase": (
            "10.26B reproduce APBSalt1D legacy mesh/domain before changing "
            "pressure_source or timing"
        ),
        "recommended_legacy_equivalence_config": {
            "outer_radius_m": 8.0,
            "radial_elements": 15,
            "mesh_ratio": 10.0,
            "integration_order": 3,
            "sampling": "Element 0 / local Gauss point 0 equivalent",
        },
    }


def _apply_geometry_gate(
    pressure_timing_cause: str, pressure_timing_gate: str, geometry: dict[str, Any]
) -> tuple[str, str]:
    if not geometry["geometry_equivalent"]:
        return "SIGMATHETA_MESH_OR_DOMAIN_MISMATCH", "LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING"
    return pressure_timing_cause, pressure_timing_gate


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _plot_outputs(output_dir: Path, candidates: list[dict[str, Any]]) -> dict[str, bool]:
    names = [
        "pressure_source_candidates_vs_sigmaTheta.png",
        "margin_candidates_vs_time.png",
        "predicted_opening_time_by_candidate.png",
        "legacy_vs_modern_opening_timing.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}
    output_dir.mkdir(parents=True, exist_ok=True)
    valid = [row for row in candidates if row.get("predicted_opening_time_s") is not None]

    plt.figure()
    for row in valid:
        plt.scatter(row["pressure_at_predicted_opening_Pa"], row["sigmaTheta_at_predicted_opening_Pa"], s=12)
    plt.xlabel("candidate pressure Pa")
    plt.ylabel("candidate sigmaTheta Pa")
    plt.title("Phase 10.26A pressure candidates vs sigmaTheta")
    plt.savefig(output_dir / names[0], dpi=150)
    plt.close()

    plt.figure()
    for row in valid:
        plt.scatter(row["predicted_opening_time_s"], row["margin_at_predicted_opening_Pa"], s=12)
    plt.axvline(LEGACY_OPENING_TIME_S, color="black", linestyle="--")
    plt.xlabel("predicted opening time s")
    plt.ylabel("margin Pa")
    plt.title("Phase 10.26A candidate margins")
    plt.savefig(output_dir / names[1], dpi=150)
    plt.close()

    plt.figure(figsize=(8, 4))
    labels = [f"{row['pressure_source']}|{row['sigmaTheta_timing']}|{row['record_timing']}" for row in valid[:30]]
    values = [row["predicted_opening_time_s"] for row in valid[:30]]
    plt.bar(range(len(values)), values)
    plt.axhline(LEGACY_OPENING_TIME_S, color="black", linestyle="--")
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=6)
    plt.ylabel("time s")
    plt.title("Phase 10.26A predicted opening by candidate")
    plt.tight_layout()
    plt.savefig(output_dir / names[2], dpi=150)
    plt.close()

    plt.figure()
    best = _best_candidate(candidates)
    plt.bar(["legacy", "best_candidate"], [LEGACY_OPENING_TIME_S, best["predicted_opening_time_s"] if best else 0.0])
    plt.ylabel("time s")
    plt.title("Legacy vs best modern candidate")
    plt.savefig(output_dir / names[3], dpi=150)
    plt.close()
    return {name: True for name in names}


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_trace))
    modern_rows = _read_csv(Path(args.modern_csv))
    if not legacy_rows:
        raise ValueError("legacy trace has no rows")
    if not modern_rows:
        raise ValueError("modern CSV has no rows")
    legacy = _legacy_summary(legacy_rows)
    fields = _modern_fields(modern_rows)
    sigma_points = _time_sorted_unique(legacy_rows, "sigmaTheta_Pa")
    modern_steps = _modern_step_rows(modern_rows)
    candidates = _candidate_rows(modern_steps, sigma_points)
    best = _best_candidate(candidates)
    pressure_timing_cause, pressure_timing_gate = _cause_and_gate(fields, candidates, best)
    geometry = _geometry_audit()
    cause, gate = _apply_geometry_gate(pressure_timing_cause, pressure_timing_gate, geometry)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(Path(args.output_csv), candidates)
    plots = _plot_outputs(output_dir, candidates)
    summary = {
        "phase": PHASE,
        "cause": cause,
        "gate": gate,
        "pressure_source_timing_cause_before_geometry_gate": pressure_timing_cause,
        "pressure_source_timing_gate_before_geometry_gate": pressure_timing_gate,
        "geometry_audit": geometry,
        "legacy": legacy,
        "modern_fields": fields,
        "missing_modern_fields": [key for key, present in fields.items() if not present],
        "sigmaTheta_points_from_legacy_trace": len(sigma_points),
        "candidate_count": len(candidates),
        "best_candidate": best,
        "classification_counts": {
            name: sum(1 for row in candidates if row["classification"] == name)
            for name in sorted({row["classification"] for row in candidates})
        },
        "plots": plots,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "Modern CSV does not export explicit before/trial/after pressure fields.",
            "Derived pressure candidates use previous/current wellbore_pressure_Pa and must not be treated as runtime semantics.",
            "APBSalt1D legacy mesh/domain/sampling are not yet reproduced by the modern bridge defaults.",
            "Do not correct pressure_source or timing until a legacy-equivalent mesh/domain case is tested.",
            "No default LOT/PKN behavior changed.",
        ],
    }
    Path(args.output_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 10.26A sigma-theta pressure_source and timing candidates."
    )
    parser.add_argument("--legacy-trace", required=True, type=Path)
    parser.add_argument("--modern-csv", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = analyze(build_parser().parse_args(argv))
    print(json.dumps({"phase": summary["phase"], "cause": summary["cause"], "gate": summary["gate"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
