from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


PHASE = "10.18E"
LEGACY_MAX_PRESSURE_PA = 69.0358361743195e6
KNOWN_10_18B_MAX_PRESSURE_PA = 82.129237e6
KNOWN_10_18C_MAX_PRESSURE_PA = 26.732215e6


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


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
        selected = max(
            grouped[time_s],
            key=lambda row: _finite_float(row.get("pw_Pa")) or -math.inf,
        )
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": _finite_float(selected.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(selected.get("pw_Pa")),
            }
        )
    return points


def _modern_points(rows: list[dict[str, str]], pressure_field: str) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        pressure = _finite_float(row.get(pressure_field))
        if time_s is None or pressure is None:
            continue
        points.append(
            {
                "time_s": time_s,
                "injected_volume_m3": _finite_float(row.get("injected_volume_m3")),
                "pressure_Pa": pressure,
            }
        )
    return points


def _max_pressure(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _relative_error(reference: float | None, target: float | None) -> float | None:
    if reference is None or target is None or reference == 0.0:
        return None
    return (target - reference) / abs(reference)


def _sum_field(rows: list[dict[str, str]], field: str) -> float:
    return sum(_values(rows, field))


def _first_sink_event(rows: list[dict[str, str]]) -> dict[str, float | None]:
    for row in rows:
        fracture = _finite_float(row.get("balance_fracture_volume_increment_m3")) or 0.0
        leakoff = _finite_float(row.get("balance_leakoff_volume_increment_m3")) or 0.0
        if fracture > 0.0 or leakoff > 0.0:
            return {
                "time_s": _finite_float(row.get("time_s")),
                "pressure_Pa": _finite_float(row.get("wellbore_pressure_Pa")),
                "fracture_increment_m3": fracture,
                "leakoff_increment_m3": leakoff,
            }
    return {
        "time_s": None,
        "pressure_Pa": None,
        "fracture_increment_m3": None,
        "leakoff_increment_m3": None,
    }


def _classify(max_10_18e: float | None) -> str:
    if max_10_18e is None or not math.isfinite(max_10_18e):
        return "STATIC_BREAKDOWN_ERROR"
    rel = _relative_error(LEGACY_MAX_PRESSURE_PA, max_10_18e)
    if rel is None:
        return "INCONCLUSIVE"
    if abs(rel) <= 0.10:
        return "STATIC_BREAKDOWN_EFFECTIVE"
    diff_b = abs(KNOWN_10_18B_MAX_PRESSURE_PA - LEGACY_MAX_PRESSURE_PA)
    diff_c = abs(KNOWN_10_18C_MAX_PRESSURE_PA - LEGACY_MAX_PRESSURE_PA)
    diff_e = abs(max_10_18e - LEGACY_MAX_PRESSURE_PA)
    if max_10_18e <= LEGACY_MAX_PRESSURE_PA * 0.55:
        return "STATIC_BREAKDOWN_OPENED_TOO_EARLY"
    if max_10_18e >= KNOWN_10_18B_MAX_PRESSURE_PA * 0.98:
        return "STATIC_BREAKDOWN_OPENED_TOO_LATE"
    if diff_e < min(diff_b, diff_c):
        return "STATIC_BREAKDOWN_PARTIAL"
    if diff_e >= diff_b:
        return "STATIC_BREAKDOWN_NO_IMPROVEMENT"
    return "INCONCLUSIVE"


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
    markers: list[tuple[str, float | None, float | None]] | None = None,
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
    if markers:
        for label, xvalue, yvalue in markers:
            if xvalue is not None:
                ax.axvline(xvalue, linestyle="--", linewidth=1.0, label=label)
            if yvalue is not None:
                ax.axhline(yvalue, linestyle=":", linewidth=1.0)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.text(0.02, 0.02, caveat, transform=ax.transAxes, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def _volume_balance_points(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    fields = [
        "balance_injected_volume_increment_m3",
        "balance_fracture_volume_increment_m3",
        "balance_leakoff_volume_increment_m3",
        "balance_effective_volume_increment_m3",
    ]
    points: list[dict[str, Any]] = []
    for row in rows:
        point = {"time_s": _finite_float(row.get("time_s"))}
        for field in fields:
            point[field] = _finite_float(row.get(field))
        points.append(point)
    return points


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    threshold = _read_json(Path(args.threshold_json))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    legacy_points = _legacy_points(legacy_rows)
    modern_points = _modern_points(modern_rows, "wellbore_pressure_Pa")

    optional_series: list[tuple[str, list[dict[str, Any]], str, str]] = [
        ("Legacy audit pw_Pa", legacy_points, "time_s", "pressure_Pa"),
        ("Modern 10.18E static breakdown", modern_points, "time_s", "pressure_Pa"),
    ]
    if args.modern_10_18b_csv:
        rows_10_18b = _read_csv(Path(args.modern_10_18b_csv))
        optional_series.append(
            (
                "Modern 10.18B",
                _modern_points(rows_10_18b, "wellbore_pressure_Pa"),
                "time_s",
                "pressure_Pa",
            )
        )
    if args.modern_10_18c_csv:
        rows_10_18c = _read_csv(Path(args.modern_10_18c_csv))
        optional_series.append(
            (
                "Modern 10.18C placeholder",
                _modern_points(rows_10_18c, "wellbore_pressure_Pa"),
                "time_s",
                "pressure_Pa",
            )
        )

    legacy_max = _max_pressure(legacy_rows, "pw_Pa")
    modern_max = _max_pressure(modern_rows, "wellbore_pressure_Pa")
    first_sink = _first_sink_event(modern_rows)
    classification = _classify(modern_max)

    breakdown_time_s = threshold.get("breakdown_time_s")
    breakdown_pressure_Pa = threshold.get("breakdown_pressure_Pa")
    plots = {
        "pressure_vs_time_static_breakdown": _plot_xy(
            output_dir / "pressure_vs_time_static_breakdown.png",
            optional_series[:2],
            "Phase 10.18E - Static legacy breakdown threshold",
            "time_s",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - static legacy threshold; not final sigma-theta runtime criterion.",
            [("legacy breakdown time", breakdown_time_s, breakdown_pressure_Pa)],
        ),
        "injected_volume_vs_pressure_static_breakdown": _plot_xy(
            output_dir / "injected_volume_vs_pressure_static_breakdown.png",
            [
                ("Legacy audit pw_Pa", legacy_points, "injected_volume_m3", "pressure_Pa"),
                (
                    "Modern 10.18E static breakdown",
                    modern_points,
                    "injected_volume_m3",
                    "pressure_Pa",
                ),
            ],
            "Phase 10.18E - Pressure vs injected volume",
            "injected_volume_m3",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - no physical fracture validation.",
        ),
        "pressure_comparison_all_modes_static_breakdown": _plot_xy(
            output_dir / "pressure_comparison_all_modes_static_breakdown.png",
            optional_series,
            "Phase 10.18E - Pressure comparison",
            "time_s",
            "pressure_Pa",
            "DIAGNOSTIC ONLY - mixed diagnostic modes.",
            [("legacy breakdown time", breakdown_time_s, breakdown_pressure_Pa)],
        ),
    }

    balance = _volume_balance_points(modern_rows)
    plots["volume_balance_static_breakdown"] = _plot_xy(
        output_dir / "volume_balance_static_breakdown.png",
        [
            ("injected increment", balance, "time_s", "balance_injected_volume_increment_m3"),
            ("fracture increment", balance, "time_s", "balance_fracture_volume_increment_m3"),
            ("leakoff increment", balance, "time_s", "balance_leakoff_volume_increment_m3"),
            ("effective increment", balance, "time_s", "balance_effective_volume_increment_m3"),
        ],
        "Phase 10.18E - Volume balance increments",
        "time_s",
        "volume_increment_m3",
        "DIAGNOSTIC ONLY - static threshold.",
    )

    metadata = {
        "phase": PHASE,
        "status": "PHASE10_18E_STATIC_LEGACY_BREAKDOWN_DIAGNOSTIC_COMPLETE",
        "classification": classification,
        "physical_validation": False,
        "sigma_theta_runtime": False,
        "legacy": {
            "pressure_field": "pw_Pa",
            "max_pressure_Pa": legacy_max,
            "time_range_s": _range(_values(legacy_rows, "time_s")),
        },
        "modern_10_18e": {
            "pressure_field": "wellbore_pressure_Pa",
            "max_pressure_Pa": modern_max,
            "relative_error_vs_legacy_max": _relative_error(legacy_max, modern_max),
            "time_range_s": _range(_values(modern_rows, "time_s")),
            "max_fracture_volume_m3": max(_values(modern_rows, "fracture_volume_m3"), default=None),
            "max_leakoff_volume_m3": max(_values(modern_rows, "leakoff_volume_m3"), default=None),
            "total_fracture_sink_increment_m3": _sum_field(
                modern_rows, "balance_fracture_volume_increment_m3"
            ),
            "total_leakoff_sink_increment_m3": _sum_field(
                modern_rows, "balance_leakoff_volume_increment_m3"
            ),
            "total_effective_increment_m3": _sum_field(
                modern_rows, "balance_effective_volume_increment_m3"
            ),
            "first_sink_event": first_sink,
        },
        "known_reference_modes": {
            "max_pressure_legacy_Pa": LEGACY_MAX_PRESSURE_PA,
            "max_pressure_10_18B_Pa": KNOWN_10_18B_MAX_PRESSURE_PA,
            "max_pressure_10_18C_Pa": KNOWN_10_18C_MAX_PRESSURE_PA,
        },
        "threshold": threshold,
        "plots": plots,
        "caveats": [
            "Static threshold is derived from legacy audit data.",
            "This is not the final sigma-theta runtime criterion.",
            "The modern PknModel currently consumes a delta pressure threshold.",
            "No physical validation of fracture, damage, or salt response is declared.",
        ],
    }

    summary_rows = [
        {
            "phase": "Legacy",
            "max_pressure_MPa": LEGACY_MAX_PRESSURE_PA / 1.0e6,
            "relative_error_vs_legacy": 0.0,
            "classification": "reference",
        },
        {
            "phase": "10.18B",
            "max_pressure_MPa": KNOWN_10_18B_MAX_PRESSURE_PA / 1.0e6,
            "relative_error_vs_legacy": _relative_error(
                LEGACY_MAX_PRESSURE_PA, KNOWN_10_18B_MAX_PRESSURE_PA
            ),
            "classification": "known_reference",
        },
        {
            "phase": "10.18C",
            "max_pressure_MPa": KNOWN_10_18C_MAX_PRESSURE_PA / 1.0e6,
            "relative_error_vs_legacy": _relative_error(
                LEGACY_MAX_PRESSURE_PA, KNOWN_10_18C_MAX_PRESSURE_PA
            ),
            "classification": "known_reference",
        },
        {
            "phase": "10.18E",
            "max_pressure_MPa": modern_max / 1.0e6 if modern_max is not None else None,
            "relative_error_vs_legacy": _relative_error(LEGACY_MAX_PRESSURE_PA, modern_max),
            "classification": classification,
        },
    ]
    _write_csv(
        output_dir / "phase10_18e_summary.csv",
        summary_rows,
        ["phase", "max_pressure_MPa", "relative_error_vs_legacy", "classification"],
    )
    (output_dir / "phase10_18e_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.18E static legacy breakdown diagnostic."
    )
    parser.add_argument("--legacy-csv", required=True)
    parser.add_argument("--modern-csv", required=True)
    parser.add_argument("--threshold-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--modern-10-18b-csv")
    parser.add_argument("--modern-10-18c-csv")
    return parser


def main() -> int:
    parser = build_parser()
    metadata = run_comparison(parser.parse_args())
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
