from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


PHASE = "10.21A"
C_FLUID_1_PA = 6.4e-10
C_GEOM_CONSTANT_10_19C = 1.8571966938610005e-8
C_EFF_CONSTANT_10_19C = 1.9211966938610006e-8
C_GEOM_ELASTIC_10_20C = 1.7242805809704984e-10
DEFAULT_ANNULAR_VOLUME_M3_RAD = 0.17842518895535997
DEFAULT_INJECTION_DURATION_MIN = 12.5
DEFAULT_LEGACY_OPEN_TIME_S = 510.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _safe_delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return current - previous


def _cumulative_vq_m3_rad(row: dict[str, str], injection_duration_min: float) -> float | None:
    direct = _float(row.get("Vq_m3_rad"))
    if direct is not None:
        return direct
    total_injected = _float(row.get("injected_volume_m3"))
    if total_injected is not None and total_injected > 0.0:
        return total_injected / (2.0 * math.pi)
    q_total_m3_min = _float(row.get("Q_SI_m3_per_min"))
    time_min = _float(row.get("time_min"))
    if q_total_m3_min is None or time_min is None:
        return None
    active_time_min = min(max(time_min, 0.0), injection_duration_min)
    return q_total_m3_min * active_time_min / (2.0 * math.pi)


def _linear_slope(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0.0:
        return None
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom


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
    return {
        "mean": avg,
        "median": median(values),
        "std": pstdev(values),
        "min": min(values),
        "max": max(values),
        "coefficient_of_variation": None if avg == 0.0 else pstdev(values) / abs(avg),
    }


def _classify(pre_rows: list[dict[str, Any]]) -> str:
    valid = [
        row
        for row in pre_rows
        if row.get("C_eff_apparent_1_Pa") is not None
        and math.isfinite(float(row["C_eff_apparent_1_Pa"]))
    ]
    if len(valid) < 3:
        return "APPARENT_COMPLIANCE_INCONCLUSIVE"
    stats = _stats(valid, "C_eff_apparent_1_Pa")
    cv = stats["coefficient_of_variation"]
    times = [float(row["time_s"]) for row in valid]
    pressures = [float(row["pw_Pa"]) for row in valid]
    values = [float(row["C_eff_apparent_1_Pa"]) for row in valid]
    corr_time = _correlation(times, values)
    corr_pressure = _correlation(pressures, values)
    if cv is not None and cv < 0.15:
        if (corr_time is None or abs(corr_time) < 0.5) and (
            corr_pressure is None or abs(corr_pressure) < 0.5
        ):
            return "APPARENT_COMPLIANCE_NEAR_CONSTANT"
    if corr_pressure is not None and abs(corr_pressure) >= 0.70:
        return "APPARENT_COMPLIANCE_PRESSURE_DEPENDENT"
    if corr_time is not None and abs(corr_time) >= 0.70:
        return "APPARENT_COMPLIANCE_TIME_DEPENDENT"
    if cv is not None and cv >= 0.50:
        return "APPARENT_COMPLIANCE_PHASE_DEPENDENT"
    return "APPARENT_COMPLIANCE_INCONCLUSIVE"


def build_series(
    rows: list[dict[str, str]],
    *,
    annular_volume_m3_rad: float,
    fluid_compressibility_1_Pa: float,
    injection_duration_min: float,
    legacy_open_time_s: float,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if annular_volume_m3_rad <= 0.0:
        raise ValueError("annular_volume_m3_rad must be positive")
    fields = set(rows[0]) if rows else set()
    required = {"time_s", "dP", "pw_Pa"}
    missing_required = sorted(required - fields)
    if missing_required:
        raise ValueError(f"legacy trace missing required fields: {missing_required}")
    desired = {
        "dV_geom_m3_rad",
        "dV_leakoff_m3_rad",
        "dMl_term_m3_rad",
        "Vi_m3_rad",
        "k_1_Pa",
        "sigmaTheta_Pa",
        "opened",
    }
    fields_missing = sorted(desired - fields)
    fields_exported = sorted(fields)

    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _float(row.get("time_s"))
        if time_s is None:
            continue
        grouped.setdefault(time_s, []).append(row)
    ordered = [
        max(group, key=lambda item: _float(item.get("dP")) or -math.inf)
        for _, group in sorted(grouped.items())
    ]
    series: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for index, row in enumerate(ordered):
        time_s = _float(row.get("time_s"))
        time_min = _float(row.get("time_min"))
        d_p = _float(row.get("dP"))
        pw = _float(row.get("pw_Pa"))
        vq = _cumulative_vq_m3_rad(row, injection_duration_min)
        d_v_geom = _float(row.get("dV_geom_m3_rad"))
        d_v_leakoff = _float(row.get("dV_leakoff_m3_rad"))
        d_ml_term = _float(row.get("dMl_term_m3_rad"))
        k = _float(row.get("k_1_Pa")) or fluid_compressibility_1_Pa
        opened = str(row.get("opened", "")).lower() in {"1", "true", "yes"}
        if time_s is not None and time_s >= legacy_open_time_s:
            opened = True

        delta_vq = _safe_delta(vq, None if previous is None else previous["Vq_m3_rad"])
        delta_dp = _safe_delta(d_p, None if previous is None else previous["dP_Pa"])
        delta_pw = _safe_delta(pw, None if previous is None else previous["pw_Pa"])
        delta_dv_geom = _safe_delta(
            d_v_geom, None if previous is None else previous.get("dV_geom_m3_rad")
        )
        delta_dv_leakoff = _safe_delta(
            d_v_leakoff, None if previous is None else previous.get("dV_leakoff_m3_rad")
        )
        delta_dml = _safe_delta(
            d_ml_term, None if previous is None else previous.get("dMl_term_m3_rad")
        )

        c_eff = None
        c_geom = None
        formula_status = "NOT_EVALUATED_FIRST_ROW"
        if (
            delta_vq is not None
            and delta_dp is not None
            and delta_dp != 0.0
            and annular_volume_m3_rad > 0.0
        ):
            c_eff = delta_vq / (annular_volume_m3_rad * delta_dp)
            c_geom = c_eff - k
            formula_status = "REDUCED_VQ_OVER_VI_DP"
        elif delta_dp == 0.0:
            formula_status = "SKIPPED_ZERO_DELTA_DP"

        out = {
            "step": index,
            "time_min": time_min,
            "time_s": time_s,
            "dt_min": None if previous is None or time_min is None else time_min - previous["time_min"],
            "dt_s": None if previous is None or time_s is None else time_s - previous["time_s"],
            "Vq_m3_rad": vq,
            "delta_Vq_m3_rad": delta_vq,
            "dV_geom_m3_rad": d_v_geom,
            "delta_dV_geom_m3_rad": delta_dv_geom,
            "dV_leakoff_m3_rad": d_v_leakoff,
            "delta_dV_leakoff_m3_rad": delta_dv_leakoff,
            "dMl_term_m3_rad": d_ml_term,
            "delta_dMl_term_m3_rad": delta_dml,
            "Vi_m3_rad": annular_volume_m3_rad,
            "k_1_Pa": k,
            "dP_Pa": d_p,
            "delta_dP_Pa": delta_dp,
            "pw_Pa": pw,
            "delta_pw_Pa": delta_pw,
            "sigmaTheta_Pa": _float(row.get("sigmaTheta_Pa")),
            "margin_Pa": None,
            "opened": opened,
            "phase": "post_opening" if opened else "pre_opening",
            "C_eff_apparent_1_Pa": c_eff,
            "C_geom_apparent_1_Pa": c_geom,
            "formula_status": formula_status,
        }
        if out["sigmaTheta_Pa"] is not None and pw is not None:
            out["margin_Pa"] = pw - out["sigmaTheta_Pa"]
        series.append(out)
        previous = out
    return series, fields_exported, fields_missing


def _phase_rows(series: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    return [
        row
        for row in series
        if row.get("phase") == phase and row.get("C_eff_apparent_1_Pa") is not None
    ]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _plot(series: list[dict[str, Any]], output_dir: Path) -> dict[str, bool]:
    names = [
        "apparent_compliance_vs_time.png",
        "apparent_compliance_vs_pressure.png",
        "geometric_volume_terms_vs_time.png",
        "pressure_and_opening_vs_time.png",
        "compliance_model_comparison.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, bool] = {}

    valid = [row for row in series if row.get("C_eff_apparent_1_Pa") is not None]
    times = [row["time_s"] for row in valid]
    ceff = [row["C_eff_apparent_1_Pa"] for row in valid]
    cgeom = [row["C_geom_apparent_1_Pa"] for row in valid]
    pressures = [row["pw_Pa"] for row in valid]

    def save(name: str) -> None:
        plt.figtext(
            0.5,
            0.01,
            "Phase 10.21A - diagnostic extraction from legacy trace",
            ha="center",
            fontsize=8,
        )
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()
        generated[name] = True

    plt.figure()
    plt.plot(times, ceff, label="C_eff_apparent")
    plt.plot(times, cgeom, label="C_geom_apparent")
    plt.axhline(C_EFF_CONSTANT_10_19C, linestyle="--", label="C_eff_constant_10_19C")
    plt.xlabel("time_s")
    plt.ylabel("1/Pa")
    plt.yscale("log")
    plt.legend()
    save("apparent_compliance_vs_time.png")

    plt.figure()
    plt.scatter(pressures, ceff, label="C_eff_apparent")
    plt.xlabel("pw_Pa")
    plt.ylabel("1/Pa")
    plt.yscale("log")
    plt.legend()
    save("apparent_compliance_vs_pressure.png")

    plt.figure()
    plt.plot([row["time_s"] for row in series], [row["Vq_m3_rad"] for row in series], label="Vq")
    plt.xlabel("time_s")
    plt.ylabel("m3/rad")
    plt.legend()
    save("geometric_volume_terms_vs_time.png")

    plt.figure()
    plt.plot([row["time_s"] for row in series], [row["pw_Pa"] for row in series], label="pw_Pa")
    open_times = [row["time_s"] for row in series if row["opened"]]
    if open_times:
        plt.axvline(open_times[0], color="red", linestyle="--", label="opening marker")
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    plt.legend()
    save("pressure_and_opening_vs_time.png")

    plt.figure()
    labels = ["mean C_geom app", "constant 10.19C", "elastic 10.20C"]
    pre = _phase_rows(series, "pre_opening")
    mean_cgeom = _stats(pre, "C_geom_apparent_1_Pa")["mean"] or 0.0
    plt.bar(labels, [mean_cgeom, C_GEOM_CONSTANT_10_19C, C_GEOM_ELASTIC_10_20C])
    plt.yscale("log")
    plt.ylabel("1/Pa")
    save("compliance_model_comparison.png")

    return generated


def run_extraction(args: argparse.Namespace) -> dict[str, Any]:
    rows = _read_csv(Path(args.legacy_trace))
    series, fields_exported, fields_missing = build_series(
        rows,
        annular_volume_m3_rad=args.annular_volume_m3_rad,
        fluid_compressibility_1_Pa=args.fluid_compressibility_1_Pa,
        injection_duration_min=args.injection_duration_min,
        legacy_open_time_s=args.legacy_open_time_s,
    )
    output_dir = Path(args.output_dir)
    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    trace_csv = output_dir / "legacy_apparent_compliance_trace.csv"
    _write_csv(output_csv, series)
    _write_csv(trace_csv, series)

    pre = _phase_rows(series, "pre_opening")
    opening = [
        row
        for row in series
        if row.get("opened") and row.get("C_eff_apparent_1_Pa") is not None
    ][:1]
    post = _phase_rows(series, "post_opening")
    classification = _classify(pre)
    valid_pre = [row for row in pre if row.get("C_eff_apparent_1_Pa") is not None]
    times = [float(row["time_s"]) for row in valid_pre]
    pressures = [float(row["pw_Pa"]) for row in valid_pre]
    ceff_values = [float(row["C_eff_apparent_1_Pa"]) for row in valid_pre]
    plots = _plot(series, output_dir)

    pre_cgeom_mean = _stats(pre, "C_geom_apparent_1_Pa")["mean"]
    comparison = {
        "C_geom_constant_10_19C": C_GEOM_CONSTANT_10_19C,
        "C_eff_constant_10_19C": C_EFF_CONSTANT_10_19C,
        "C_fluid": args.fluid_compressibility_1_Pa,
        "C_geom_elastic_10_20C": C_GEOM_ELASTIC_10_20C,
        "pre_opening_mean_C_geom_apparent_1_Pa": pre_cgeom_mean,
        "ratio_pre_mean_to_constant_10_19C": None
        if pre_cgeom_mean is None
        else pre_cgeom_mean / C_GEOM_CONSTANT_10_19C,
        "ratio_elastic_10_20C_to_pre_mean": None
        if pre_cgeom_mean in (None, 0.0)
        else C_GEOM_ELASTIC_10_20C / pre_cgeom_mean,
    }
    summary = {
        "phase": PHASE,
        "status": "PHASE10_21A_APPARENT_COMPLIANCE_EXTRACTED",
        "classification": classification,
        "physical_validation": False,
        "numeric_equivalence": False,
        "legacy_trace": str(args.legacy_trace),
        "fields_exported": fields_exported,
        "fields_missing": fields_missing,
        "formula": {
            "legacy_balance": "dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k",
            "reduced_apparent": "C_eff_apparent = delta_Vq_m3_rad / (Vi_m3_rad * delta_dP_Pa)",
            "C_geom_apparent": "C_eff_apparent - k_1_Pa",
            "status": "REDUCED_TRACE_NO_EXPLICIT_DV_GEOM_OR_DML",
        },
        "unit_conventions": {
            "Vq": "m3/rad",
            "Vi": "m3/rad",
            "pressure": "Pa",
            "time": "s and min",
            "fluid_compressibility": "1/Pa",
        },
        "statistics": {
            "pre_opening": {
                "C_eff_apparent": _stats(pre, "C_eff_apparent_1_Pa"),
                "C_geom_apparent": _stats(pre, "C_geom_apparent_1_Pa"),
                "linear_trend_vs_pressure": _linear_slope(pressures, ceff_values),
                "linear_trend_vs_time": _linear_slope(times, ceff_values),
                "correlation_vs_pressure": _correlation(pressures, ceff_values),
                "correlation_vs_time": _correlation(times, ceff_values),
                "n": len(valid_pre),
            },
            "opening_step": {
                "C_eff_apparent": _stats(opening, "C_eff_apparent_1_Pa"),
                "C_geom_apparent": _stats(opening, "C_geom_apparent_1_Pa"),
                "n": len(opening),
            },
            "post_opening": {
                "C_eff_apparent": _stats(post, "C_eff_apparent_1_Pa"),
                "C_geom_apparent": _stats(post, "C_geom_apparent_1_Pa"),
                "n": len(post),
            },
        },
        "comparison": comparison,
        "plots": plots,
        "notes": [
            "No legacy source was modified by this extraction tool.",
            "The available audited legacy CSV does not expose dV_geom or dMl_term directly.",
            "The apparent compliance is therefore a reduced incremental estimate from Vq, Vi and dP.",
            "Generated results are diagnostic artifacts and must not be versioned.",
        ],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    metadata_path = output_dir / "legacy_apparent_compliance_trace_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "case_name": "BUZ67D PKN legacy apparent compliance",
                "source_file": str(args.legacy_trace),
                "instrumented_files": [],
                "instrumentation_status": "NOT_MODIFIED_USING_EXISTING_AUDIT_TRACE",
                "fields_exported": fields_exported,
                "fields_missing": fields_missing,
                "unit_conventions": summary["unit_conventions"],
                "notes": summary["notes"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Phase 10.21A apparent compliance from a legacy LOT trace."
    )
    parser.add_argument("--legacy-trace", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--annular-volume-m3-rad",
        type=float,
        default=DEFAULT_ANNULAR_VOLUME_M3_RAD,
    )
    parser.add_argument(
        "--fluid-compressibility-1-Pa",
        type=float,
        default=C_FLUID_1_PA,
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
                "pre_opening": summary["statistics"]["pre_opening"],
                "comparison": summary["comparison"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
