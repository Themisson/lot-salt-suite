from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _finite_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _values(rows: list[dict[str, str]], field: str) -> list[float]:
    values = [_finite_float(row.get(field)) for row in rows]
    return [value for value in values if value is not None]


def _range(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values), "mean": mean(values)}


def _max_pressure(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _difference(reference: float | None, target: float | None) -> dict[str, float | None]:
    if reference is None or target is None:
        return {"absolute_Pa": None, "relative": None}
    absolute = abs(target - reference)
    return {"absolute_Pa": absolute, "relative": absolute / abs(reference) if reference else None}


def _modern_points(rows: list[dict[str, str]], pressure_field: str) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        pressure = _finite_float(row.get(pressure_field))
        injected = _finite_float(row.get("injected_volume_m3"))
        if time_s is None or pressure is None:
            continue
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": injected,
                "pressure_Pa": pressure,
            }
        )
    return points


def _legacy_points(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        if time_s is not None:
            grouped.setdefault(time_s, []).append(row)
    points: list[dict[str, Any]] = []
    for time_s in sorted(grouped):
        selected = max(
            grouped[time_s],
            key=lambda row: _finite_float(row.get("injected_volume_m3")) or 0.0,
        )
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": _finite_float(selected.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(selected.get("pw_Pa")),
            }
        )
    return points


def _require_summary_denominator(modern_json: dict[str, Any]) -> float:
    summary = modern_json.get("summary", {})
    compressibility = summary.get("fluid_compressibility_per_Pa")
    volume = summary.get("initial_annular_volume_m3")
    if not isinstance(compressibility, (int, float)) or not math.isfinite(compressibility) or compressibility <= 0.0:
        raise ValueError("modern result.json missing positive fluid_compressibility_per_Pa")
    if not isinstance(volume, (int, float)) or not math.isfinite(volume) or volume <= 0.0:
        raise ValueError("modern result.json missing positive initial_annular_volume_m3")
    return float(compressibility) * float(volume)


def _reconstruct_uncoupled_pressure(
    modern_rows: list[dict[str, str]], denominator: float
) -> list[dict[str, Any]]:
    pressure = 0.0
    points: list[dict[str, Any]] = []
    for index, row in enumerate(modern_rows):
        time_s = _finite_float(row.get("time_s"))
        injected_increment = _finite_float(row.get("balance_injected_volume_increment_m3"))
        initial_pressure = _finite_float(row.get("initial_pressure_Pa"))
        injected_volume = _finite_float(row.get("injected_volume_m3"))
        if time_s is None or injected_increment is None or initial_pressure is None:
            continue
        if index == 0:
            pressure = initial_pressure
        pressure = max(0.0, pressure + injected_increment / denominator)
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": injected_volume,
                "pressure_Pa": pressure,
            }
        )
    return points


def _sum_field(rows: list[dict[str, str]], field: str) -> float:
    return sum(_values(rows, field))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _plot_xy(
    path: Path,
    series: list[tuple[str, list[dict[str, Any]], str, str]],
    title: str,
    xlabel: str,
    ylabel: str,
    caveat: str,
) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(9, 5))
    for label, points, xfield, yfield in series:
        xs = [
            point[xfield]
            for point in points
            if point.get(xfield) is not None and point.get(yfield) is not None
        ]
        ys = [
            point[yfield]
            for point in points
            if point.get(xfield) is not None and point.get(yfield) is not None
        ]
        ax.plot(xs, ys, label=label)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.text(0.02, 0.02, caveat, transform=ax.transAxes, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_coupled_csv))
    modern_json = _read_json(Path(args.modern_result_json))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    denominator = _require_summary_denominator(modern_json)
    legacy = _legacy_points(legacy_rows)
    coupled = _modern_points(modern_rows, "wellbore_pressure_Pa")
    uncoupled = _reconstruct_uncoupled_pressure(modern_rows, denominator)

    legacy_max = _max_pressure(legacy_rows, "pw_Pa")
    coupled_max = max((point["pressure_Pa"] for point in coupled), default=None)
    uncoupled_max = max((point["pressure_Pa"] for point in uncoupled), default=None)

    total_fracture_sink = _sum_field(modern_rows, "balance_fracture_volume_increment_m3")
    total_leakoff_sink = _sum_field(modern_rows, "balance_leakoff_volume_increment_m3")
    total_injected_increment = _sum_field(modern_rows, "balance_injected_volume_increment_m3")
    total_effective_increment = _sum_field(modern_rows, "balance_effective_volume_increment_m3")

    plots = {
        "pressure_vs_time_fracture_volume_coupling": _plot_xy(
            output_dir / "pressure_vs_time_fracture_volume_coupling.png",
            [
                ("Legacy audit pw_Pa", legacy, "time_s", "pressure_Pa"),
                ("Modern uncoupled reconstruction", uncoupled, "time_s", "pressure_Pa"),
                ("Modern 10.18C coupled", coupled, "time_s", "pressure_Pa"),
            ],
            "Phase 10.18C - Fracture/leakoff volume balance diagnostic",
            "time_s",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - pressure-threshold approximation; no physical validation.",
        ),
        "pressure_vs_injected_volume_fracture_volume_coupling": _plot_xy(
            output_dir / "pressure_vs_injected_volume_fracture_volume_coupling.png",
            [
                ("Legacy audit pw_Pa", legacy, "injected_volume_m3", "pressure_Pa"),
                ("Modern uncoupled reconstruction", uncoupled, "injected_volume_m3", "pressure_Pa"),
                ("Modern 10.18C coupled", coupled, "injected_volume_m3", "pressure_Pa"),
            ],
            "Phase 10.18C - Pressure vs injected volume",
            "injected_volume_m3",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - not a fracture-validation plot.",
        ),
    }

    metadata = {
        "phase": "10.18C",
        "status": "PHASE10_18C_FRACTURE_VOLUME_BALANCE_DIAGNOSTIC_COMPLETE",
        "gate": "FRACTURE_VOLUME_BALANCE_IMPLEMENTATION_ALLOWED_PRESSURE_THRESHOLD_APPROXIMATION",
        "legacy_sigma_theta_criterion_status": "PARTIALLY_EXTRACTED_NOT_REPRODUCED_IN_PKN_MODEL",
        "physical_validation": False,
        "numeric_equivalence": False,
        "pressure_semantic_equivalence": False,
        "legacy": {
            "pressure_field": "pw_Pa",
            "max_pressure_Pa": legacy_max,
            "time_range_s": _range(_values(legacy_rows, "time_s")),
        },
        "modern_uncoupled_reconstruction": {
            "pressure_field": "initial_pressure + cumulative_injected_increment/(C*V)",
            "max_pressure_Pa": uncoupled_max,
        },
        "modern_coupled_10_18c": {
            "pressure_field": "wellbore_pressure_Pa",
            "max_pressure_Pa": coupled_max,
            "total_injected_increment_m3": total_injected_increment,
            "total_fracture_sink_increment_m3": total_fracture_sink,
            "total_leakoff_sink_increment_m3": total_leakoff_sink,
            "total_effective_increment_m3": total_effective_increment,
        },
        "differences": {
            "legacy_vs_uncoupled_max_pressure": _difference(legacy_max, uncoupled_max),
            "legacy_vs_coupled_max_pressure": _difference(legacy_max, coupled_max),
            "uncoupled_vs_coupled_max_pressure": _difference(uncoupled_max, coupled_max),
        },
        "plots": plots,
        "caveats": [
            "Diagnostic only; no physical validation.",
            "Legacy opens fracture with |dP + pi| > |sigma_theta at influence height|.",
            "Modern PknModel does not reproduce the legacy sigma-theta influence-height criterion in this phase.",
            "Modern coupling uses the existing fracture.breakdown.pressure threshold as a simplified opt-in approximation.",
            "No Zamora, casing compliance, APB feedback or new PKN formulation is implemented.",
        ],
    }

    with (output_dir / "phase10_18c_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")

    _write_csv(
        output_dir / "phase10_18c_summary.csv",
        [
            {
                "metric": "max_pressure_Pa",
                "legacy": legacy_max,
                "modern_uncoupled_reconstruction": uncoupled_max,
                "modern_coupled_10_18c": coupled_max,
            },
            {
                "metric": "relative_difference_to_legacy",
                "legacy": 0.0,
                "modern_uncoupled_reconstruction": metadata["differences"][
                    "legacy_vs_uncoupled_max_pressure"
                ]["relative"],
                "modern_coupled_10_18c": metadata["differences"][
                    "legacy_vs_coupled_max_pressure"
                ]["relative"],
            },
            {
                "metric": "total_volume_increment_m3",
                "legacy": None,
                "modern_uncoupled_reconstruction": total_injected_increment,
                "modern_coupled_10_18c": total_effective_increment,
            },
            {
                "metric": "total_fracture_plus_leakoff_sink_m3",
                "legacy": None,
                "modern_uncoupled_reconstruction": 0.0,
                "modern_coupled_10_18c": total_fracture_sink + total_leakoff_sink,
            },
        ],
        [
            "metric",
            "legacy",
            "modern_uncoupled_reconstruction",
            "modern_coupled_10_18c",
        ],
    )
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 10.18C fracture/leakoff volume balance diagnostic."
    )
    parser.add_argument("--legacy-csv", required=True)
    parser.add_argument("--modern-coupled-csv", required=True)
    parser.add_argument("--modern-result-json", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    metadata = run_comparison(parse_args())
    print(json.dumps({"phase": metadata["phase"], "status": metadata["status"]}, indent=2))


if __name__ == "__main__":
    main()
