from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


CAVEATS = [
    "dP legacy semantic meaning not confirmed as net_pressure_Pa",
    "Layer legacy 1-based not mapped to modern indices",
    "sigmaTheta/pw/margin/opened not available",
    "This is a structural diagnostic, not physical validation",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _finite_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _available_fields(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    fields = rows[0].keys()
    available: list[str] = []
    for field in fields:
        if any(row.get(field) not in {None, ""} for row in rows):
            available.append(field)
    return available


def _unique_sorted(values: list[float]) -> list[float]:
    return sorted(set(values))


def _mean_dt(times: list[float]) -> float | None:
    unique = _unique_sorted(times)
    if len(unique) < 2:
        return None
    return mean([b - a for a, b in zip(unique, unique[1:])])


def _range_stats(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
    }


def _time_factor(unit: str) -> float:
    normalized = unit.strip().lower()
    if normalized in {"min", "minute", "minutes"}:
        return 60.0
    if normalized in {"s", "sec", "second", "seconds"}:
        return 1.0
    raise ValueError(f"unsupported legacy time unit: {unit}")


def _summarize_legacy(rows: list[dict[str, str]], legacy_time_unit: str) -> dict[str, Any]:
    factor = _time_factor(legacy_time_unit)
    raw_times = [_finite_float(row.get("time_raw")) for row in rows]
    raw_times_f = [value for value in raw_times if value is not None]
    converted_times = [value * factor for value in raw_times_f]
    dps = [_finite_float(row.get("dP")) for row in rows]
    dps_f = [value for value in dps if value is not None]

    return {
        "n_records": len(rows),
        "time_min_s": min(converted_times) if converted_times else None,
        "time_max_s": max(converted_times) if converted_times else None,
        "time_min_raw": min(raw_times_f) if raw_times_f else None,
        "time_max_raw": max(raw_times_f) if raw_times_f else None,
        "n_time_steps": len(set(converted_times)),
        "dt_s_mean": _mean_dt(converted_times),
        "fields": _available_fields(rows),
        "pressure_field": "dP" if dps_f else "",
        "pressure_stats": _range_stats(dps_f),
    }


def _summarize_modern(rows: list[dict[str, str]]) -> dict[str, Any]:
    times = [_finite_float(row.get("time_s")) for row in rows]
    times_f = [value for value in times if value is not None]
    pressures = [_finite_float(row.get("net_pressure_Pa")) for row in rows]
    pressures_f = [value for value in pressures if value is not None]

    return {
        "n_records": len(rows),
        "time_min_s": min(times_f) if times_f else None,
        "time_max_s": max(times_f) if times_f else None,
        "n_time_steps": len(set(times_f)),
        "dt_s_mean": _mean_dt(times_f),
        "fields": _available_fields(rows),
        "pressure_field": "net_pressure_Pa" if pressures_f else "",
        "pressure_stats": _range_stats(pressures_f),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}"
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return str(value)


def _summary_rows(legacy: dict[str, Any], modern: dict[str, Any]) -> list[dict[str, str]]:
    rows = [
        ("n_records", legacy["n_records"], modern["n_records"], "diagnostic_only"),
        ("time_min_s", legacy["time_min_s"], modern["time_min_s"], "unit_converted"),
        ("time_max_s", legacy["time_max_s"], modern["time_max_s"], "unit_converted"),
        ("n_time_steps", legacy["n_time_steps"], modern["n_time_steps"], "structural_diagnostic"),
        ("dt_s_mean", legacy["dt_s_mean"], modern["dt_s_mean"], "structural_diagnostic"),
        ("fields_available", legacy["fields"], modern["fields"], "presence_only"),
    ]
    return [
        {
            "metric": metric,
            "legacy": _fmt(legacy_value),
            "modern": _fmt(modern_value),
            "status": status,
        }
        for metric, legacy_value, modern_value, status in rows
    ]


def _try_import_matplotlib() -> Any | None:
    try:
        import matplotlib  # type: ignore

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    return plt


def _plot_time_coverage(plt: Any, output: Path, legacy: dict[str, Any], modern: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.barh(["legacy", "modern"], [legacy["time_max_s"], modern["time_max_s"]], left=[0, 0], color=["#4f46e5", "#0f766e"])
    ax.set_xlabel("time_s")
    ax.set_title("Level 1 Diagnostic - Time Coverage")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _plot_record_count(plt: Any, output: Path, legacy: dict[str, Any], modern: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(["legacy", "modern"], [legacy["n_records"], modern["n_records"]], color=["#7c3aed", "#0891b2"])
    ax.set_ylabel("records")
    ax.set_title("Level 1 Diagnostic - Record Count")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _plot_pressure_range(plt: Any, output: Path, legacy: dict[str, Any], modern: dict[str, Any]) -> bool:
    legacy_stats = legacy.get("pressure_stats")
    modern_stats = modern.get("pressure_stats")
    if not legacy_stats or not modern_stats:
        return False

    labels = ["legacy dP — semantic unconfirmed", "modern net_pressure_Pa"]
    mins = [legacy_stats["min"], modern_stats["min"]]
    maxs = [legacy_stats["max"], modern_stats["max"]]
    means = [legacy_stats["mean"], modern_stats["mean"]]
    yerr = [[m - lo for m, lo in zip(means, mins)], [hi - m for hi, m in zip(maxs, means)]]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.errorbar(labels, means, yerr=yerr, fmt="o", capsize=6, color="#b91c1c")
    ax.set_ylabel("pressure_Pa")
    ax.set_title("Level 1 Diagnostic - Pressure Range - DIAGNOSTIC ONLY - NOT PHYSICAL VALIDATION")
    ax.tick_params(axis="x", rotation=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return True


def _plot_fields_availability(plt: Any, output: Path, legacy: dict[str, Any], modern: dict[str, Any]) -> None:
    fields = ["time", "layer", "dP", "net_pressure_Pa", "fracture_width_m", "sigmaTheta", "pw", "margin", "opened"]
    legacy_available = set(legacy["fields"])
    modern_available = set(modern["fields"])
    table_data = []
    colors = []
    for field in fields:
        legacy_ok = field in legacy_available or (field == "time" and "time_raw" in legacy_available)
        modern_ok = field in modern_available or (field == "time" and "time_s" in modern_available)
        table_data.append([field, "yes" if legacy_ok else "no", "yes" if modern_ok else "no"])
        colors.append(["#ffffff", "#dcfce7" if legacy_ok else "#fee2e2", "#dcfce7" if modern_ok else "#fee2e2"])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.set_title("Level 1 Diagnostic - Fields Availability")
    table = ax.table(
        cellText=table_data,
        colLabels=["field", "legacy", "modern"],
        cellColours=colors,
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.35)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _generate_plots(output_dir: Path, legacy: dict[str, Any], modern: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    plt = _try_import_matplotlib()
    if plt is None:
        return False, [], [
            "time_coverage.png: NOT_GENERATED_MATPLOTLIB_UNAVAILABLE",
            "record_count.png: NOT_GENERATED_MATPLOTLIB_UNAVAILABLE",
            "pressure_range_diagnostic.png: NOT_GENERATED_MATPLOTLIB_UNAVAILABLE",
            "fields_availability.png: NOT_GENERATED_MATPLOTLIB_UNAVAILABLE",
        ]

    generated: list[str] = []
    not_generated: list[str] = []

    path = output_dir / "time_coverage.png"
    _plot_time_coverage(plt, path, legacy, modern)
    generated.append(str(path))

    path = output_dir / "record_count.png"
    _plot_record_count(plt, path, legacy, modern)
    generated.append(str(path))

    path = output_dir / "pressure_range_diagnostic.png"
    if _plot_pressure_range(plt, path, legacy, modern):
        generated.append(str(path))
    else:
        not_generated.append("pressure_range_diagnostic.png: pressure fields unavailable")

    path = output_dir / "fields_availability.png"
    _plot_fields_availability(plt, path, legacy, modern)
    generated.append(str(path))

    return True, generated, not_generated


def compare(args: argparse.Namespace) -> None:
    legacy_csv = Path(args.legacy_csv)
    modern_csv = Path(args.modern_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    legacy_rows = _read_csv(legacy_csv)
    modern_rows = _read_csv(modern_csv)
    legacy_summary = _summarize_legacy(legacy_rows, args.legacy_time_unit)
    modern_summary = _summarize_modern(modern_rows)

    summary_path = output_dir / "level1_summary.csv"
    _write_csv(summary_path, _summary_rows(legacy_summary, modern_summary))

    matplotlib_available, generated, not_generated = _generate_plots(output_dir, legacy_summary, modern_summary)

    metadata = {
        "phase": "10.15A",
        "legacy_source": "legance/LOT_Tese/results/8-BUZ-67D-PKN.dat",
        "legacy_csv": str(legacy_csv),
        "modern_source": str(modern_csv),
        "controlled_case": "cases/validation/buz67d_pkn_legacy_aligned.yaml",
        "case_classification": "CONTROLLED_EQUIVALENT",
        "time_conversion": "Time_raw * 60.0 (min to s)",
        "comparison_type": "structural_diagnostic",
        "physical_validation": False,
        "numeric_equivalence": False,
        "legacy": legacy_summary,
        "modern": modern_summary,
        "summary_csv": str(summary_path),
        "plots_generated": generated,
        "plots_not_generated": not_generated,
        "matplotlib_available": matplotlib_available,
        "caveats": CAVEATS,
    }
    metadata_path = output_dir / "level1_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"summary_csv={summary_path}")
    print(f"metadata_json={metadata_path}")
    print(f"plots_generated={len(generated)}")
    print(f"plots_not_generated={len(not_generated)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Level 1 structural diagnostics for legacy-modern LOT outputs."
    )
    parser.add_argument("--legacy-csv", required=True, help="legacy_points.csv produced by extract_legacy_lot_outputs.py")
    parser.add_argument("--modern-csv", required=True, help="Modern lot-sim timeseries.csv")
    parser.add_argument("--output-dir", required=True, help="Directory for level1_summary.csv, metadata and PNG diagnostics")
    parser.add_argument("--legacy-time-unit", required=True, choices=["min", "s"], help="Unit of legacy Time_raw values")
    return parser


def main() -> None:
    parser = build_parser()
    compare(parser.parse_args())


if __name__ == "__main__":
    main()
