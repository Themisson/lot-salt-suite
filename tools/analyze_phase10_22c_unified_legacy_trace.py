from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


PHASE = "10.22C"

REQUIRED_COLUMNS = {
    "record_type",
    "step",
    "time_min",
    "time_s",
    "idAnnular",
    "idLayer",
    "Vi_m3_rad",
    "Vq_m3_rad",
    "dV_total_m3_rad",
    "dV_leakoff_m3_rad",
    "dMl_term_m3_rad",
    "thermal_pressure_equivalent_Pa",
    "volumetric_pressure_equivalent_Pa",
    "dP_Pa",
    "pw_Pa",
    "sigmaTheta_Pa",
    "margin_Pa",
    "opened",
    "sink_positive",
}

BOOL_COLUMNS = {
    "opened",
    "opened_before_step",
    "opened_after_step",
    "fracture_started_this_step",
    "sink_positive",
    "sink_started_this_step",
}


def _normalize_trace_text(text: str) -> str:
    return text.replace("`n", "\n").replace("\\n", "\n")


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


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0.0:
        return None
    return num / den


def read_trace(path: Path) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = _normalize_trace_text(path.read_text(encoding="utf-8", errors="replace"))
    reader = csv.DictReader(text.splitlines())
    columns = reader.fieldnames or []
    missing = sorted(REQUIRED_COLUMNS - set(columns))
    if missing:
        raise ValueError(f"trace missing required columns: {missing}")

    rows: list[dict[str, Any]] = []
    for raw in reader:
        row: dict[str, Any] = dict(raw)
        for key in columns:
            if key in BOOL_COLUMNS:
                row[key] = _bool(raw.get(key))
            elif key != "record_type":
                row[key] = _float(raw.get(key))
        rows.append(row)
    missing_optional = sorted(key for key in REQUIRED_COLUMNS if all(row.get(key) is None for row in rows))
    return rows, columns, missing_optional


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        out["C_geom_accumulated_1_Pa"] = _safe_div(
            out.get("dV_total_m3_rad"),
            (out.get("Vi_m3_rad") or 0.0) * (out.get("dP_Pa") or 0.0),
        )
        out["C_geom_incremental_1_Pa"] = _safe_div(
            out.get("dV_increment_m3_rad"),
            (out.get("Vi_m3_rad") or 0.0) * (out.get("dP_increment_Pa") or 0.0),
        )
        out["dP_reconstructed_Pa"] = (
            None
            if out.get("thermal_pressure_equivalent_Pa") is None
            or out.get("volumetric_pressure_equivalent_Pa") is None
            else out["thermal_pressure_equivalent_Pa"] + out["volumetric_pressure_equivalent_Pa"]
        )
        out["dP_residual_Pa"] = (
            None
            if out.get("dP_reconstructed_Pa") is None or out.get("dP_Pa") is None
            else out["dP_reconstructed_Pa"] - out["dP_Pa"]
        )
        enriched.append(out)
    return enriched


def _first_row(rows: list[dict[str, Any]], predicate: Any) -> dict[str, Any] | None:
    candidates = [row for row in rows if predicate(row) and row.get("time_s") is not None]
    return min(candidates, key=lambda row: (row["time_s"], row.get("step") or 0.0)) if candidates else None


def _stats(values: list[float]) -> dict[str, float | None]:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return {"count": 0, "mean": None, "median": None, "std": None, "cv": None}
    avg = mean(finite)
    std = pstdev(finite) if len(finite) > 1 else 0.0
    return {
        "count": len(finite),
        "mean": avg,
        "median": median(finite),
        "std": std,
        "cv": None if avg == 0.0 else std / abs(avg),
    }


def analyze(rows: list[dict[str, Any]], missing_optional: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = enrich_rows(rows)
    balance_rows = [row for row in rows if row.get("record_type") == "balance"]
    opening_rows = [row for row in rows if row.get("record_type") == "opening"]
    first_open = _first_row(rows, lambda row: row.get("opened") is True or (row.get("margin_Pa") or -math.inf) > 0)
    first_sink = _first_row(rows, lambda row: row.get("sink_positive") is True)
    first_fracture_started = _first_row(rows, lambda row: row.get("fracture_started_this_step") is True)

    first_open_time_s = first_open.get("time_s") if first_open else None
    first_sink_time_s = first_sink.get("time_s") if first_sink else None
    sink_delay_s = (
        None if first_open_time_s is None or first_sink_time_s is None else first_sink_time_s - first_open_time_s
    )

    if first_open and first_open.get("margin_Pa") is not None and first_open["margin_Pa"] > 0:
        opening_classification = "OPENING_CRITERION_CONFIRMED"
    else:
        opening_classification = "OPENING_TRACE_MISSING_OR_AMBIGUOUS"

    if first_open and first_sink and sink_delay_s is not None and sink_delay_s >= 0:
        phase_classification = "PHASE_DEPENDENCE_EXPLAINED_BY_SINK"
    else:
        phase_classification = "PHASE_DEPENDENCE_UNEXPLAINED"

    required_signal_fields = {"sigmaTheta_Pa", "margin_Pa", "opened", "sink_positive"}
    trace_classification = (
        "UNIFIED_TRACE_COMPLETE"
        if not (required_signal_fields & set(missing_optional)) and first_open is not None
        else "UNIFIED_TRACE_PARTIAL"
    )

    summary: dict[str, Any] = {
        "phase": PHASE,
        "trace_classification": trace_classification,
        "opening_classification": opening_classification,
        "sink_classification": "SINK_TIMING_CONFIRMED" if first_sink else "SINK_TIMING_MISSING",
        "phase_dependence_classification": phase_classification,
        "gate": (
            "LEGACY_OPENING_AND_SINK_TRACE_READY_FOR_REVIEW"
            if trace_classification == "UNIFIED_TRACE_COMPLETE"
            else "LEGACY_OPENING_TRACE_STILL_REQUIRED"
        ),
        "row_counts": {
            "total": len(rows),
            "balance": len(balance_rows),
            "opening": len(opening_rows),
        },
        "first_opened_time_s": first_open_time_s,
        "first_opened_step": first_open.get("step") if first_open else None,
        "first_pw_Pa": first_open.get("pw_Pa") if first_open else None,
        "first_sigmaTheta_Pa": first_open.get("sigmaTheta_Pa") if first_open else None,
        "first_margin_Pa": first_open.get("margin_Pa") if first_open else None,
        "first_sink_positive_time_s": first_sink_time_s,
        "first_sink_positive_step": first_sink.get("step") if first_sink else None,
        "sink_delay_s": sink_delay_s,
        "first_fracture_started_time_s": first_fracture_started.get("time_s") if first_fracture_started else None,
        "missing_fields": missing_optional,
        "concept_map": {
            "pw_Pa": "legacy pi + dP",
            "sigmaTheta_Pa": "legacy -getSigmaTheta()",
            "margin_Pa": "pw_Pa - sigmaTheta_Pa",
            "opened": "legacy pw > sigmaTheta",
            "sink_positive": "dV_leakoff_m3_rad > 0",
        },
        "compliance": {
            "accumulated": _stats(
                [
                    row["C_geom_accumulated_1_Pa"]
                    for row in rows
                    if row.get("C_geom_accumulated_1_Pa") is not None
                ]
            ),
            "incremental": _stats(
                [
                    row["C_geom_incremental_1_Pa"]
                    for row in rows
                    if row.get("C_geom_incremental_1_Pa") is not None
                ]
            ),
        },
        "caveats": [
            "temporary legacy instrumentation only; no legacy edits are committed",
            "trace samples internal legacy state and does not validate modern physical equivalence",
            "C_geom incremental values can be noisy around very small pressure increments",
            "phase dependence is diagnostic, not a calibrated pressure model",
        ],
    }
    return rows, summary


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_plots(rows: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        for name in [
            "pressure_sigmaTheta_margin_vs_time.png",
            "opening_and_sink_timing.png",
            "balance_terms_by_regime.png",
            "dP_increment_by_regime.png",
            "dV_dMl_leakoff_by_regime.png",
            "termwise_compliance_by_regime.png",
        ]:
            (output_dir / name).write_text("matplotlib unavailable\n", encoding="utf-8")
        return

    def xy(field: str) -> tuple[list[float], list[float]]:
        pairs = [(row.get("time_s"), row.get(field)) for row in rows if row.get(field) is not None]
        return [float(a) for a, _ in pairs], [float(b) for _, b in pairs]

    plots = [
        ("pressure_sigmaTheta_margin_vs_time.png", ["pw_Pa", "sigmaTheta_Pa", "margin_Pa"]),
        ("balance_terms_by_regime.png", ["thermal_pressure_equivalent_Pa", "volumetric_pressure_equivalent_Pa"]),
        ("dP_increment_by_regime.png", ["dP_increment_Pa"]),
        ("dV_dMl_leakoff_by_regime.png", ["dV_total_m3_rad", "dMl_term_m3_rad", "dV_leakoff_m3_rad"]),
        ("termwise_compliance_by_regime.png", ["C_geom_accumulated_1_Pa", "C_geom_incremental_1_Pa"]),
    ]
    for filename, fields in plots:
        plt.figure(figsize=(8, 4.5))
        for field in fields:
            xs, ys = xy(field)
            if xs:
                plt.plot(xs, ys, label=field)
        plt.xlabel("time_s")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / filename)
        plt.close()

    plt.figure(figsize=(8, 2.8))
    xs, opened = xy("opened")
    sink_xs, sink = xy("sink_positive")
    if xs:
        plt.step(xs, opened, label="opened")
    if sink:
        plt.step(sink_xs, sink, label="sink_positive")
    plt.xlabel("time_s")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "opening_and_sink_timing.png")
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Phase 10.22C unified legacy trace.")
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    raw_rows, _, missing_optional = read_trace(args.trace)
    rows, summary = analyze(raw_rows, missing_optional)
    write_csv(rows, args.output_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_plots(rows, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
