from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


PHASE = "10.21C"
DEFAULT_ALPHA_1_C = 8.0e-4
DEFAULT_COMPRESSIBILITY_1_PA = 6.40e-10
DEFAULT_PROF_TESTE_M = 4374.0
DEFAULT_ANNULAR_VOLUME_M3_RAD = 0.17842518895535997
DEFAULT_INJECTION_DURATION_MIN = 12.5
DEFAULT_LEGACY_OPEN_TIME_S = 510.0
DEFAULT_THERMAL_LIMIT_MIN = 0.25
C_GEOM_CONSTANT_10_19C = 1.8571966938610005e-8
C_EFF_CONSTANT_10_19C = 1.9211966938610006e-8


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(value: str | float | int | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _require_finite(value: float, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _require_positive(value: float, name: str) -> float:
    _require_finite(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")
    return value


def _require_non_negative(value: float, name: str) -> float:
    _require_finite(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return value


def parse_vector_literal(source: str, name: str) -> list[float]:
    match = re.search(rf"\b{name}\s*<<\s*(.*?);", source, flags=re.S)
    if not match:
        raise ValueError(f"could not find vector {name}")
    values = []
    for token in match.group(1).replace("\n", " ").split(","):
        stripped = token.strip()
        if stripped:
            values.append(float(stripped))
    if not values:
        raise ValueError(f"vector {name} is empty")
    return values


def parse_prof_teste_m(source: str, fallback: float = DEFAULT_PROF_TESTE_M) -> float:
    match = re.search(r"\bprofTeste\s*=\s*([0-9.eE+-]+)", source)
    return float(match.group(1)) if match else fallback


def parse_fluid_alpha_k(source: str) -> tuple[float, float]:
    match = re.search(
        r"vfluids\[0\]->setPFluid\(\s*[0-9.eE+-]+\s*,\s*([0-9.eE+-]+)\s*,\s*([0-9.eE+-]+)\s*\)",
        source,
    )
    if not match:
        return DEFAULT_ALPHA_1_C, DEFAULT_COMPRESSIBILITY_1_PA
    return float(match.group(1)), float(match.group(2))


def linear_interpolate(depth_m: float, depths_m: list[float], values: list[float]) -> float:
    if len(depths_m) != len(values) or len(depths_m) < 2:
        raise ValueError("depth and value vectors must have the same length >= 2")
    for left, right, v_left, v_right in zip(
        depths_m[:-1], depths_m[1:], values[:-1], values[1:]
    ):
        if left <= depth_m <= right:
            fraction = (depth_m - left) / (right - left)
            return v_left + fraction * (v_right - v_left)
    raise ValueError(f"depth {depth_m} m is outside the profile range")


def build_thermal_profile(legacy_case: Path, prof_teste_m: float | None = None) -> dict[str, Any]:
    source = legacy_case.read_text(encoding="utf-8", errors="replace")
    depth_m = prof_teste_m if prof_teste_m is not None else parse_prof_teste_m(source)
    depths = parse_vector_literal(source, "dA")
    initial = parse_vector_literal(source, "A0")
    final = parse_vector_literal(source, "Af")
    alpha, compressibility = parse_fluid_alpha_k(source)
    t_initial = linear_interpolate(depth_m, depths, initial)
    t_final = linear_interpolate(depth_m, depths, final)
    return {
        "depth_m": depth_m,
        "profile_source": "linear_interpolation_dA_A0_Af_annular_A",
        "T_initial_degC": t_initial,
        "T_final_degC": t_final,
        "DTmax_degC": t_final - t_initial,
        "alpha_1_C": alpha,
        "compressibility_1_Pa": compressibility,
        "thermal_limit_min": DEFAULT_THERMAL_LIMIT_MIN,
    }


def legacy_thermal_increment_degC(
    time_min: float,
    dtmax_degC: float,
    thermal_limit_min: float = DEFAULT_THERMAL_LIMIT_MIN,
    tac_min: float = 0.0,
) -> float:
    _require_non_negative(time_min, "time_min")
    _require_non_negative(dtmax_degC, "dtmax_degC")
    _require_positive(thermal_limit_min, "thermal_limit_min")
    if time_min <= tac_min:
        return 0.0
    active = time_min - tac_min
    return dtmax_degC * active / (thermal_limit_min + active)


def _cumulative_vq_m3_rad(row: dict[str, str], injection_duration_min: float) -> float | None:
    direct = _float(row.get("Vq_m3_rad"))
    if direct is not None:
        return direct
    injected_total = _float(row.get("injected_volume_m3"))
    if injected_total is not None and injected_total > 0.0:
        return injected_total / (2.0 * math.pi)
    q_total_m3_min = _float(row.get("Q_SI_m3_per_min"))
    time_min = _float(row.get("time_min"))
    if q_total_m3_min is None or time_min is None:
        return None
    active_time_min = min(max(time_min, 0.0), injection_duration_min)
    return q_total_m3_min * active_time_min / (2.0 * math.pi)


def _safe_delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return current - previous


def _correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    if x_var == 0.0 or y_var == 0.0:
        return None
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / math.sqrt(
        x_var * y_var
    )


def _stats(rows: list[dict[str, Any]], field: str) -> dict[str, float | None]:
    values = [
        float(row[field])
        for row in rows
        if row.get(field) is not None and math.isfinite(float(row[field]))
    ]
    if not values:
        return {
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "coefficient_of_variation": None,
        }
    avg = mean(values)
    std = pstdev(values)
    return {
        "mean": avg,
        "median": median(values),
        "std": std,
        "min": min(values),
        "max": max(values),
        "coefficient_of_variation": None if avg == 0.0 else std / abs(avg),
    }


def _valid_rows(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get(field) is not None and math.isfinite(float(row[field]))
    ]


def classify_apparent_compliance(rows: list[dict[str, Any]], field: str) -> str:
    valid = _valid_rows(rows, field)
    if len(valid) < 3:
        return "THERMAL_CORRECTED_COMPLIANCE_INCONCLUSIVE"
    values = [float(row[field]) for row in valid]
    times = [float(row["time_s"]) for row in valid]
    pressures = [float(row["dP_Pa"]) for row in valid]
    stats = _stats(valid, field)
    cv = stats["coefficient_of_variation"]
    corr_pressure = _correlation(pressures, values)
    corr_time = _correlation(times, values)
    if cv is not None and cv < 0.15 and (corr_pressure is None or abs(corr_pressure) < 0.5):
        return "THERMAL_CORRECTED_COMPLIANCE_NEAR_CONSTANT"
    if corr_pressure is not None and abs(corr_pressure) >= 0.70:
        return "THERMAL_CORRECTED_COMPLIANCE_PRESSURE_DEPENDENT"
    if corr_time is not None and abs(corr_time) >= 0.70:
        return "THERMAL_CORRECTED_COMPLIANCE_TIME_DEPENDENT"
    if cv is not None and cv >= 0.50:
        return "THERMAL_CORRECTED_COMPLIANCE_PHASE_DEPENDENT"
    return "THERMAL_CORRECTED_COMPLIANCE_INCONCLUSIVE"


def _compliance(delta_v: float | None, volume: float, delta_p: float | None, k: float) -> tuple[float | None, float | None, str]:
    if delta_v is None or delta_p is None:
        return None, None, "SKIPPED_MISSING_DELTA"
    if delta_p <= 0.0:
        return None, None, "SKIPPED_NON_POSITIVE_DELTA_PRESSURE"
    c_eff = delta_v / (volume * delta_p)
    return c_eff, c_eff - k, "OK"


def build_thermal_corrected_series(
    rows: list[dict[str, str]],
    *,
    thermal_profile: dict[str, Any],
    alpha_1_C: float,
    compressibility_1_Pa: float,
    annular_volume_m3_rad: float,
    injection_duration_min: float,
    legacy_open_time_s: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not rows:
        raise ValueError("legacy audit CSV has no rows")
    fields = set(rows[0])
    required = {"time_min", "time_s", "dP"}
    missing = sorted(required - fields)
    if missing:
        raise ValueError(f"legacy audit CSV missing required fields: {missing}")
    _require_positive(compressibility_1_Pa, "compressibility_1_Pa")
    _require_positive(annular_volume_m3_rad, "annular_volume_m3_rad")
    _require_positive(injection_duration_min, "injection_duration_min")

    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _float(row.get("time_s"))
        if time_s is not None:
            grouped.setdefault(time_s, []).append(row)

    ordered = [
        max(group, key=lambda item: _float(item.get("dP")) or -math.inf)
        for _, group in sorted(grouped.items())
    ]
    out: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    dtmax = float(thermal_profile["DTmax_degC"])
    t_initial = float(thermal_profile["T_initial_degC"])

    for index, row in enumerate(ordered):
        time_min = _float(row.get("time_min"))
        time_s = _float(row.get("time_s"))
        d_p = _float(row.get("dP"))
        vq = _cumulative_vq_m3_rad(row, injection_duration_min)
        if time_min is None or time_s is None:
            continue
        d_t = legacy_thermal_increment_degC(time_min, dtmax)
        thermal_pressure = alpha_1_C * d_t / compressibility_1_Pa
        d_p_subtract = None if d_p is None else d_p - thermal_pressure
        d_p_add = None if d_p is None else d_p + thermal_pressure

        delta_vq = _safe_delta(vq, None if previous is None else previous["Vq_m3_rad"])
        delta_dp = _safe_delta(d_p, None if previous is None else previous["dP_Pa"])
        delta_thermal = _safe_delta(
            thermal_pressure,
            None if previous is None else previous["thermal_pressure_equivalent_Pa"],
        )
        delta_dp_subtract = _safe_delta(
            d_p_subtract, None if previous is None else previous["dP_mech_subtract_Pa"]
        )
        delta_dp_add = _safe_delta(
            d_p_add, None if previous is None else previous["dP_mech_add_Pa"]
        )
        c_raw, cg_raw, raw_status = _compliance(
            delta_vq, annular_volume_m3_rad, delta_dp, compressibility_1_Pa
        )
        c_sub, cg_sub, sub_status = _compliance(
            delta_vq, annular_volume_m3_rad, delta_dp_subtract, compressibility_1_Pa
        )
        c_add, cg_add, add_status = _compliance(
            delta_vq, annular_volume_m3_rad, delta_dp_add, compressibility_1_Pa
        )
        out_row = {
            "step": index,
            "time_min": time_min,
            "time_s": time_s,
            "phase": "post_opening" if time_s >= legacy_open_time_s else "pre_opening",
            "Vq_m3_rad": vq,
            "delta_Vq_m3_rad": delta_vq,
            "dP_Pa": d_p,
            "delta_dP_Pa": delta_dp,
            "T_initial_degC": t_initial,
            "T_current_degC": t_initial + d_t,
            "T_final_degC": float(thermal_profile["T_final_degC"]),
            "dT_degC": d_t,
            "alpha_1_C": alpha_1_C,
            "k_1_Pa": compressibility_1_Pa,
            "thermal_term_alpha_dT": alpha_1_C * d_t,
            "thermal_pressure_equivalent_Pa": thermal_pressure,
            "delta_thermal_pressure_equivalent_Pa": delta_thermal,
            "thermal_fraction_accumulated": None
            if d_p in (None, 0.0)
            else thermal_pressure / d_p,
            "thermal_fraction_incremental": None
            if delta_dp in (None, 0.0)
            else (None if delta_thermal is None else delta_thermal / delta_dp),
            "dP_mech_subtract_Pa": d_p_subtract,
            "delta_dP_mech_subtract_Pa": delta_dp_subtract,
            "dP_mech_add_Pa": d_p_add,
            "delta_dP_mech_add_Pa": delta_dp_add,
            "C_eff_apparent_raw_1_Pa": c_raw,
            "C_geom_apparent_raw_1_Pa": cg_raw,
            "raw_status": raw_status,
            "C_eff_apparent_thermal_corrected_subtract_1_Pa": c_sub,
            "C_geom_apparent_thermal_corrected_subtract_1_Pa": cg_sub,
            "subtract_status": sub_status,
            "C_eff_apparent_thermal_corrected_add_1_Pa": c_add,
            "C_geom_apparent_thermal_corrected_add_1_Pa": cg_add,
            "add_status": add_status,
        }
        out.append(out_row)
        previous = out_row
    caveats = [
        "Thermal correction is reconstructed from the legacy case profile and audited dP trace.",
        "The subtract convention follows dP_mech = dP - alpha*dT/k from the active legacy balance.",
        "The add convention is reported only as a sign-sensitivity alternative.",
        "dV_geom, dMl and explicit per-step leakoff terms are still absent from the audit CSV.",
    ]
    return out, caveats


def _phase_rows(series: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    return [row for row in series if row.get("phase") == phase]


def summarize(series: list[dict[str, Any]], caveats: list[str], thermal_profile: dict[str, Any]) -> dict[str, Any]:
    pre = _phase_rows(series, "pre_opening")
    valid_subtract = _valid_rows(pre, "C_eff_apparent_thermal_corrected_subtract_1_Pa")
    valid_add = _valid_rows(pre, "C_eff_apparent_thermal_corrected_add_1_Pa")
    negative_mech = [
        row
        for row in pre
        if row.get("dP_mech_subtract_Pa") is not None and row["dP_mech_subtract_Pa"] < 0.0
    ]
    non_positive_delta_subtract = [
        row for row in pre if row.get("subtract_status") == "SKIPPED_NON_POSITIVE_DELTA_PRESSURE"
    ]
    sign_ambiguous = bool(negative_mech or non_positive_delta_subtract or len(valid_subtract) < 3)
    subtract_classification = (
        "THERMAL_CORRECTED_COMPLIANCE_SIGN_AMBIGUOUS"
        if sign_ambiguous
        else classify_apparent_compliance(
            pre, "C_eff_apparent_thermal_corrected_subtract_1_Pa"
        )
    )
    add_classification = classify_apparent_compliance(
        pre, "C_eff_apparent_thermal_corrected_add_1_Pa"
    )
    raw_classification = classify_apparent_compliance(pre, "C_eff_apparent_raw_1_Pa")

    raw_geom = _stats(pre, "C_geom_apparent_raw_1_Pa")
    subtract_geom = _stats(pre, "C_geom_apparent_thermal_corrected_subtract_1_Pa")
    add_geom = _stats(pre, "C_geom_apparent_thermal_corrected_add_1_Pa")
    mean_subtract_geom = subtract_geom["mean"]
    gate = [
        "THERMAL_CORRECTION_EXTRACTED_DIAGNOSTIC_ONLY",
        "PRESSURE_TABULATED_STILL_BLOCKED_MISSING_BALANCE_TERMS",
    ]
    if sign_ambiguous:
        gate.append("PRESSURE_TABULATED_STILL_BLOCKED_SIGN_CONVENTION_AMBIGUOUS")
    return {
        "phase": PHASE,
        "status": "PHASE10_21C_THERMAL_CORRECTED_APPARENT_COMPLIANCE_EXTRACTED",
        "classification": subtract_classification,
        "raw_classification": raw_classification,
        "subtract_classification": subtract_classification,
        "add_sign_sensitivity_classification": add_classification,
        "apparent_compliance_classification": subtract_classification,
        "level1_ready": False,
        "physical_validation": False,
        "numeric_equivalence": False,
        "runtime_default_changed": False,
        "pressure_tabulated_geometric_allowed": False,
        "thermal_profile": thermal_profile,
        "pre_opening": {
            "raw": {
                "C_eff_apparent": _stats(pre, "C_eff_apparent_raw_1_Pa"),
                "C_geom_apparent": raw_geom,
            },
            "thermal_corrected_subtract": {
                "C_eff_apparent": _stats(
                    pre, "C_eff_apparent_thermal_corrected_subtract_1_Pa"
                ),
                "C_geom_apparent": subtract_geom,
                "valid_n": len(valid_subtract),
                "negative_mechanical_pressure_n": len(negative_mech),
                "non_positive_delta_pressure_n": len(non_positive_delta_subtract),
            },
            "thermal_corrected_add_sign_sensitivity": {
                "C_eff_apparent": _stats(pre, "C_eff_apparent_thermal_corrected_add_1_Pa"),
                "C_geom_apparent": add_geom,
                "valid_n": len(valid_add),
            },
            "thermal_fraction": _stats(pre, "thermal_fraction_accumulated"),
        },
        "correlations": {
            "subtract_vs_pressure": _correlation(
                [row["dP_Pa"] for row in valid_subtract],
                [row["C_eff_apparent_thermal_corrected_subtract_1_Pa"] for row in valid_subtract],
            ),
            "subtract_vs_time": _correlation(
                [row["time_s"] for row in valid_subtract],
                [row["C_eff_apparent_thermal_corrected_subtract_1_Pa"] for row in valid_subtract],
            ),
            "add_vs_pressure": _correlation(
                [row["dP_Pa"] for row in valid_add],
                [row["C_eff_apparent_thermal_corrected_add_1_Pa"] for row in valid_add],
            ),
            "add_vs_time": _correlation(
                [row["time_s"] for row in valid_add],
                [row["C_eff_apparent_thermal_corrected_add_1_Pa"] for row in valid_add],
            ),
        },
        "comparison": {
            "C_geom_constant_10_19C": C_GEOM_CONSTANT_10_19C,
            "C_eff_constant_10_19C": C_EFF_CONSTANT_10_19C,
            "subtract_mean_C_geom_to_constant_ratio": None
            if mean_subtract_geom in (None, 0.0)
            else mean_subtract_geom / C_GEOM_CONSTANT_10_19C,
            "raw_mean_C_geom_to_constant_ratio": None
            if raw_geom["mean"] in (None, 0.0)
            else raw_geom["mean"] / C_GEOM_CONSTANT_10_19C,
        },
        "gate": gate,
        "caveats": caveats
        + [
            "This is still diagnostic extraction, not a solver model.",
            "Do not implement pressure_tabulated_geometric from this series until sign convention and missing balance terms are resolved.",
        ],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_plots(series: list[dict[str, Any]], output_dir: Path) -> dict[str, bool]:
    names = [
        "thermal_profile_at_prof_teste.png",
        "dT_vs_time.png",
        "thermal_pressure_equivalent_vs_time.png",
        "thermal_fraction_vs_time.png",
        "raw_vs_thermal_corrected_compliance_vs_time.png",
        "raw_vs_thermal_corrected_compliance_vs_pressure.png",
        "mechanical_pressure_sign_sensitivity.png",
        "constant_geometric_comparison.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}

    output_dir.mkdir(parents=True, exist_ok=True)
    times = [row["time_s"] for row in series]
    dps = [row["dP_Pa"] for row in series]

    def save(name: str) -> None:
        plt.figtext(0.5, 0.01, "Phase 10.21C diagnostic only", ha="center", fontsize=8)
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()

    plt.figure()
    plt.plot(times, [row["T_current_degC"] for row in series], label="T_current")
    plt.axhline(series[0]["T_initial_degC"], linestyle="--", label="T_initial")
    plt.axhline(series[0]["T_final_degC"], linestyle="--", label="T_final")
    plt.xlabel("time_s")
    plt.ylabel("degC")
    plt.legend()
    save("thermal_profile_at_prof_teste.png")

    plt.figure()
    plt.plot(times, [row["dT_degC"] for row in series])
    plt.xlabel("time_s")
    plt.ylabel("dT_degC")
    save("dT_vs_time.png")

    plt.figure()
    plt.plot(times, [row["thermal_pressure_equivalent_Pa"] for row in series])
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    save("thermal_pressure_equivalent_vs_time.png")

    plt.figure()
    plt.plot(times, [row["thermal_fraction_accumulated"] for row in series])
    plt.xlabel("time_s")
    plt.ylabel("thermal_pressure/dP")
    save("thermal_fraction_vs_time.png")

    plt.figure()
    plt.plot(times, [row["C_eff_apparent_raw_1_Pa"] for row in series], label="raw")
    plt.plot(
        times,
        [row["C_eff_apparent_thermal_corrected_subtract_1_Pa"] for row in series],
        label="subtract",
    )
    plt.plot(
        times,
        [row["C_eff_apparent_thermal_corrected_add_1_Pa"] for row in series],
        label="add sensitivity",
    )
    plt.yscale("log")
    plt.xlabel("time_s")
    plt.ylabel("1/Pa")
    plt.legend()
    save("raw_vs_thermal_corrected_compliance_vs_time.png")

    plt.figure()
    plt.scatter(dps, [row["C_eff_apparent_raw_1_Pa"] for row in series], label="raw")
    plt.scatter(
        dps,
        [row["C_eff_apparent_thermal_corrected_subtract_1_Pa"] for row in series],
        label="subtract",
    )
    plt.yscale("log")
    plt.xlabel("dP_Pa")
    plt.ylabel("1/Pa")
    plt.legend()
    save("raw_vs_thermal_corrected_compliance_vs_pressure.png")

    plt.figure()
    plt.plot(times, dps, label="dP")
    plt.plot(times, [row["dP_mech_subtract_Pa"] for row in series], label="dP - thermal")
    plt.plot(times, [row["dP_mech_add_Pa"] for row in series], label="dP + thermal")
    plt.axhline(0.0, color="black", linewidth=0.8)
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    plt.legend()
    save("mechanical_pressure_sign_sensitivity.png")

    plt.figure()
    pre = [row for row in series if row["phase"] == "pre_opening"]
    subtract_mean = _stats(pre, "C_geom_apparent_thermal_corrected_subtract_1_Pa")[
        "mean"
    ] or 0.0
    raw_mean = _stats(pre, "C_geom_apparent_raw_1_Pa")["mean"] or 0.0
    plt.bar(
        ["raw mean", "thermal subtract mean", "constant 10.19C"],
        [raw_mean, subtract_mean, C_GEOM_CONSTANT_10_19C],
    )
    plt.yscale("log")
    plt.ylabel("C_geom 1/Pa")
    save("constant_geometric_comparison.png")
    return {name: (output_dir / name).exists() for name in names}


def run_extraction(args: argparse.Namespace) -> dict[str, Any]:
    _require_non_negative(args.prof_teste_m, "prof_teste_m")
    _require_positive(args.alpha_1_C, "alpha_1_C")
    _require_positive(args.compressibility_1_Pa, "compressibility_1_Pa")
    profile = build_thermal_profile(Path(args.legacy_case), args.prof_teste_m)
    profile["alpha_1_C"] = args.alpha_1_C
    profile["compressibility_1_Pa"] = args.compressibility_1_Pa
    rows = _read_csv(Path(args.legacy_audit_csv))
    series, caveats = build_thermal_corrected_series(
        rows,
        thermal_profile=profile,
        alpha_1_C=args.alpha_1_C,
        compressibility_1_Pa=args.compressibility_1_Pa,
        annular_volume_m3_rad=args.annular_volume_m3_rad,
        injection_duration_min=args.injection_duration_min,
        legacy_open_time_s=args.legacy_open_time_s,
    )
    output_dir = Path(args.output_dir)
    plots = _write_plots(series, output_dir)
    summary = summarize(series, caveats, profile)
    summary["plots"] = plots
    summary["legacy_case"] = str(args.legacy_case)
    summary["legacy_audit_csv"] = str(args.legacy_audit_csv)
    _write_csv(Path(args.output_csv), series)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "thermal_corrected_compliance_metadata.json").write_text(
        json.dumps(
            {
                "phase": PHASE,
                "source_case": str(args.legacy_case),
                "source_audit_csv": str(args.legacy_audit_csv),
                "instrumentation_status": "NO_LEGANCE_MODIFICATION_USED_EXISTING_AUDIT_TRACE",
                "classification": summary["classification"],
                "gate": summary["gate"],
                "caveats": summary["caveats"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Phase 10.21C thermally corrected apparent compliance diagnostics."
    )
    parser.add_argument("--legacy-case", required=True, type=Path)
    parser.add_argument("--legacy-audit-csv", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prof-teste-m", type=float, default=DEFAULT_PROF_TESTE_M)
    parser.add_argument("--alpha-1-C", type=float, default=DEFAULT_ALPHA_1_C)
    parser.add_argument(
        "--compressibility-1-Pa", type=float, default=DEFAULT_COMPRESSIBILITY_1_PA
    )
    parser.add_argument(
        "--thermal-evolution",
        choices=["legacy"],
        default="legacy",
        help="Legacy DT(t)=DTmax*t/(Tlimit+t) evolution.",
    )
    parser.add_argument(
        "--annular-volume-m3-rad",
        type=float,
        default=DEFAULT_ANNULAR_VOLUME_M3_RAD,
    )
    parser.add_argument(
        "--injection-duration-min",
        type=float,
        default=DEFAULT_INJECTION_DURATION_MIN,
    )
    parser.add_argument(
        "--legacy-open-time-s",
        type=float,
        default=DEFAULT_LEGACY_OPEN_TIME_S,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run_extraction(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": summary["phase"],
                "classification": summary["classification"],
                "gate": summary["gate"],
                "thermal_profile": summary["thermal_profile"],
                "pre_opening": summary["pre_opening"]["thermal_corrected_subtract"],
                "comparison": summary["comparison"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
