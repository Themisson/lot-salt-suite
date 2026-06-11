from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.23B"
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


def _values(rows: list[dict[str, str]], field: str) -> list[float]:
    return [value for row in rows if (value := _float(row.get(field))) is not None]


def _flag(row: dict[str, str], field: str) -> bool:
    return row.get(field, "").strip().lower() in {"1", "true", "yes"}


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


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


def _last_value(rows: list[dict[str, str]], field: str) -> float | None:
    for row in reversed(rows):
        value = _float(row.get(field))
        if value is not None:
            return value
    return None


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


def _classify(metrics: dict[str, Any]) -> str:
    rel = metrics["relative_error_max_pressure"]
    opening_time = metrics["modern_fracture_initiation_time_s"]
    sink_delay = metrics["modern_sink_delay_s"]
    pressure_ok = rel is not None and abs(rel) <= 0.10
    opening_ok = (
        opening_time is not None
        and abs(opening_time - LEGACY_FIRST_OPENED_TIME_S) <= 60.0
    )
    sink_ok = sink_delay is not None and abs(sink_delay - 30.0) <= 1.0e-9
    if pressure_ok and opening_ok and sink_ok:
        return "COMBINED_DIAGNOSTIC_EFFECTIVE"
    if pressure_ok and not opening_ok:
        return "COMBINED_DIAGNOSTIC_PRESSURE_OK_OPENING_SHIFTED"
    if opening_ok and not pressure_ok:
        return "COMBINED_DIAGNOSTIC_OPENING_OK_PRESSURE_SHIFTED"
    if pressure_ok or opening_ok or sink_ok:
        return "COMBINED_DIAGNOSTIC_PARTIAL"
    if rel is None or opening_time is None or sink_delay is None:
        return "COMBINED_DIAGNOSTIC_INCONCLUSIVE"
    return "COMBINED_DIAGNOSTIC_NO_IMPROVEMENT"


def _series_points(rows: list[dict[str, str]], pressure_field: str) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    for row in rows:
        time_s = _float(row.get("time_s"))
        pressure = _float(row.get(pressure_field))
        volume = _float(row.get("injected_volume_m3"))
        if time_s is None or pressure is None:
            continue
        points.append({"time_s": time_s, "pressure_Pa": pressure, "volume_m3": volume or 0.0})
    return points


def _plot_outputs(
    output_dir: Path,
    legacy_rows: list[dict[str, str]],
    modern_rows: list[dict[str, str]],
    optional_rows: dict[str, list[dict[str, str]]],
    metrics: dict[str, Any],
) -> dict[str, bool]:
    names = [
        "pressure_vs_time_combined.png",
        "injected_volume_vs_pressure_combined.png",
        "opening_and_sink_timing_combined.png",
        "model_comparison_pressure.png",
        "sink_applied_vs_time_combined.png",
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
            "Phase 10.23B - DIAGNOSTIC ONLY - not physical validation",
            ha="center",
            fontsize=8,
        )
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()
        generated[name] = True

    series = [
        ("legacy", _series_points(legacy_rows, "pw_Pa")),
        ("combined", _series_points(modern_rows, "wellbore_pressure_Pa")),
    ]
    for label, rows in optional_rows.items():
        series.append((label, _series_points(rows, "wellbore_pressure_Pa")))

    plt.figure()
    for label, points in series:
        if points:
            plt.plot([p["time_s"] for p in points], [p["pressure_Pa"] for p in points], label=label)
    plt.xlabel("time_s")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.23B pressure vs time")
    plt.legend()
    save("pressure_vs_time_combined.png")

    plt.figure()
    for label, points in series:
        if points:
            plt.plot([p["volume_m3"] for p in points], [p["pressure_Pa"] for p in points], label=label)
    plt.xlabel("injected_volume_m3")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.23B injected volume vs pressure")
    plt.legend()
    save("injected_volume_vs_pressure_combined.png")

    plt.figure()
    labels = ["legacy_open", "legacy_sink", "modern_open", "modern_sink"]
    values = [
        LEGACY_FIRST_OPENED_TIME_S,
        LEGACY_FIRST_SINK_POSITIVE_TIME_S,
        metrics["modern_fracture_initiation_time_s"] or 0.0,
        metrics["modern_first_sink_positive_time_s"] or 0.0,
    ]
    plt.bar(labels, values)
    plt.ylabel("time_s")
    plt.title("Phase 10.23B opening and sink timing")
    save("opening_and_sink_timing_combined.png")

    plt.figure()
    labels = ["legacy", "combined"]
    values = [metrics["max_pressure_legacy_Pa"] or 0.0, metrics["max_pressure_modern_Pa"] or 0.0]
    for label, rows in optional_rows.items():
        labels.append(label)
        values.append(_max(rows, "wellbore_pressure_Pa") or 0.0)
    plt.bar(labels, values)
    plt.ylabel("max_pressure_Pa")
    plt.title("Phase 10.23B model comparison")
    save("model_comparison_pressure.png")

    plt.figure()
    sink_points = []
    for row in modern_rows:
        time_s = _float(row.get("time_s"))
        fracture = _float(row.get("fracture_sink_applied_m3")) or 0.0
        leakoff = _float(row.get("leakoff_sink_applied_m3")) or 0.0
        if time_s is not None:
            sink_points.append((time_s, fracture + leakoff))
    if sink_points:
        plt.plot([p[0] for p in sink_points], [p[1] for p in sink_points], label="combined")
    plt.xlabel("time_s")
    plt.ylabel("sink_applied_m3")
    plt.title("Phase 10.23B sink applied vs time")
    plt.legend()
    save("sink_applied_vs_time_combined.png")

    return generated


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    optional_rows = {
        "constant_compliance": _read_csv(Path(args.modern_constant_compliance_csv))
        if args.modern_constant_compliance_csv
        else [],
        "elastic_compliance": _read_csv(Path(args.modern_elastic_compliance_csv))
        if args.modern_elastic_compliance_csv
        else [],
        "next_step": _read_csv(Path(args.modern_next_step_csv))
        if args.modern_next_step_csv
        else [],
    }
    optional_rows = {key: value for key, value in optional_rows.items() if value}

    legacy_max = _max(legacy_rows, "pw_Pa")
    modern = _modern_metrics(modern_rows)
    metrics: dict[str, Any] = {
        "max_pressure_legacy_Pa": legacy_max,
        "max_pressure_modern_Pa": modern["max_pressure_Pa"],
        "relative_error_max_pressure": _relative_error(legacy_max, modern["max_pressure_Pa"]),
        "legacy_first_opened_time_s": LEGACY_FIRST_OPENED_TIME_S,
        "legacy_first_sink_positive_time_s": LEGACY_FIRST_SINK_POSITIVE_TIME_S,
        "modern_fracture_initiation_time_s": modern["fracture_initiation_time_s"],
        "modern_first_sink_positive_time_s": modern["first_sink_positive_time_s"],
        "modern_sink_delay_s": modern["sink_delay_s"],
        "pressure_at_opening_legacy_Pa": LEGACY_PRESSURE_AT_OPENING_PA,
        "pressure_at_opening_modern_Pa": modern["pressure_at_opening_Pa"],
        "final_pressure_legacy_Pa": _last_value(legacy_rows, "pw_Pa"),
        "final_pressure_modern_Pa": modern["final_pressure_Pa"],
    }
    classification = _classify(metrics)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plots = _plot_outputs(output_dir, legacy_rows, modern_rows, optional_rows, metrics)
    summary_row = {"phase": PHASE, "classification": classification, **metrics}
    with (output_dir / "phase10_23b_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_row))
        writer.writeheader()
        writer.writerow(summary_row)
    metadata = {
        "phase": PHASE,
        "classification": classification,
        "physical_validation": False,
        "runtime_default_changed": False,
        "configuration": {
            "compliance": "constant_geometric_phase10_19c",
            "sigma_theta_static_Pa": 66666600.0,
            "sink_timing": "next_step",
        },
        "metrics": metrics,
        "plots": plots,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "sigma_theta_static is a fixed Phase 10.22C proxy, not runtime salt stress.",
            "constant_geometric is an inferred diagnostic compliance, not a mechanics model.",
            "sink_timing next_step is opt-in and does not change default runtime behavior.",
        ],
    }
    (output_dir / "phase10_23b_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.23B BUZ67D combined compliance/sigma-theta/next-step diagnostic."
    )
    parser.add_argument("--legacy-csv", required=True, type=Path)
    parser.add_argument("--modern-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--modern-constant-compliance-csv", type=Path, default=None)
    parser.add_argument("--modern-elastic-compliance-csv", type=Path, default=None)
    parser.add_argument("--modern-next-step-csv", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    metadata = run_comparison(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": metadata["phase"],
                "classification": metadata["classification"],
                "metrics": metadata["metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
