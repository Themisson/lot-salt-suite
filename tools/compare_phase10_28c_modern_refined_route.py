#!/usr/bin/env python3
"""Compare Phase 10.28C modern-refined additional or sensitivity route."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


CLASS_ADDITIONAL_OK = "PHASE10_28C_ADDITIONAL_CASE_RUN_OK"
CLASS_ADDITIONAL_NO_LEGACY = "PHASE10_28C_ADDITIONAL_CASE_NO_LEGACY_COMPARISON"
CLASS_SENSITIVITY_OK = "PHASE10_28C_SENSITIVITY_MATRIX_RUN_OK"
CLASS_SENSITIVITY_INCONCLUSIVE = "PHASE10_28C_SENSITIVITY_MATRIX_INCONCLUSIVE"
CLASS_RUN_FAILED = "PHASE10_28C_RUN_FAILED"


@dataclass
class ScenarioMetrics:
    scenario_id: str
    c_geom_factor: float | None
    sink_timing: str
    max_pressure_Pa: float | None
    fracture_initiation_time_s: float | None
    first_sink_positive_time_s: float | None
    sink_delay_s: float | None
    final_pressure_Pa: float | None
    injected_volume_total_m3: float | None
    fracture_volume_max_m3: float | None
    leakoff_volume_max_m3: float | None
    delta_vs_baseline_Pa: float | None = None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no data rows")
    return rows


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def first_present(row: dict[str, str], names: Iterable[str]) -> float | None:
    for name in names:
        value = as_float(row.get(name))
        if value is not None:
            return value
    return None


def pressure(row: dict[str, str]) -> float | None:
    return first_present(row, ["wellbore_pressure_Pa", "pressure_Pa", "wall_pressure_Pa", "net_pressure_Pa"])


def time_s(row: dict[str, str]) -> float | None:
    return first_present(row, ["time_s", "elapsed_time_s"])


def truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "opened"}


def infer_factor(scenario_id: str) -> float | None:
    if "075" in scenario_id or "lower" in scenario_id:
        return 0.75
    if "125" in scenario_id or "higher" in scenario_id:
        return 1.25
    if "baseline" in scenario_id or "same_step" in scenario_id:
        return 1.0
    return None


def infer_sink_timing(scenario_id: str) -> str:
    if "same_step" in scenario_id:
        return "same_step"
    return "next_step"


def max_column(rows: list[dict[str, str]], names: Iterable[str]) -> float | None:
    values = [first_present(row, names) for row in rows]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def summarize_timeseries(path: Path, scenario_id: str) -> ScenarioMetrics:
    rows = read_csv(path)
    pressures = [pressure(row) for row in rows]
    pressures = [value for value in pressures if value is not None]
    if not pressures:
        raise ValueError(f"{path} does not expose a usable pressure column")

    first_open_time = None
    for row in rows:
        opened = (
            truthy(row.get("fracture_open"))
            or truthy(row.get("fracture_opened"))
            or truthy(row.get("fracture_initiated"))
            or truthy(row.get("opened"))
        )
        if opened:
            first_open_time = time_s(row)
            break

    first_sink_time = None
    for row in rows:
        sink = first_present(
            row,
            [
                "fracture_sink_m3",
                "fracture_sink_increment_m3",
                "fracture_sink_applied_m3",
                "leakoff_volume_increment_m3",
                "fracture_volume_increment_m3",
            ],
        )
        if sink is not None and sink > 0:
            first_sink_time = time_s(row)
            break

    final_pressure = pressures[-1]
    return ScenarioMetrics(
        scenario_id=scenario_id,
        c_geom_factor=infer_factor(scenario_id),
        sink_timing=infer_sink_timing(scenario_id),
        max_pressure_Pa=max(pressures),
        fracture_initiation_time_s=first_open_time,
        first_sink_positive_time_s=first_sink_time,
        sink_delay_s=(first_sink_time - first_open_time) if first_open_time is not None and first_sink_time is not None else None,
        final_pressure_Pa=final_pressure,
        injected_volume_total_m3=max_column(rows, ["injected_volume_m3", "cumulative_injected_volume_m3"]),
        fracture_volume_max_m3=max_column(rows, ["fracture_volume_m3", "cumulative_fracture_volume_m3"]),
        leakoff_volume_max_m3=max_column(rows, ["leakoff_volume_m3", "cumulative_leakoff_volume_m3"]),
    )


def discover_sensitivity(root: Path) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    files = sorted(root.glob("*/timeseries.csv"))
    if not files:
        raise FileNotFoundError(f"No timeseries.csv files under {root}")
    return files


def classify_sensitivity(metrics: list[ScenarioMetrics]) -> str:
    ids = {m.scenario_id for m in metrics}
    required = {
        "buz67d_modern_refined_sens_baseline",
        "buz67d_modern_refined_sens_cgeom_075",
        "buz67d_modern_refined_sens_cgeom_125",
        "buz67d_modern_refined_sens_same_step",
    }
    return CLASS_SENSITIVITY_OK if required.issubset(ids) else CLASS_SENSITIVITY_INCONCLUSIVE


def write_summary_csv(path: Path, metrics: list[ScenarioMetrics]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(metrics[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(asdict(metric))


def maybe_plot(output_dir: Path, metrics: list[ScenarioMetrics]) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    labels = [m.scenario_id.replace("buz67d_modern_refined_sens_", "") for m in metrics]
    plots: list[str] = []

    def bar_plot(values: list[float | None], title: str, ylabel: str, filename: str) -> None:
        plt.figure(figsize=(8, 4))
        plt.bar(labels, [0.0 if value is None else value for value in values])
        plt.xticks(rotation=20, ha="right")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.tight_layout()
        out = output_dir / filename
        plt.savefig(out, dpi=160)
        plt.close()
        plots.append(str(out))

    bar_plot([m.max_pressure_Pa for m in metrics], "Sensitivity max pressure", "Pa", "sensitivity_max_pressure_bar.png")
    bar_plot([m.fracture_initiation_time_s for m in metrics], "Sensitivity opening time", "s", "sensitivity_opening_time_bar.png")
    bar_plot([m.sink_delay_s for m in metrics], "Sensitivity sink delay", "s", "sensitivity_sink_delay_bar.png")

    plt.figure(figsize=(8, 4))
    plt.scatter(
        [0.0 if m.injected_volume_total_m3 is None else m.injected_volume_total_m3 for m in metrics],
        [0.0 if m.max_pressure_Pa is None else m.max_pressure_Pa for m in metrics],
    )
    for label, metric in zip(labels, metrics):
        plt.annotate(label, (metric.injected_volume_total_m3 or 0.0, metric.max_pressure_Pa or 0.0))
    plt.xlabel("injected volume max (m3)")
    plt.ylabel("max pressure (Pa)")
    plt.tight_layout()
    out = output_dir / "sensitivity_volume_pressure.png"
    plt.savefig(out, dpi=160)
    plt.close()
    plots.append(str(out))

    return plots


def plot_sensitivity_pressure_timeseries(root: Path, output_dir: Path) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return []

    plt.figure(figsize=(8, 4))
    for csv_path in discover_sensitivity(root):
        rows = read_csv(csv_path)
        xs = [time_s(row) for row in rows]
        ys = [pressure(row) for row in rows]
        pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if not pairs:
            continue
        plt.plot([p[0] for p in pairs], [p[1] for p in pairs], label=csv_path.parent.name.replace("buz67d_modern_refined_sens_", ""))
    plt.xlabel("time (s)")
    plt.ylabel("pressure (Pa)")
    plt.legend(fontsize="small")
    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "sensitivity_pressure_vs_time.png"
    plt.savefig(out, dpi=160)
    plt.close()
    return [str(out)]


def compare_additional(modern_csv: Path, output_dir: Path) -> dict:
    metric = summarize_timeseries(modern_csv, modern_csv.parent.name)
    summary_csv = output_dir / "phase10_28c_summary.csv"
    write_summary_csv(summary_csv, [metric])
    metadata = {
        "route": "additional_well",
        "classification": CLASS_ADDITIONAL_NO_LEGACY,
        "summary_csv": str(summary_csv),
        "metrics": [asdict(metric)],
        "caveats": ["No audited legacy comparison was provided for this additional route."],
    }
    write_metadata(output_dir, metadata)
    return metadata


def compare_sensitivity(root: Path, output_dir: Path) -> dict:
    metrics = [summarize_timeseries(path, path.parent.name) for path in discover_sensitivity(root)]
    baseline = next((m.max_pressure_Pa for m in metrics if "baseline" in m.scenario_id), None)
    for metric in metrics:
        if baseline is not None and metric.max_pressure_Pa is not None:
            metric.delta_vs_baseline_Pa = metric.max_pressure_Pa - baseline
    summary_csv = output_dir / "phase10_28c_summary.csv"
    write_summary_csv(summary_csv, metrics)
    plots = plot_sensitivity_pressure_timeseries(root, output_dir) + maybe_plot(output_dir, metrics)
    metadata = {
        "route": "sensitivity",
        "classification": classify_sensitivity(metrics),
        "summary_csv": str(summary_csv),
        "plots": plots,
        "metrics": [asdict(metric) for metric in metrics],
        "caveats": [
            "Modern-refined sensitivity only; not legacy-equivalence.",
            "Opening differences are diagnostic and not automatic physical errors.",
            "APBSalt1D metadata is not consumed as an effective sensitivity variable.",
        ],
    }
    write_metadata(output_dir, metadata)
    return metadata


def write_metadata(output_dir: Path, metadata: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase10_28c_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", choices=["additional_well", "sensitivity"], required=True)
    parser.add_argument("--modern-csv", type=Path)
    parser.add_argument("--sensitivity-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.route == "additional_well":
            if args.modern_csv is None:
                raise ValueError("--modern-csv is required for additional_well")
            metadata = compare_additional(args.modern_csv, args.output_dir)
        else:
            if args.sensitivity_root is None:
                raise ValueError("--sensitivity-root is required for sensitivity")
            metadata = compare_sensitivity(args.sensitivity_root, args.output_dir)
    except Exception as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        metadata = {"route": args.route, "classification": CLASS_RUN_FAILED, "error": str(exc)}
        write_metadata(args.output_dir, metadata)
        print(f"CLASSIFICATION={CLASS_RUN_FAILED}")
        print(f"ERROR={exc}")
        return 2
    print(f"CLASSIFICATION={metadata['classification']}")
    print(f"SUMMARY_CSV={metadata['summary_csv']}")
    print(f"METADATA_JSON={args.output_dir / 'phase10_28c_metadata.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
