from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


PHASE = "10.22A"
REQUIRED_COLUMNS = {
    "time_s",
    "time_min",
    "idAnnular",
    "idLayer",
    "Vq_m3_rad",
    "dV_total_m3_rad",
    "dV_leakoff_m3_rad",
    "dMl_term_m3_rad",
    "Vi_m3_rad",
    "k_1_Pa",
    "alpha_1_C",
    "dT_C",
    "thermal_pressure_equivalent_Pa",
    "volumetric_term_dimensionless",
    "volumetric_pressure_equivalent_Pa",
    "dP_Pa",
}
OPTIONAL_COLUMNS = {
    "sigmaTheta_Pa",
    "margin_Pa",
    "opened",
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


def reconstruct_row(row: dict[str, Any]) -> dict[str, Any]:
    thermal = row["thermal_pressure_equivalent_Pa"]
    volumetric = row["volumetric_pressure_equivalent_Pa"]
    reconstructed = None if thermal is None or volumetric is None else thermal + volumetric
    residual = None if reconstructed is None or row["dP_Pa"] is None else reconstructed - row["dP_Pa"]
    return {
        **row,
        "dP_reconstructed_Pa": reconstructed,
        "dP_residual_Pa": residual,
        "thermal_fraction_of_dP": None
        if row["dP_Pa"] in (None, 0.0)
        else thermal / row["dP_Pa"],
        "volumetric_fraction_of_dP": None
        if row["dP_Pa"] in (None, 0.0)
        else volumetric / row["dP_Pa"],
    }


def representative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_time: dict[float, list[dict[str, Any]]] = {}
    for row in rows:
        if row["time_s"] is not None:
            by_time.setdefault(float(row["time_s"]), []).append(row)
    return [
        max(group, key=lambda item: item["dP_Pa"] if item["dP_Pa"] is not None else -math.inf)
        for _, group in sorted(by_time.items())
    ]


def add_increments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for row in rows:
        out = dict(row)
        for field in [
            "Vq_m3_rad",
            "dV_total_m3_rad",
            "dV_leakoff_m3_rad",
            "dMl_term_m3_rad",
            "dP_Pa",
            "thermal_pressure_equivalent_Pa",
            "volumetric_pressure_equivalent_Pa",
        ]:
            out[f"{field}_increment"] = None if previous is None else out[field] - previous[field]
        out["phase"] = "pre_opening"
        enriched.append(out)
        previous = out

    first_sink_time = next(
        (
            row["time_s"]
            for row in enriched
            if row.get("dV_leakoff_m3_rad_increment") is not None
            and row["dV_leakoff_m3_rad_increment"] > 0.0
        ),
        None,
    )
    for row in enriched:
        if first_sink_time is not None and row["time_s"] > first_sink_time:
            row["phase"] = "post_opening"
        elif first_sink_time is not None and row["time_s"] == first_sink_time:
            row["phase"] = "opening_step"
    return enriched


def add_compliance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        delta_vq = row.get("Vq_m3_rad_increment")
        delta_dv = row.get("dV_total_m3_rad_increment")
        delta_dml = row.get("dMl_term_m3_rad_increment")
        delta_leakoff = row.get("dV_leakoff_m3_rad_increment") or 0.0
        delta_dp = row.get("dP_Pa_increment")
        vi = row.get("Vi_m3_rad")
        k = row.get("k_1_Pa")
        effective_volume = None
        c_eff = None
        c_geom = None
        status = "SKIPPED_FIRST_OR_MISSING"
        if None not in (delta_vq, delta_dv, delta_dml):
            effective_volume = delta_vq - delta_dv + delta_dml - delta_leakoff
        if (
            effective_volume is not None
            and delta_dp is not None
            and delta_dp > 0.0
            and vi is not None
            and vi > 0.0
            and k is not None
        ):
            c_eff = effective_volume / (vi * delta_dp)
            c_geom = c_eff - k
            status = "OK"
        elif delta_dp is not None and delta_dp <= 0.0:
            status = "SKIPPED_NON_POSITIVE_DELTA_DP"
        enriched = dict(row)
        enriched["effective_volume_increment_m3_rad"] = effective_volume
        enriched["C_eff_termwise_1_Pa"] = c_eff
        enriched["C_geom_termwise_1_Pa"] = c_geom
        enriched["termwise_compliance_status"] = status
        out.append(enriched)
    return out


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


def classify_residual(rows: list[dict[str, Any]], tolerance_abs: float = 1.0e-5) -> str:
    residuals = [abs(row["dP_residual_Pa"]) for row in rows if row.get("dP_residual_Pa") is not None]
    if not residuals:
        return "LEGACY_BALANCE_RECONSTRUCTION_MISMATCH"
    return (
        "LEGACY_BALANCE_RECONSTRUCTION_MATCHES_DP"
        if max(residuals) <= tolerance_abs
        else "LEGACY_BALANCE_RECONSTRUCTION_MISMATCH"
    )


def classify_accumulation(rows: list[dict[str, Any]], field: str) -> str:
    values = [row[field] for row in rows if row.get(field) is not None]
    if len(values) < 2:
        return "not_available"
    diffs = [b - a for a, b in zip(values[:-1], values[1:])]
    if all(diff >= -1.0e-12 for diff in diffs) and max(values) > min(values):
        return "accumulated_non_decreasing"
    if any(abs(diff) > 1.0e-12 for diff in diffs):
        return "state_value_variable"
    return "constant_or_not_available"


def summarize(
    all_rows: list[dict[str, Any]],
    analysis_rows: list[dict[str, Any]],
    columns: list[str],
    missing_optional: list[str],
) -> dict[str, Any]:
    residual_stats = _stats(all_rows, "dP_residual_Pa")
    residual_classification = classify_residual(all_rows)
    first_sink = next(
        (
            row["time_s"]
            for row in analysis_rows
            if row.get("dV_leakoff_m3_rad_increment") is not None
            and row["dV_leakoff_m3_rad_increment"] > 0.0
        ),
        None,
    )
    first_opened = next((row["time_s"] for row in analysis_rows if row.get("opened") is True), None)
    trace_completeness = (
        "LEGACY_BALANCE_TRACE_COMPLETE" if not missing_optional else "LEGACY_BALANCE_TRACE_PARTIAL"
    )
    sign_classification = (
        "LEGACY_BALANCE_TRACE_SIGN_CONFIRMED"
        if residual_classification == "LEGACY_BALANCE_RECONSTRUCTION_MATCHES_DP"
        else "LEGACY_BALANCE_TRACE_SIGN_AMBIGUOUS"
    )
    pre = [row for row in analysis_rows if row["phase"] == "pre_opening"]
    opening = [row for row in analysis_rows if row["phase"] == "opening_step"]
    post = [row for row in analysis_rows if row["phase"] == "post_opening"]
    recommendation = [
        "PRESSURE_TABULATED_CAN_BE_RETRIED_WITH_TERMWISE_COMPLIANCE"
        if residual_classification == "LEGACY_BALANCE_RECONSTRUCTION_MATCHES_DP"
        else "LEGACY_TERMWISE_TRACE_REQUIRED_AGAIN"
    ]
    if "opened" in missing_optional:
        recommendation.append("LEGACY_TERMWISE_TRACE_REQUIRED_AGAIN")
    return {
        "phase": PHASE,
        "status": "PHASE10_22A_LEGACY_BALANCE_TERMS_AUDIT_COMPLETE",
        "classifications": [
            trace_completeness,
            sign_classification,
            residual_classification,
        ],
        "next_phase_recommendation": recommendation,
        "physical_validation": False,
        "numeric_equivalence": False,
        "runtime_default_changed": False,
        "formula_source_location": "legance/LOT_Tese/src/apb_code/APB1da.cpp active LOT branch near dP assignment",
        "formula_exact_text": "double dP = (alpha * dT - (-Vq + dV - dMl/(rho_f2 * FC))) / Vi) / k;",
        "fields_exported": columns,
        "fields_missing": missing_optional,
        "residual": {
            "max_abs_Pa": residual_stats["max"],
            "mean_abs_Pa": _stats(
                [{"abs_residual": abs(row["dP_residual_Pa"])} for row in all_rows if row.get("dP_residual_Pa") is not None],
                "abs_residual",
            )["mean"],
            "classification": residual_classification,
        },
        "timing": {
            "first_opened_time_s": first_opened,
            "first_sink_positive_time_s": first_sink,
            "legacy_breakdown_time_s": first_opened if first_opened is not None else first_sink,
        },
        "accumulation": {
            "dP": classify_accumulation(analysis_rows, "dP_Pa"),
            "Vq": classify_accumulation(analysis_rows, "Vq_m3_rad"),
            "dV": classify_accumulation(analysis_rows, "dV_total_m3_rad"),
            "dMl_term": classify_accumulation(analysis_rows, "dMl_term_m3_rad"),
            "dV_leakoff": classify_accumulation(analysis_rows, "dV_leakoff_m3_rad"),
        },
        "statistics": {
            "pre_opening": {
                "C_eff_termwise": _stats(pre, "C_eff_termwise_1_Pa"),
                "C_geom_termwise": _stats(pre, "C_geom_termwise_1_Pa"),
                "thermal_fraction": _stats(pre, "thermal_fraction_of_dP"),
                "volumetric_fraction": _stats(pre, "volumetric_fraction_of_dP"),
            },
            "opening_step": {
                "C_eff_termwise": _stats(opening, "C_eff_termwise_1_Pa"),
                "C_geom_termwise": _stats(opening, "C_geom_termwise_1_Pa"),
            },
            "post_opening": {
                "C_eff_termwise": _stats(post, "C_eff_termwise_1_Pa"),
                "C_geom_termwise": _stats(post, "C_geom_termwise_1_Pa"),
            },
            "all_representative_rows": {
                "thermal_pressure_equivalent": _stats(analysis_rows, "thermal_pressure_equivalent_Pa"),
                "volumetric_pressure_equivalent": _stats(analysis_rows, "volumetric_pressure_equivalent_Pa"),
            },
        },
        "notes": [
            "Trace was generated by temporary LOT_Tese instrumentation and the legacy source was restored before commit.",
            "Representative rows select the maximum dP per time from the instrumented nonlinear iteration trace.",
            "Missing opened/sigmaTheta fields keep the trace partial; sink timing is inferred from dV_leakoff increments.",
            "This is an audit artifact, not physical validation and not a runtime model.",
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


def _write_plots(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, bool]:
    names = [
        "balance_terms_pressure_equivalent_vs_time.png",
        "dp_reconstruction_residual.png",
        "termwise_compliance_vs_time.png",
        "termwise_compliance_vs_pressure.png",
        "thermal_vs_volumetric_contribution.png",
        "opening_and_sink_timing.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}
    output_dir.mkdir(parents=True, exist_ok=True)
    times = [row["time_s"] for row in rows]

    def save(name: str) -> None:
        plt.figtext(0.5, 0.01, "Phase 10.22A diagnostic only", ha="center", fontsize=8)
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()

    plt.figure()
    plt.plot(times, [row["thermal_pressure_equivalent_Pa"] for row in rows], label="thermal")
    plt.plot(times, [row["volumetric_pressure_equivalent_Pa"] for row in rows], label="volumetric")
    plt.plot(times, [row["dP_Pa"] for row in rows], label="dP")
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    plt.legend()
    save("balance_terms_pressure_equivalent_vs_time.png")

    plt.figure()
    plt.plot(times, [row["dP_residual_Pa"] for row in rows])
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    save("dp_reconstruction_residual.png")

    plt.figure()
    plt.plot(times, [row["C_eff_termwise_1_Pa"] for row in rows], label="C_eff")
    plt.plot(times, [row["C_geom_termwise_1_Pa"] for row in rows], label="C_geom")
    plt.yscale("log")
    plt.xlabel("time_s")
    plt.ylabel("1/Pa")
    plt.legend()
    save("termwise_compliance_vs_time.png")

    plt.figure()
    plt.scatter([row["dP_Pa"] for row in rows], [row["C_eff_termwise_1_Pa"] for row in rows])
    plt.yscale("log")
    plt.xlabel("dP_Pa")
    plt.ylabel("C_eff 1/Pa")
    save("termwise_compliance_vs_pressure.png")

    plt.figure()
    plt.plot(times, [row["thermal_fraction_of_dP"] for row in rows], label="thermal/dP")
    plt.plot(times, [row["volumetric_fraction_of_dP"] for row in rows], label="volumetric/dP")
    plt.xlabel("time_s")
    plt.ylabel("fraction")
    plt.legend()
    save("thermal_vs_volumetric_contribution.png")

    plt.figure()
    plt.plot(times, [row["dV_leakoff_m3_rad"] for row in rows], label="dV_leakoff")
    plt.xlabel("time_s")
    plt.ylabel("m3/rad")
    plt.legend()
    save("opening_and_sink_timing.png")
    return {name: (output_dir / name).exists() for name in names}


def run_analysis(args: argparse.Namespace) -> dict[str, Any]:
    raw_rows, columns, missing_optional = read_trace(Path(args.trace))
    reconstructed = [reconstruct_row(row) for row in raw_rows]
    representative = add_compliance(add_increments(representative_rows(reconstructed)))
    output_dir = Path(args.output_dir)
    plots = _write_plots(representative, output_dir)
    summary = summarize(reconstructed, representative, columns, missing_optional)
    summary["trace"] = str(args.trace)
    summary["plots"] = plots
    _write_csv(Path(args.output_csv), representative)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "legacy_balance_terms_trace_metadata.json").write_text(
        json.dumps(
            {
                "phase": PHASE,
                "fields_exported": columns,
                "fields_missing": missing_optional,
                "formula_source_location": summary["formula_source_location"],
                "formula_exact_text": summary["formula_exact_text"],
                "unit_conventions": {
                    "time_min": "min",
                    "time_s": "s",
                    "volumes": "m3/rad",
                    "pressure": "Pa",
                    "compressibility": "1/Pa",
                    "temperature": "degC",
                    "Qinj_m3_rad_min": "m3/min/rad",
                },
                "notes": summary["notes"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Phase 10.22A LOT_Tese pressure-balance term trace."
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
                "classifications": summary["classifications"],
                "next_phase_recommendation": summary["next_phase_recommendation"],
                "residual": summary["residual"],
                "timing": summary["timing"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
