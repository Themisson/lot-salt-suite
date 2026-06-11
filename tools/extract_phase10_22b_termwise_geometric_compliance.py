from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


PHASE = "10.22B"
C_GEOM_CONSTANT_10_19C = 1.8571966938610005e-8
C_EFF_CONSTANT_10_19C = 1.9211966938610006e-8
C_GEOM_ELASTIC_10_20C = 1.7242805809704984e-10

REQUIRED_COLUMNS = {
    "time_s",
    "time_min",
    "Vq_m3_rad",
    "dV_total_m3_rad",
    "Vi_m3_rad",
    "dP_Pa",
    "thermal_pressure_equivalent_Pa",
    "volumetric_pressure_equivalent_Pa",
    "dMl_term_m3_rad",
    "dV_leakoff_m3_rad",
}

OPTIONAL_COLUMNS = {
    "dV_increment_m3_rad",
    "dP_increment_Pa",
    "pw_Pa",
    "dMl_term_increment_m3_rad",
    "dV_leakoff_increment_m3_rad",
    "opened",
    "sigmaTheta_Pa",
    "margin_Pa",
    "opened_before_step",
    "opened_after_step",
    "T_final_C",
}


def _float(value: str | float | int | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0.0:
        return None
    return num / den


def _bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes"}:
        return True
    if lowered in {"0", "false", "no"}:
        return False
    return None


def read_trace(path: Path) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = sorted(REQUIRED_COLUMNS - set(columns))
        if missing:
            raise ValueError(f"trace missing required columns: {missing}")
        rows: list[dict[str, Any]] = []
        for raw in reader:
            row: dict[str, Any] = dict(raw)
            for key in set(columns) - {"opened", "opened_before_step", "opened_after_step"}:
                row[key] = _float(raw.get(key))
            for key in {"opened", "opened_before_step", "opened_after_step"}:
                row[key] = _bool(raw.get(key))
            rows.append(row)
    missing_optional = sorted(
        key for key in OPTIONAL_COLUMNS if key not in columns or all(r.get(key) is None for r in rows)
    )
    return rows, columns, missing_optional


def representative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_time: dict[float, list[dict[str, Any]]] = {}
    for row in rows:
        time_s = row.get("time_s")
        if time_s is not None:
            by_time.setdefault(float(time_s), []).append(row)
    return [
        max(group, key=lambda item: item.get("dP_Pa") if item.get("dP_Pa") is not None else -math.inf)
        for _, group in sorted(by_time.items())
    ]


def add_missing_increments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for row in rows:
        enriched = dict(row)
        for source, target in [
            ("dV_total_m3_rad", "dV_increment_m3_rad"),
            ("dP_Pa", "dP_increment_Pa"),
            ("dMl_term_m3_rad", "dMl_term_increment_m3_rad"),
            ("dV_leakoff_m3_rad", "dV_leakoff_increment_m3_rad"),
        ]:
            if enriched.get(target) is None:
                enriched[target] = (
                    None
                    if previous is None or enriched.get(source) is None or previous.get(source) is None
                    else enriched[source] - previous[source]
                )
        out.append(enriched)
        previous = enriched
    return out


def _regime(time_s: float | None) -> str:
    if time_s is None:
        return "unknown"
    if abs(time_s - 510.0) <= 1.0e-6:
        return "opening_step_known"
    if time_s < 510.0:
        return "pre_opening_known"
    if time_s >= 540.0:
        return "first_sink_positive_known"
    return "between_opening_and_sink_known"


def add_compliance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        enriched = dict(row)
        vi = row.get("Vi_m3_rad")
        dp = row.get("dP_Pa")
        dvi = row.get("dV_total_m3_rad")
        delta_dv = row.get("dV_increment_m3_rad")
        delta_dp = row.get("dP_increment_Pa")
        thermal = row.get("thermal_pressure_equivalent_Pa")
        volumetric = row.get("volumetric_pressure_equivalent_Pa")
        vq = row.get("Vq_m3_rad")
        dml = row.get("dMl_term_m3_rad")
        leakoff = row.get("dV_leakoff_m3_rad")
        volumetric_volume = None
        if None not in (vq, dvi, dml):
            volumetric_volume = vq - dvi + dml
        pressure_for_corr = row.get("pw_Pa") if row.get("pw_Pa") is not None else dp
        enriched["regime"] = _regime(row.get("time_s"))
        enriched["regime_source"] = "known_from_previous_phase_not_from_this_trace"
        enriched["injection_regime"] = "injection" if row.get("time_s") is not None and row["time_s"] <= 750.0 else "shut_in"
        enriched["C_geom_accumulated_1_Pa"] = (
            _safe_div(dvi, vi * dp) if vi is not None and vi > 0.0 and dp not in (None, 0.0) else None
        )
        enriched["C_geom_incremental_1_Pa"] = (
            _safe_div(delta_dv, vi * delta_dp)
            if vi is not None and vi > 0.0 and delta_dp not in (None, 0.0)
            else None
        )
        enriched["C_eff_equivalent_from_total_balance_1_Pa"] = (
            _safe_div(volumetric_volume, vi * dp)
            if vi is not None and vi > 0.0 and dp not in (None, 0.0)
            else None
        )
        enriched["C_geom_from_volumetric_pressure_equivalent_1_Pa"] = (
            None
            if dp in (None, 0.0) or volumetric is None
            else C_EFF_CONSTANT_10_19C * (volumetric / dp)
        )
        enriched["thermal_fraction"] = _safe_div(thermal, dp)
        enriched["volumetric_fraction"] = _safe_div(volumetric, dp)
        enriched["dMl_fraction"] = _safe_div(dml, volumetric_volume)
        enriched["dV_leakoff_fraction"] = _safe_div(leakoff, vq)
        enriched["ratio_C_geom_accumulated_to_constant_10_19C"] = _safe_div(
            enriched["C_geom_accumulated_1_Pa"], C_GEOM_CONSTANT_10_19C
        )
        enriched["ratio_C_geom_incremental_to_constant_10_19C"] = _safe_div(
            enriched["C_geom_incremental_1_Pa"], C_GEOM_CONSTANT_10_19C
        )
        enriched["percent_difference_C_geom_accumulated_to_constant_10_19C"] = (
            None
            if enriched["ratio_C_geom_accumulated_to_constant_10_19C"] is None
            else (enriched["ratio_C_geom_accumulated_to_constant_10_19C"] - 1.0) * 100.0
        )
        enriched["percent_difference_C_geom_incremental_to_constant_10_19C"] = (
            None
            if enriched["ratio_C_geom_incremental_to_constant_10_19C"] is None
            else (enriched["ratio_C_geom_incremental_to_constant_10_19C"] - 1.0) * 100.0
        )
        enriched["pressure_for_correlation_Pa"] = pressure_for_corr
        out.append(enriched)
    return out


def _values(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [
        float(row[field])
        for row in rows
        if row.get(field) is not None and math.isfinite(float(row[field]))
    ]


def _correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = mean(xs)
    my = mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0.0 or sy == 0.0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def _slope(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = mean(xs)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0.0:
        return None
    my = mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def _stats(rows: list[dict[str, Any]], field: str) -> dict[str, float | int | None]:
    pairs_pressure = [
        (float(row["pressure_for_correlation_Pa"]), float(row[field]))
        for row in rows
        if row.get(field) is not None
        and row.get("pressure_for_correlation_Pa") is not None
        and math.isfinite(float(row[field]))
        and math.isfinite(float(row["pressure_for_correlation_Pa"]))
    ]
    pairs_time = [
        (float(row["time_s"]), float(row[field]))
        for row in rows
        if row.get(field) is not None
        and row.get("time_s") is not None
        and math.isfinite(float(row[field]))
        and math.isfinite(float(row["time_s"]))
    ]
    values = _values(rows, field)
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "coefficient_of_variation": None,
            "correlation_with_pressure": None,
            "correlation_with_time": None,
            "linear_trend_vs_pressure": None,
            "linear_trend_vs_time": None,
        }
    avg = mean(values)
    std = pstdev(values)
    px, py = zip(*pairs_pressure) if pairs_pressure else ([], [])
    tx, ty = zip(*pairs_time) if pairs_time else ([], [])
    return {
        "count": len(values),
        "mean": avg,
        "median": median(values),
        "std": std,
        "min": min(values),
        "max": max(values),
        "coefficient_of_variation": None if avg == 0.0 else std / abs(avg),
        "correlation_with_pressure": _correlation(list(px), list(py)),
        "correlation_with_time": _correlation(list(tx), list(ty)),
        "linear_trend_vs_pressure": _slope(list(px), list(py)),
        "linear_trend_vs_time": _slope(list(tx), list(ty)),
    }


def classify_series(stats: dict[str, Any], rows: list[dict[str, Any]], field: str) -> str:
    if stats["count"] is None or int(stats["count"]) < 4:
        return "TERMWISE_GEOM_COMPLIANCE_INCONCLUSIVE"
    values = _values(rows, field)
    has_sign_change = any(v < 0.0 for v in values) and any(v > 0.0 for v in values)
    cv = stats.get("coefficient_of_variation")
    corr_p = abs(stats.get("correlation_with_pressure") or 0.0)
    corr_t = abs(stats.get("correlation_with_time") or 0.0)
    if has_sign_change or (cv is not None and cv > 0.5):
        return "TERMWISE_GEOM_COMPLIANCE_NOISY"
    if cv is not None and cv < 0.15 and corr_p < 0.4 and corr_t < 0.4:
        return "TERMWISE_GEOM_COMPLIANCE_NEAR_CONSTANT"
    if corr_p >= 0.6:
        return "TERMWISE_GEOM_COMPLIANCE_PRESSURE_DEPENDENT"
    if corr_t >= 0.6:
        return "TERMWISE_GEOM_COMPLIANCE_TIME_DEPENDENT"
    return "TERMWISE_GEOM_COMPLIANCE_INCONCLUSIVE"


def summarize(rows: list[dict[str, Any]], columns: list[str], missing_optional: list[str]) -> dict[str, Any]:
    regimes = {
        "pre_opening_known": [r for r in rows if r["regime"] == "pre_opening_known"],
        "opening_step_known": [r for r in rows if r["regime"] == "opening_step_known"],
        "first_sink_positive_known": [r for r in rows if r["regime"] == "first_sink_positive_known"],
        "injection": [r for r in rows if r["injection_regime"] == "injection"],
        "shut_in": [r for r in rows if r["injection_regime"] == "shut_in"],
        "all_representative_rows": rows,
    }
    statistics: dict[str, Any] = {}
    for name, subset in regimes.items():
        statistics[name] = {
            "C_geom_accumulated": _stats(subset, "C_geom_accumulated_1_Pa"),
            "C_geom_incremental": _stats(subset, "C_geom_incremental_1_Pa"),
            "C_eff_equivalent_from_total_balance": _stats(
                subset, "C_eff_equivalent_from_total_balance_1_Pa"
            ),
        }
    pre = regimes["pre_opening_known"]
    accumulated_classification = classify_series(
        statistics["pre_opening_known"]["C_geom_accumulated"], pre, "C_geom_accumulated_1_Pa"
    )
    incremental_classification = classify_series(
        statistics["pre_opening_known"]["C_geom_incremental"], pre, "C_geom_incremental_1_Pa"
    )
    phase_dependent = False
    pre_mean = statistics["pre_opening_known"]["C_geom_accumulated"]["mean"]
    post_mean = statistics["first_sink_positive_known"]["C_geom_accumulated"]["mean"]
    if pre_mean not in (None, 0.0) and post_mean is not None:
        phase_dependent = abs((post_mean - pre_mean) / pre_mean) > 0.5
    gate = ["LEGACY_OPENING_TRACE_STILL_REQUIRED"]
    if accumulated_classification == "TERMWISE_GEOM_COMPLIANCE_NEAR_CONSTANT":
        gate.append("CONSTANT_GEOMETRIC_STILL_BEST_DIAGNOSTIC")
    elif incremental_classification in {
        "TERMWISE_GEOM_COMPLIANCE_PRESSURE_DEPENDENT",
        "TERMWISE_GEOM_COMPLIANCE_TIME_DEPENDENT",
    }:
        gate.append("PRESSURE_TABULATED_CAN_BE_RETRIED_WITH_TERMWISE_GEOM")
    else:
        gate.append("TERMWISE_GEOM_COMPLIANCE_INSUFFICIENT_FOR_MODEL")
    if phase_dependent:
        gate.append("TERMWISE_GEOM_COMPLIANCE_PHASE_DEPENDENT")
    gate.append("ELASTIC_MODEL_REQUIRES_SCALING")
    return {
        "phase": PHASE,
        "status": "PHASE10_22B_TERMWISE_GEOMETRIC_COMPLIANCE_EXTRACTED",
        "physical_validation": False,
        "numeric_equivalence": False,
        "runtime_default_changed": False,
        "pressure_tabulated_geometric_allowed": False,
        "regime_source": "known_from_previous_phase_not_from_this_trace",
        "fields_exported": columns,
        "fields_missing": missing_optional,
        "formula": {
            "C_geom_accumulated": "dV_total_m3_rad / (Vi_m3_rad * dP_Pa)",
            "C_geom_incremental": "dV_increment_m3_rad / (Vi_m3_rad * dP_increment_Pa)",
            "legacy_balance": "dP = alpha*dT/k + (Vq - dV + dMl/(rho_f2*FC))/(Vi*k)",
        },
        "comparisons": {
            "C_geom_constant_10_19C": C_GEOM_CONSTANT_10_19C,
            "C_eff_constant_10_19C": C_EFF_CONSTANT_10_19C,
            "C_geom_elastic_10_20C": C_GEOM_ELASTIC_10_20C,
            "pre_opening_accumulated_ratio_to_constant_10_19C": _safe_div(
                pre_mean, C_GEOM_CONSTANT_10_19C
            ),
            "pre_opening_incremental_ratio_to_constant_10_19C": _safe_div(
                statistics["pre_opening_known"]["C_geom_incremental"]["mean"],
                C_GEOM_CONSTANT_10_19C,
            ),
            "pre_opening_accumulated_ratio_to_elastic_10_20C": _safe_div(
                pre_mean, C_GEOM_ELASTIC_10_20C
            ),
        },
        "statistics": statistics,
        "classification": {
            "C_geom_accumulated": accumulated_classification,
            "C_geom_incremental": incremental_classification,
            "phase_dependent": phase_dependent,
        },
        "gate": gate,
        "caveats": [
            "This is structural/diagnostic extraction only, not physical validation.",
            "Regimes are assigned from known Phase 10.18F/10.22A timing, not from opened in this trace.",
            "opened, sigmaTheta and margin remain absent from the same trace.",
            "No solver model or runtime default was changed.",
        ],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def _write_plots(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, bool]:
    names = [
        "termwise_geometric_compliance_vs_time.png",
        "termwise_geometric_compliance_vs_pressure.png",
        "accumulated_vs_incremental_compliance.png",
        "termwise_vs_constant_geometric.png",
        "balance_terms_for_compliance.png",
        "regime_classification_timeline.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}
    output_dir.mkdir(parents=True, exist_ok=True)
    times = [r["time_s"] for r in rows]

    def save(name: str) -> None:
        plt.figtext(0.5, 0.01, "Phase 10.22B diagnostic only", ha="center", fontsize=8)
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()

    plt.figure()
    plt.plot(times, [r["C_geom_accumulated_1_Pa"] for r in rows], label="accumulated")
    plt.plot(times, [r["C_geom_incremental_1_Pa"] for r in rows], label="incremental")
    plt.axhline(C_GEOM_CONSTANT_10_19C, color="black", linestyle="--", label="constant 10.19C")
    plt.xlabel("time_s")
    plt.ylabel("1/Pa")
    plt.legend()
    save(names[0])

    plt.figure()
    plt.scatter([r["pressure_for_correlation_Pa"] for r in rows], [r["C_geom_accumulated_1_Pa"] for r in rows], label="accumulated")
    plt.scatter([r["pressure_for_correlation_Pa"] for r in rows], [r["C_geom_incremental_1_Pa"] for r in rows], label="incremental")
    plt.xlabel("pressure_Pa")
    plt.ylabel("1/Pa")
    plt.legend()
    save(names[1])

    plt.figure()
    plt.plot([r["C_geom_accumulated_1_Pa"] for r in rows], [r["C_geom_incremental_1_Pa"] for r in rows], marker="o")
    plt.xlabel("accumulated 1/Pa")
    plt.ylabel("incremental 1/Pa")
    save(names[2])

    plt.figure()
    plt.plot(times, [r["C_geom_accumulated_1_Pa"] for r in rows], label="accumulated")
    plt.axhline(C_GEOM_CONSTANT_10_19C, color="black", linestyle="--", label="constant 10.19C")
    plt.axhline(C_GEOM_ELASTIC_10_20C, color="red", linestyle=":", label="elastic 10.20C")
    plt.xlabel("time_s")
    plt.ylabel("1/Pa")
    plt.legend()
    save(names[3])

    plt.figure()
    plt.plot(times, [r["thermal_fraction"] for r in rows], label="thermal fraction")
    plt.plot(times, [r["volumetric_fraction"] for r in rows], label="volumetric fraction")
    plt.xlabel("time_s")
    plt.ylabel("fraction")
    plt.legend()
    save(names[4])

    plt.figure()
    regime_codes = {
        "pre_opening_known": 0,
        "opening_step_known": 1,
        "between_opening_and_sink_known": 2,
        "first_sink_positive_known": 3,
        "unknown": -1,
    }
    plt.step(times, [regime_codes.get(r["regime"], -1) for r in rows], where="post")
    plt.xlabel("time_s")
    plt.ylabel("regime code")
    save(names[5])
    return {name: (output_dir / name).exists() for name in names}


def run_analysis(args: argparse.Namespace) -> dict[str, Any]:
    raw_rows, columns, missing_optional = read_trace(Path(args.trace))
    rows = add_compliance(add_missing_increments(representative_rows(raw_rows)))
    output_dir = Path(args.output_dir)
    plots = _write_plots(rows, output_dir)
    summary = summarize(rows, columns, missing_optional)
    summary["trace"] = str(args.trace)
    summary["plots"] = plots
    _write_csv(Path(args.output_csv), rows)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Phase 10.22B termwise geometric compliance from legacy balance trace."
    )
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run_analysis(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": summary["phase"],
                "status": summary["status"],
                "classification": summary["classification"],
                "gate": summary["gate"],
                "pre_opening": summary["statistics"]["pre_opening_known"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
