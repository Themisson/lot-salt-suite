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


def _legacy_points(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        if time_s is not None:
            grouped.setdefault(time_s, []).append(row)
    points: list[dict[str, Any]] = []
    for time_s in sorted(grouped):
        selected = max(grouped[time_s], key=lambda row: _finite_float(row.get("injected_volume_m3")) or 0.0)
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": _finite_float(selected.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(selected.get("pw_Pa")),
            }
        )
    return points


def _modern_points(rows: list[dict[str, str]], pressure_field: str) -> list[dict[str, Any]]:
    return [
        {
            "time_s": _finite_float(row.get("time_s")),
            "injected_volume_m3": _finite_float(row.get("injected_volume_m3")),
            "pressure_Pa": _finite_float(row.get(pressure_field)),
        }
        for row in rows
        if _finite_float(row.get("time_s")) is not None
    ]


def _max_pressure(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _difference(reference: float | None, target: float | None) -> dict[str, float | None]:
    if reference is None or target is None:
        return {"absolute_Pa": None, "relative": None}
    absolute = abs(target - reference)
    return {"absolute_Pa": absolute, "relative": absolute / abs(reference) if reference else None}


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _plot_xy(path: Path, series: list[tuple[str, list[dict[str, Any]], str, str]], title: str, xlabel: str, ylabel: str, caveat: str) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(9, 5))
    for label, points, xfield, yfield in series:
      xs = [p[xfield] for p in points if p.get(xfield) is not None and p.get(yfield) is not None]
      ys = [p[yfield] for p in points if p.get(xfield) is not None and p.get(yfield) is not None]
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


def _rate_points(modern_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    previous_time: float | None = None
    previous_volume: float | None = None
    for row in modern_rows:
        time_s = _finite_float(row.get("time_s"))
        volume_m3 = _finite_float(row.get("injected_volume_m3"))
        if time_s is None or volume_m3 is None:
            continue
        if previous_time is None or previous_volume is None or time_s == previous_time:
            rate = 0.0
        else:
            rate = (volume_m3 - previous_volume) / (time_s - previous_time)
        points.append({"time_s": time_s, "rate_m3_s": rate})
        previous_time = time_s
        previous_volume = volume_m3
    return points


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_full_cycle_csv))
    direct_rows = _read_csv(Path(args.modern_direct_csv)) if args.modern_direct_csv else []
    volumetric_10_18a_rows = _read_csv(Path(args.modern_volumetric_10_18a_csv)) if args.modern_volumetric_10_18a_csv else []
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    legacy_max = _max_pressure(legacy_rows, "pw_Pa")
    full_max = _max_pressure(modern_rows, "wellbore_pressure_Pa")
    direct_max = _max_pressure(direct_rows, "net_pressure_Pa") if direct_rows else None
    old_vol_max = _max_pressure(volumetric_10_18a_rows, "wellbore_pressure_Pa") if volumetric_10_18a_rows else None

    legacy = _legacy_points(legacy_rows)
    modern = _modern_points(modern_rows, "wellbore_pressure_Pa")
    direct = _modern_points(direct_rows, "net_pressure_Pa") if direct_rows else []
    old_vol = _modern_points(volumetric_10_18a_rows, "wellbore_pressure_Pa") if volumetric_10_18a_rows else []

    plots = {
        "pressure_vs_time_full_cycle": _plot_xy(
            output_dir / "pressure_vs_time_full_cycle.png",
            [
                ("Legacy audit pw_Pa", legacy, "time_s", "pressure_Pa"),
                ("Modern full cycle wellbore_pressure_Pa", modern, "time_s", "pressure_Pa"),
            ],
            "Phase 10.18B - Pressure vs Time - Full LOT Cycle",
            "time_s",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - not physical validation.",
        ),
        "injected_volume_vs_pressure_full_cycle": _plot_xy(
            output_dir / "injected_volume_vs_pressure_full_cycle.png",
            [
                ("Legacy audit pw_Pa", legacy, "injected_volume_m3", "pressure_Pa"),
                ("Modern full cycle wellbore_pressure_Pa", modern, "injected_volume_m3", "pressure_Pa"),
            ],
            "Phase 10.18B - Volume vs Pressure - Full LOT Cycle",
            "injected_volume_m3",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - pressure definitions may differ.",
        ),
        "injection_rate_vs_time": _plot_xy(
            output_dir / "injection_rate_vs_time.png",
            [("Modern inferred injection rate", _rate_points(modern_rows), "time_s", "rate_m3_s")],
            "Phase 10.18B - Injection Rate Schedule",
            "time_s",
            "rate_m3_s",
            "DIAGNOSTIC ONLY - rate inferred from injected_volume_m3.",
        ),
        "pressure_comparison_all_modes": _plot_xy(
            output_dir / "pressure_comparison_all_modes.png",
            [
                ("Legacy audit pw_Pa", legacy, "time_s", "pressure_Pa"),
                ("Modern pkn_direct net_pressure_Pa", direct, "time_s", "pressure_Pa"),
                ("Modern 10.18A volumetric_balance", old_vol, "time_s", "pressure_Pa"),
                ("Modern 10.18B full cycle", modern, "time_s", "pressure_Pa"),
            ],
            "Phase 10.18B - Pressure Evolution - All Modes Comparison",
            "time_s",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - no numeric equivalence declared.",
        ),
    }

    initial_pressure = _values(modern_rows, "initial_pressure_Pa")
    metadata = {
        "phase": "10.18B",
        "status": "PHASE10_18B_INITIAL_PRESSURE_AND_SHUTIN_DIAGNOSTIC_COMPLETE",
        "pre_existing_pressure_gate": "PRE_EXISTING_PRESSURE_CONFIRMED_IMPLEMENTATION_ALLOWED",
        "shutin_gate": "SHUTIN_CONFIRMED_IMPLEMENTATION_ALLOWED",
        "pre_existing_pressure_fix_classification": "PRE_EXISTING_PRESSURE_FIX_PARTIAL_OTHER_FACTORS_REMAIN",
        "physical_validation": False,
        "numeric_equivalence": False,
        "legacy": {
            "pressure_field": "pw_Pa",
            "n_records": len(legacy_rows),
            "time_range_s": _range(_values(legacy_rows, "time_s")),
            "pressure_range_Pa": _range(_values(legacy_rows, "pw_Pa")),
            "max_pressure_Pa": legacy_max,
        },
        "modern_full_cycle": {
            "pressure_field": "wellbore_pressure_Pa",
            "n_records": len(modern_rows),
            "time_range_s": _range(_values(modern_rows, "time_s")),
            "pressure_range_Pa": _range(_values(modern_rows, "wellbore_pressure_Pa")),
            "max_pressure_Pa": full_max,
            "initial_pressure_Pa": initial_pressure[0] if initial_pressure else None,
            "max_injected_volume_m3": max(_values(modern_rows, "injected_volume_m3")),
        },
        "differences": {
            "legacy_vs_full_cycle_max_pressure": _difference(legacy_max, full_max),
            "legacy_vs_10_18a_volumetric_max_pressure": _difference(legacy_max, old_vol_max),
            "legacy_vs_pkn_direct_max_pressure": _difference(legacy_max, direct_max),
        },
        "plots": plots,
        "caveats": [
            "Diagnostic only; no physical validation.",
            "Initial pressure is extracted from audited legacy pw_Pa at t=0, where dP=0.",
            "Adding the extracted initial pressure overshoots legacy maximum pressure in the current simplified balance route.",
            "Shut-in is represented as zero new injection and constant injected volume.",
            "No Zamora, accommodation, casing elasticity, sigmaTheta, margin or opened comparison is performed.",
        ],
    }

    with (output_dir / "phase10_18b_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")

    _write_csv(
        output_dir / "phase10_18b_summary.csv",
        [
            {
                "metric": "max_pressure_Pa",
                "legacy": legacy_max,
                "pkn_direct": direct_max,
                "volumetric_10_18a": old_vol_max,
                "full_cycle_10_18b": full_max,
            },
            {
                "metric": "relative_difference_to_legacy",
                "legacy": 0.0,
                "pkn_direct": metadata["differences"]["legacy_vs_pkn_direct_max_pressure"]["relative"],
                "volumetric_10_18a": metadata["differences"]["legacy_vs_10_18a_volumetric_max_pressure"]["relative"],
                "full_cycle_10_18b": metadata["differences"]["legacy_vs_full_cycle_max_pressure"]["relative"],
            },
        ],
        ["metric", "legacy", "pkn_direct", "volumetric_10_18a", "full_cycle_10_18b"],
    )
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 10.18B initial-pressure and shut-in diagnostic.")
    parser.add_argument("--legacy-csv", required=True)
    parser.add_argument("--modern-full-cycle-csv", required=True)
    parser.add_argument("--modern-direct-csv")
    parser.add_argument("--modern-volumetric-10-18a-csv")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    metadata = run_comparison(parse_args())
    print(json.dumps({"phase": metadata["phase"], "status": metadata["status"]}, indent=2))


if __name__ == "__main__":
    main()
