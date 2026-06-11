#!/usr/bin/env python3
"""Compare Phase 10.29A refined BUZ-67D compliance sensitivity."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


LEGACY_OPENING_TIME_S = 510.0
LEGACY_MAX_PRESSURE_PA = 69035836.1743195
BASE_C_GEOM_1_PA = 1.8571966938610005e-8

CLASS_COMPLETED = "REFINED_SENSITIVITY_COMPLETED"
CLASS_BEST_FOUND = "REFINED_SENSITIVITY_BEST_DIAGNOSTIC_FACTOR_FOUND"
CLASS_OPENING_DOMINATED = "REFINED_SENSITIVITY_OPENING_DOMINATED_BY_COMPLIANCE"
CLASS_INCONCLUSIVE = "REFINED_SENSITIVITY_INCONCLUSIVE"


@dataclass
class RefinedMetrics:
    scenario_id: str
    C_geom_factor: float
    C_geom_value_1_Pa: float
    max_pressure_Pa: float | None
    relative_error_max_pressure_vs_legacy: float | None
    fracture_initiation_time_s: float | None
    opening_time_error_s_vs_510: float | None
    first_sink_positive_time_s: float | None
    sink_delay_s: float | None
    final_pressure_Pa: float | None
    fracture_volume_max_m3: float | None
    leakoff_volume_max_m3: float | None
    combined_score: float | None


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


def truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "opened"}


def time_s(row: dict[str, str]) -> float | None:
    return first_present(row, ["time_s", "elapsed_time_s"])


def pressure(row: dict[str, str]) -> float | None:
    return first_present(row, ["wellbore_pressure_Pa", "pressure_Pa", "wall_pressure_Pa", "net_pressure_Pa"])


def factor_from_id(scenario_id: str) -> float:
    if "baseline" in scenario_id:
        return 1.0
    match = re.search(r"cgeom_(\d{3})", scenario_id)
    if match:
        return int(match.group(1)) / 100.0
    raise ValueError(f"Cannot infer C_geom factor from {scenario_id}")


def max_column(rows: list[dict[str, str]], names: Iterable[str]) -> float | None:
    values = [first_present(row, names) for row in rows]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def summarize(path: Path) -> RefinedMetrics:
    scenario_id = path.parent.name
    factor = factor_from_id(scenario_id)
    rows = read_csv(path)
    pressures = [pressure(row) for row in rows]
    pressures = [value for value in pressures if value is not None]
    if not pressures:
        raise ValueError(f"{path} has no usable pressure column")

    first_open = None
    for row in rows:
        if truthy(row.get("fracture_open")) or truthy(row.get("fracture_opened")) or truthy(row.get("fracture_initiated")) or truthy(row.get("opened")):
            first_open = time_s(row)
            break

    first_sink = None
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
            first_sink = time_s(row)
            break

    max_pressure = max(pressures)
    opening_error = (first_open - LEGACY_OPENING_TIME_S) if first_open is not None else None
    pressure_error = (max_pressure - LEGACY_MAX_PRESSURE_PA) / LEGACY_MAX_PRESSURE_PA
    score = None
    if opening_error is not None:
        score = abs(opening_error) / 150.0 + abs(pressure_error) / 0.10

    return RefinedMetrics(
        scenario_id=scenario_id,
        C_geom_factor=factor,
        C_geom_value_1_Pa=BASE_C_GEOM_1_PA * factor,
        max_pressure_Pa=max_pressure,
        relative_error_max_pressure_vs_legacy=pressure_error,
        fracture_initiation_time_s=first_open,
        opening_time_error_s_vs_510=opening_error,
        first_sink_positive_time_s=first_sink,
        sink_delay_s=(first_sink - first_open) if first_sink is not None and first_open is not None else None,
        final_pressure_Pa=pressures[-1],
        fracture_volume_max_m3=max_column(rows, ["fracture_volume_m3", "cumulative_fracture_volume_m3"]),
        leakoff_volume_max_m3=max_column(rows, ["leakoff_volume_m3", "cumulative_leakoff_volume_m3"]),
        combined_score=score,
    )


def discover(root: Path) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    files = sorted(root.glob("*/timeseries.csv"))
    if not files:
        raise FileNotFoundError(f"No timeseries.csv files under {root}")
    return files


def best_by(metrics: list[RefinedMetrics], key: str) -> RefinedMetrics | None:
    candidates = [metric for metric in metrics if getattr(metric, key) is not None]
    if not candidates:
        return None
    if key == "opening_time_error_s_vs_510":
        return min(candidates, key=lambda metric: abs(metric.opening_time_error_s_vs_510 or 0.0))
    if key == "relative_error_max_pressure_vs_legacy":
        return min(candidates, key=lambda metric: abs(metric.relative_error_max_pressure_vs_legacy or 0.0))
    return min(candidates, key=lambda metric: getattr(metric, key))


def classify(metrics: list[RefinedMetrics]) -> list[str]:
    classes = [CLASS_COMPLETED]
    if best_by(metrics, "combined_score") is not None:
        classes.append(CLASS_BEST_FOUND)
    opened = [m for m in metrics if m.fracture_initiation_time_s is not None]
    if len({m.fracture_initiation_time_s for m in opened}) > 1:
        classes.append(CLASS_OPENING_DOMINATED)
    if len(metrics) < 3:
        classes.append(CLASS_INCONCLUSIVE)
    return classes


def write_summary(path: Path, metrics: list[RefinedMetrics]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(metrics[0]).keys()))
        writer.writeheader()
        for metric in metrics:
            writer.writerow(asdict(metric))


def plot_outputs(output_dir: Path, metrics: list[RefinedMetrics], root: Path) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return []

    plots: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(metrics, key=lambda m: m.C_geom_factor)
    factors = [m.C_geom_factor for m in ordered]

    def save_xy(y_values: list[float | None], ylabel: str, filename: str) -> None:
        plt.figure(figsize=(7, 4))
        plt.plot(factors, [math.nan if v is None else v for v in y_values], marker="o")
        plt.xlabel("C_geom factor")
        plt.ylabel(ylabel)
        plt.tight_layout()
        path = output_dir / filename
        plt.savefig(path, dpi=160)
        plt.close()
        plots.append(str(path))

    save_xy([m.fracture_initiation_time_s for m in ordered], "opening time (s)", "cgeom_factor_vs_opening_time.png")
    save_xy([m.max_pressure_Pa for m in ordered], "max pressure (Pa)", "cgeom_factor_vs_max_pressure.png")
    save_xy([m.combined_score for m in ordered], "combined score", "cgeom_factor_vs_combined_score.png")

    plt.figure(figsize=(8, 4))
    for csv_path in discover(root):
        scenario_metrics = next((m for m in metrics if m.scenario_id == csv_path.parent.name), None)
        if scenario_metrics is None:
            continue
        rows = read_csv(csv_path)
        pairs = [(time_s(row), pressure(row)) for row in rows]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        if pairs:
            plt.plot([p[0] for p in pairs], [p[1] for p in pairs], label=f"{scenario_metrics.C_geom_factor:.2f}x")
    plt.xlabel("time (s)")
    plt.ylabel("pressure (Pa)")
    plt.legend(fontsize="small")
    plt.tight_layout()
    path = output_dir / "pressure_vs_time_refined_sensitivity.png"
    plt.savefig(path, dpi=160)
    plt.close()
    plots.append(str(path))

    plt.figure(figsize=(7, 4))
    plt.scatter(
        [m.fracture_volume_max_m3 or 0.0 for m in ordered],
        [m.max_pressure_Pa or 0.0 for m in ordered],
    )
    plt.xlabel("fracture volume max (m3)")
    plt.ylabel("max pressure (Pa)")
    plt.tight_layout()
    path = output_dir / "volume_pressure_refined_sensitivity.png"
    plt.savefig(path, dpi=160)
    plt.close()
    plots.append(str(path))
    return plots


def compare(root: Path, output_dir: Path) -> dict:
    metrics = [summarize(path) for path in discover(root)]
    summary_csv = output_dir / "phase10_29a_refined_sensitivity_summary.csv"
    write_summary(summary_csv, metrics)
    best_opening = best_by(metrics, "opening_time_error_s_vs_510")
    best_pressure = best_by(metrics, "relative_error_max_pressure_vs_legacy")
    best_score = best_by(metrics, "combined_score")
    plots = plot_outputs(output_dir, metrics, root)
    metadata = {
        "phase": "10.29A",
        "classification": classify(metrics),
        "summary_csv": str(summary_csv),
        "best_factor_by_opening_time": best_opening.C_geom_factor if best_opening else None,
        "best_factor_by_max_pressure": best_pressure.C_geom_factor if best_pressure else None,
        "best_factor_by_combined_score": best_score.C_geom_factor if best_score else None,
        "best_scenario_by_combined_score": best_score.scenario_id if best_score else None,
        "plots": plots,
        "metrics": [asdict(metric) for metric in sorted(metrics, key=lambda m: m.C_geom_factor)],
        "caveat": "Best factors are diagnostic sensitivity results, not automatic calibration or physical validation.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase10_29a_refined_sensitivity_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sensitivity-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--legacy-csv", type=Path, help="Accepted for traceability; current defaults use documented legacy metrics.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metadata = compare(args.sensitivity_root, args.output_dir)
    print(f"CLASSIFICATION={','.join(metadata['classification'])}")
    print(f"BEST_FACTOR_BY_OPENING_TIME={metadata['best_factor_by_opening_time']}")
    print(f"BEST_FACTOR_BY_MAX_PRESSURE={metadata['best_factor_by_max_pressure']}")
    print(f"BEST_FACTOR_BY_COMBINED_SCORE={metadata['best_factor_by_combined_score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
