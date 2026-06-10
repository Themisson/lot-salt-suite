from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


PHASE = "10.19A"
LEGACY_MAX_PRESSURE_PA = 69.0358361743195e6
LEGACY_OPEN_TIME_S = 510.0


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


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


def _modern_points(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in rows:
        time_s = _float(row.get("time_s"))
        pressure = _float(row.get("wellbore_pressure_Pa"))
        if time_s is None or pressure is None:
            continue
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": _float(row.get("injected_volume_m3")),
                "pressure_Pa": pressure,
                "sigma_theta_Pa": _float(
                    row.get("fracture_initiation_sigma_theta_Pa")
                ),
                "margin_Pa": _float(row.get("fracture_initiation_margin_Pa")),
            }
        )
    return points


def _legacy_points(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _float(row.get("time_s"))
        if time_s is not None:
            grouped.setdefault(time_s, []).append(row)
    points: list[dict[str, Any]] = []
    for time_s in sorted(grouped):
        selected = max(
            grouped[time_s], key=lambda row: _float(row.get("pw_Pa")) or -math.inf
        )
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": _float(selected.get("injected_volume_m3")),
                "pressure_Pa": _float(selected.get("pw_Pa")),
            }
        )
    return points


def _first_initiation(rows: list[dict[str, str]]) -> dict[str, float | None]:
    for row in rows:
        initiated = row.get("fracture_initiated", "").strip().lower()
        if initiated not in {"1", "true", "yes"}:
          continue
        pressure = _float(row.get("fracture_initiation_pressure_Pa"))
        sigma = _float(row.get("fracture_initiation_sigma_theta_Pa"))
        margin = _float(row.get("fracture_initiation_margin_Pa"))
        if pressure is not None and pressure > 0.0:
            return {
                "time_s": _float(row.get("time_s")),
                "pressure_Pa": pressure,
                "sigma_theta_Pa": sigma,
                "margin_Pa": margin,
            }
    return {
        "time_s": None,
        "pressure_Pa": None,
        "sigma_theta_Pa": None,
        "margin_Pa": None,
    }


def _classify(max_pressure: float | None, initiation_time_s: float | None) -> str:
    if max_pressure is None or initiation_time_s is None:
        return "INCONCLUSIVE"
    if not math.isfinite(max_pressure) or not math.isfinite(initiation_time_s):
        return "SIGMA_THETA_STATIC_ERROR"
    rel = _relative_error(LEGACY_MAX_PRESSURE_PA, max_pressure)
    if rel is None:
        return "INCONCLUSIVE"
    if abs(rel) <= 0.10 and abs(initiation_time_s - LEGACY_OPEN_TIME_S) <= 30.0:
        return "SIGMA_THETA_STATIC_EFFECTIVE"
    if initiation_time_s < LEGACY_OPEN_TIME_S - 30.0:
        return "SIGMA_THETA_STATIC_OPENED_TOO_EARLY"
    if initiation_time_s > LEGACY_OPEN_TIME_S + 30.0:
        return "SIGMA_THETA_STATIC_OPENED_TOO_LATE"
    if abs(rel) > 0.10:
        return "SIGMA_THETA_STATIC_PARTIAL"
    return "INCONCLUSIVE"


def _sum(rows: list[dict[str, str]], field: str) -> float:
    return sum(_values(rows, field))


def _range(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values), "mean": mean(values)}


def _plot_xy(
    path: Path,
    series: list[tuple[str, list[dict[str, Any]], str, str]],
    title: str,
    xlabel: str,
    ylabel: str,
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
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    legacy_points = _legacy_points(legacy_rows)
    modern_points = _modern_points(modern_rows)
    pressure_series: list[tuple[str, list[dict[str, Any]], str, str]] = [
        ("Legacy audit pw_Pa", legacy_points, "time_s", "pressure_Pa"),
        ("10.19A sigma_theta_static", modern_points, "time_s", "pressure_Pa"),
    ]

    for label, path in (
        ("10.18B", args.modern_10_18b_csv),
        ("10.18C", args.modern_10_18c_csv),
        ("10.18E", args.modern_10_18e_csv),
    ):
        if path:
            pressure_series.append(
                (label, _modern_points(_read_csv(Path(path))), "time_s", "pressure_Pa")
            )

    legacy_max = _max(legacy_rows, "pw_Pa") or LEGACY_MAX_PRESSURE_PA
    modern_max = _max(modern_rows, "wellbore_pressure_Pa")
    initiation = _first_initiation(modern_rows)
    classification = _classify(modern_max, initiation["time_s"])

    summary_rows = [
        {
            "phase": PHASE,
            "classification": classification,
            "max_pressure_legacy_Pa": legacy_max,
            "max_pressure_10_19A_Pa": modern_max,
            "relative_error_max_10_19A": _relative_error(legacy_max, modern_max),
            "fracture_initiation_time_s": initiation["time_s"],
            "fracture_initiation_pressure_Pa": initiation["pressure_Pa"],
            "fracture_initiation_sigma_theta_Pa": initiation["sigma_theta_Pa"],
            "fracture_initiation_margin_Pa": initiation["margin_Pa"],
            "max_fracture_volume_m3": _max(modern_rows, "fracture_volume_m3"),
            "max_leakoff_volume_m3": _max(modern_rows, "leakoff_volume_m3"),
            "sum_fracture_increment_m3": _sum(
                modern_rows, "balance_fracture_volume_increment_m3"
            ),
            "sum_leakoff_increment_m3": _sum(
                modern_rows, "balance_leakoff_volume_increment_m3"
            ),
        }
    ]
    _write_csv(
        output_dir / "phase10_19a_summary.csv",
        summary_rows,
        list(summary_rows[0].keys()),
    )

    plots = {
        "pressure_vs_time_sigma_theta_static.png": _plot_xy(
            output_dir / "pressure_vs_time_sigma_theta_static.png",
            pressure_series,
            "Phase 10.19A pressure diagnostic",
            "time_s",
            "pressure_Pa",
        ),
        "injected_volume_vs_pressure_sigma_theta_static.png": _plot_xy(
            output_dir / "injected_volume_vs_pressure_sigma_theta_static.png",
            [
                ("Legacy audit", legacy_points, "injected_volume_m3", "pressure_Pa"),
                (
                    "10.19A sigma_theta_static",
                    modern_points,
                    "injected_volume_m3",
                    "pressure_Pa",
                ),
            ],
            "Phase 10.19A injected volume versus pressure",
            "injected_volume_m3",
            "pressure_Pa",
        ),
        "sigma_theta_margin_static.png": _plot_xy(
            output_dir / "sigma_theta_margin_static.png",
            [
                ("wellbore_pressure_Pa", modern_points, "time_s", "pressure_Pa"),
                ("sigma_theta_static_Pa", modern_points, "time_s", "sigma_theta_Pa"),
                ("margin_Pa", modern_points, "time_s", "margin_Pa"),
            ],
            "Phase 10.19A sigma-theta static margin",
            "time_s",
            "Pa",
        ),
        "volume_balance_sigma_theta_static.png": _plot_xy(
            output_dir / "volume_balance_sigma_theta_static.png",
            [
                (
                    "injected_increment",
                    [
                        {
                            "time_s": _float(row.get("time_s")),
                            "value": _float(
                                row.get("balance_injected_volume_increment_m3")
                            ),
                        }
                        for row in modern_rows
                    ],
                    "time_s",
                    "value",
                ),
                (
                    "fracture_increment",
                    [
                        {
                            "time_s": _float(row.get("time_s")),
                            "value": _float(
                                row.get("balance_fracture_volume_increment_m3")
                            ),
                        }
                        for row in modern_rows
                    ],
                    "time_s",
                    "value",
                ),
                (
                    "leakoff_increment",
                    [
                        {
                            "time_s": _float(row.get("time_s")),
                            "value": _float(
                                row.get("balance_leakoff_volume_increment_m3")
                            ),
                        }
                        for row in modern_rows
                    ],
                    "time_s",
                    "value",
                ),
                (
                    "effective_increment",
                    [
                        {
                            "time_s": _float(row.get("time_s")),
                            "value": _float(
                                row.get("balance_effective_volume_increment_m3")
                            ),
                        }
                        for row in modern_rows
                    ],
                    "time_s",
                    "value",
                ),
            ],
            "Phase 10.19A volume-balance components",
            "time_s",
            "m3",
        ),
    }

    metadata = {
        "phase": PHASE,
        "status": "PHASE10_19A_SIGMA_THETA_STATIC_DIAGNOSTIC_COMPLETE",
        "physical_validation": False,
        "runtime_default_changed": False,
        "classification": classification,
        "metrics": summary_rows[0],
        "pressure_range_modern_Pa": _range(_values(modern_rows, "wellbore_pressure_Pa")),
        "plots": plots,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "sigma_theta_static is a YAML-supplied static proxy, not runtime saltcreep stress.",
            "No Zamora, casing compliance, compositional fluid or temporal salt coupling was implemented.",
        ],
    }
    (output_dir / "phase10_19a_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.19A static sigma-theta LOT/PKN diagnostic."
    )
    parser.add_argument("--legacy-csv", required=True)
    parser.add_argument("--modern-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--modern-10-18b-csv")
    parser.add_argument("--modern-10-18c-csv")
    parser.add_argument("--modern-10-18e-csv")
    return parser


def main() -> int:
    metadata = run_comparison(build_parser().parse_args())
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
