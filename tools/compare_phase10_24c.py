from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.24C"
LEGACY_FIRST_OPENED_TIME_S = 510.0
LEGACY_FIRST_SINK_POSITIVE_TIME_S = 540.0
LEGACY_PRESSURE_AT_OPENING_PA = 66769500.0


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


def _flag(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() in {"1", "true", "yes"}


def _values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [value for row in rows if (value := _float(row.get(field))) is not None]


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _last_value(rows: list[dict[str, str]], field: str) -> float | None:
    for row in reversed(rows):
        value = _float(row.get(field))
        if value is not None:
            return value
    return None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


def _first_flag_row(rows: list[dict[str, str]], field: str) -> dict[str, str] | None:
    for row in rows:
        if _flag(row, field):
            return row
    return None


def _first_positive_sink_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        fracture = _float(row.get("fracture_sink_applied_m3"))
        leakoff = _float(row.get("leakoff_sink_applied_m3"))
        if fracture is None:
            fracture = _float(row.get("balance_fracture_volume_increment_m3"))
        if leakoff is None:
            leakoff = _float(row.get("balance_leakoff_volume_increment_m3"))
        if (fracture or 0.0) + (leakoff or 0.0) > 0.0:
            return row
    return None


def _legacy_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "opened")
    sink = _first_flag_row(rows, "sink_positive")
    return {
        "first_opened_time_s": _float(opening.get("time_s")) if opening else LEGACY_FIRST_OPENED_TIME_S,
        "first_sink_positive_time_s": _float(sink.get("time_s")) if sink else LEGACY_FIRST_SINK_POSITIVE_TIME_S,
        "pressure_at_opening_Pa": _float(opening.get("pw_Pa")) if opening else LEGACY_PRESSURE_AT_OPENING_PA,
        "max_pressure_Pa": _max(rows, "pw_Pa"),
        "final_pressure_Pa": _last_value(rows, "pw_Pa"),
    }


def _modern_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    opening = _first_flag_row(rows, "fracture_started_this_step")
    if opening is None:
        opening = _first_flag_row(rows, "fracture_initiated")
    sink = _first_positive_sink_row(rows)
    opening_time = None if opening is None else _float(opening.get("time_s"))
    sink_time = None if sink is None else _float(sink.get("time_s"))
    opening_pressure = None
    if opening is not None:
        opening_pressure = _float(opening.get("fracture_initiation_pressure_Pa"))
        if opening_pressure is None or opening_pressure == 0.0:
            opening_pressure = _float(opening.get("wellbore_pressure_Pa"))
    return {
        "fracture_initiation_time_s": opening_time,
        "first_sink_positive_time_s": sink_time,
        "sink_delay_s": None
        if opening_time is None or sink_time is None
        else sink_time - opening_time,
        "pressure_at_opening_Pa": opening_pressure,
        "max_pressure_Pa": _max(rows, "wellbore_pressure_Pa"),
        "final_pressure_Pa": _last_value(rows, "wellbore_pressure_Pa"),
    }


def _abs_close(value: float | None, target: float, tolerance: float) -> bool:
    return value is not None and abs(value - target) <= tolerance


def classify(metrics: dict[str, Any]) -> str:
    peak_ok = (
        metrics["relative_error_max_pressure"] is not None
        and abs(metrics["relative_error_max_pressure"]) <= 0.10
    )
    opening_ok = _abs_close(metrics["opening_time_error_s"], 0.0, 60.0)
    sink_ok = _abs_close(metrics["sink_delay_error_s"], 0.0, 1.0e-9)
    shutin_bad = (
        metrics["final_pressure_relative_error"] is not None
        and abs(metrics["final_pressure_relative_error"]) > 0.10
    )
    if peak_ok and opening_ok and sink_ok and shutin_bad:
        return "SIGMA_THETA_TIMESERIES_SHUTIN_MISMATCH"
    if peak_ok and opening_ok and sink_ok:
        return "SIGMA_THETA_TIMESERIES_DIAGNOSTIC_EFFECTIVE"
    if peak_ok and not opening_ok:
        return "SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED"
    if opening_ok and not peak_ok:
        return "SIGMA_THETA_TIMESERIES_OPENING_OK_PRESSURE_SHIFTED"
    if (
        metrics["relative_error_max_pressure"] is None
        or metrics["modern_fracture_initiation_time_s"] is None
        or metrics["modern_sink_delay_s"] is None
    ):
        return "SIGMA_THETA_TIMESERIES_INCONCLUSIVE"
    return "SIGMA_THETA_TIMESERIES_NO_IMPROVEMENT"


def recommend_next_model(classification: str) -> str:
    if classification == "SIGMA_THETA_TIMESERIES_DIAGNOSTIC_EFFECTIVE":
        return "NEXT_MODEL_SALT_WALL_STRESS_RUNTIME"
    if classification == "SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED":
        return "NEXT_MODEL_SIGMA_THETA_TIMESERIES_NEEDS_BETTER_SOURCE"
    if classification == "SIGMA_THETA_TIMESERIES_OPENING_OK_PRESSURE_SHIFTED":
        return "NEXT_MODEL_COMPLIANCE_REVISIT_REQUIRED"
    if classification == "SIGMA_THETA_TIMESERIES_SHUTIN_MISMATCH":
        return "NEXT_MODEL_THERMAL_EXPLICIT_REQUIRED"
    if classification == "SIGMA_THETA_TIMESERIES_NO_IMPROVEMENT":
        return "NEXT_MODEL_SIGMA_THETA_TIMESERIES_NEEDS_BETTER_SOURCE"
    return "NEXT_MODEL_INCONCLUSIVE"


def _series(rows: list[dict[str, str]], pressure_field: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for row in rows:
        time_s = _float(row.get("time_s"))
        pressure = _float(row.get(pressure_field))
        if time_s is not None and pressure is not None:
            points.append((time_s, pressure))
    return points


def _volume_pressure_series(
    rows: list[dict[str, str]], pressure_field: str
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for row in rows:
        volume = _float(row.get("injected_volume_m3"))
        pressure = _float(row.get(pressure_field))
        if volume is not None and pressure is not None:
            points.append((volume, pressure))
    return points


def _plot_outputs(
    output_dir: Path,
    legacy_rows: list[dict[str, str]],
    modern_rows: list[dict[str, str]],
    optional_rows: dict[str, list[dict[str, str]]],
    metrics: dict[str, Any],
) -> dict[str, bool]:
    names = [
        "pressure_vs_time_sigma_theta_timeseries.png",
        "injected_volume_vs_pressure_sigma_theta_timeseries.png",
        "opening_timing_comparison.png",
        "sink_timing_comparison.png",
        "model_comparison_pressure.png",
        "shutin_pressure_comparison.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, bool] = {}

    def save(name: str) -> None:
        plt.figtext(
            0.5,
            0.01,
            "Phase 10.24C - DIAGNOSTIC ONLY - not physical validation",
            ha="center",
            fontsize=8,
        )
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()
        generated[name] = True

    plt.figure()
    for label, points in {
        "legacy": _series(legacy_rows, "pw_Pa"),
        "sigma_theta_time_series": _series(modern_rows, "wellbore_pressure_Pa"),
        **{
            label: _series(rows, "wellbore_pressure_Pa")
            for label, rows in optional_rows.items()
        },
    }.items():
        if points:
            plt.plot([p[0] for p in points], [p[1] for p in points], label=label)
    plt.xlabel("time_s")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.24C pressure vs time")
    plt.legend()
    save("pressure_vs_time_sigma_theta_timeseries.png")

    plt.figure()
    for label, points in {
        "legacy": _volume_pressure_series(legacy_rows, "pw_Pa"),
        "sigma_theta_time_series": _volume_pressure_series(modern_rows, "wellbore_pressure_Pa"),
    }.items():
        if points:
            plt.plot([p[0] for p in points], [p[1] for p in points], label=label)
    plt.xlabel("injected_volume_m3")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.24C injected volume vs pressure")
    plt.legend()
    save("injected_volume_vs_pressure_sigma_theta_timeseries.png")

    plt.figure()
    plt.bar(
        ["legacy", "modern"],
        [
            metrics["legacy_first_opened_time_s"] or 0.0,
            metrics["modern_fracture_initiation_time_s"] or 0.0,
        ],
    )
    plt.ylabel("time_s")
    plt.title("Opening timing")
    save("opening_timing_comparison.png")

    plt.figure()
    plt.bar(
        ["legacy", "modern"],
        [
            metrics["legacy_sink_delay_s"] or 0.0,
            metrics["modern_sink_delay_s"] or 0.0,
        ],
    )
    plt.ylabel("delay_s")
    plt.title("Sink delay")
    save("sink_timing_comparison.png")

    plt.figure()
    labels = ["legacy", "sigma_theta_time_series"]
    values = [
        metrics["max_pressure_legacy_Pa"] or 0.0,
        metrics["max_pressure_modern_Pa"] or 0.0,
    ]
    for label, rows in optional_rows.items():
        labels.append(label)
        values.append(_max(rows, "wellbore_pressure_Pa") or 0.0)
    plt.bar(labels, values)
    plt.xticks(rotation=15, ha="right")
    plt.ylabel("max_pressure_Pa")
    plt.title("Model pressure comparison")
    save("model_comparison_pressure.png")

    plt.figure()
    plt.bar(
        ["legacy_final", "modern_final"],
        [
            metrics["final_pressure_legacy_Pa"] or 0.0,
            metrics["final_pressure_modern_Pa"] or 0.0,
        ],
    )
    plt.ylabel("pressure_Pa")
    plt.title("Shut-in/final pressure")
    save("shutin_pressure_comparison.png")

    return generated


def _load_optional(args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    optional: dict[str, list[dict[str, str]]] = {}
    if args.modern_combined_static_csv:
        optional["combined_static"] = _read_csv(Path(args.modern_combined_static_csv))
    if args.modern_next_step_csv:
        optional["next_step"] = _read_csv(Path(args.modern_next_step_csv))
    if args.modern_constant_compliance_csv:
        optional["constant_compliance"] = _read_csv(Path(args.modern_constant_compliance_csv))
    return optional


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    optional_rows = _load_optional(args)
    legacy = _legacy_metrics(legacy_rows)
    modern = _modern_metrics(modern_rows)
    legacy_sink_delay = None
    if legacy["first_opened_time_s"] is not None and legacy["first_sink_positive_time_s"] is not None:
        legacy_sink_delay = legacy["first_sink_positive_time_s"] - legacy["first_opened_time_s"]

    metrics: dict[str, Any] = {
        "max_pressure_legacy_Pa": legacy["max_pressure_Pa"],
        "max_pressure_modern_Pa": modern["max_pressure_Pa"],
        "relative_error_max_pressure": _relative_error(
            legacy["max_pressure_Pa"], modern["max_pressure_Pa"]
        ),
        "legacy_first_opened_time_s": legacy["first_opened_time_s"],
        "modern_fracture_initiation_time_s": modern["fracture_initiation_time_s"],
        "opening_time_error_s": None
        if legacy["first_opened_time_s"] is None or modern["fracture_initiation_time_s"] is None
        else modern["fracture_initiation_time_s"] - legacy["first_opened_time_s"],
        "legacy_first_sink_positive_time_s": legacy["first_sink_positive_time_s"],
        "modern_first_sink_positive_time_s": modern["first_sink_positive_time_s"],
        "legacy_sink_delay_s": legacy_sink_delay,
        "modern_sink_delay_s": modern["sink_delay_s"],
        "sink_delay_error_s": None
        if legacy_sink_delay is None or modern["sink_delay_s"] is None
        else modern["sink_delay_s"] - legacy_sink_delay,
        "legacy_pressure_at_opening_Pa": legacy["pressure_at_opening_Pa"],
        "modern_pressure_at_opening_Pa": modern["pressure_at_opening_Pa"],
        "pressure_at_opening_error_Pa": None
        if legacy["pressure_at_opening_Pa"] is None or modern["pressure_at_opening_Pa"] is None
        else modern["pressure_at_opening_Pa"] - legacy["pressure_at_opening_Pa"],
        "pressure_at_opening_relative_error": _relative_error(
            legacy["pressure_at_opening_Pa"], modern["pressure_at_opening_Pa"]
        ),
        "final_pressure_legacy_Pa": legacy["final_pressure_Pa"],
        "final_pressure_modern_Pa": modern["final_pressure_Pa"],
        "final_pressure_error_Pa": None
        if legacy["final_pressure_Pa"] is None or modern["final_pressure_Pa"] is None
        else modern["final_pressure_Pa"] - legacy["final_pressure_Pa"],
        "final_pressure_relative_error": _relative_error(
            legacy["final_pressure_Pa"], modern["final_pressure_Pa"]
        ),
    }
    classification = classify(metrics)
    next_model = recommend_next_model(classification)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plots = _plot_outputs(output_dir, legacy_rows, modern_rows, optional_rows, metrics)

    summary_row = {
        "phase": PHASE,
        "classification": classification,
        "next_model_recommendation": next_model,
        **metrics,
    }
    with (output_dir / "phase10_24c_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_row))
        writer.writeheader()
        writer.writerow(summary_row)

    metadata = {
        "phase": PHASE,
        "classification": classification,
        "next_model_recommendation": next_model,
        "physical_validation": False,
        "runtime_default_changed": False,
        "metrics": metrics,
        "plots": plots,
        "optional_comparisons": sorted(optional_rows),
        "caveats": [
            "Diagnostic only; not physical validation.",
            "The sigma_theta_time_series source is a minimal legacy-derived fixture.",
            "No SaltWallStressDiagnostics runtime provider is connected.",
            "No Zamora, pressure_tabulated_geometric or new compliance model was implemented.",
        ],
    }
    (output_dir / "phase10_24c_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnose Phase 10.24C BUZ67D sigma-theta time-series criterion."
    )
    parser.add_argument("--legacy-csv", required=True, type=Path)
    parser.add_argument("--modern-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--modern-combined-static-csv", type=Path, default=None)
    parser.add_argument("--modern-next-step-csv", type=Path, default=None)
    parser.add_argument("--modern-constant-compliance-csv", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    metadata = run_comparison(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": metadata["phase"],
                "classification": metadata["classification"],
                "next_model_recommendation": metadata["next_model_recommendation"],
                "metrics": metadata["metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
