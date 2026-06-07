from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


LEGACY_PRESSURE_LABEL = "Legacy pw_Pa — LOT_Tese audit run"
MODERN_PRESSURE_LABEL = "Modern net_pressure_Pa — lot-sim, semantic equivalence not confirmed"

CAVEATS = [
    "Legacy pw_Pa and modern net_pressure_Pa may differ semantically.",
    "Injected volume conversion depends on audited legacy flow-rate conversion.",
    "Annular volume comparison reports per-radian and total volumes explicitly.",
    "This phase is diagnostic only and does not validate LOT physics.",
    "No sigmaTheta/pw/margin/opened equivalence is declared.",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        return
    names = fieldnames if fieldnames is not None else list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names)
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


def _range(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values), "mean": mean(values)}


def _aggregate_legacy_by_time(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        if time_s is None:
            continue
        grouped.setdefault(time_s, []).append(row)

    aggregated: list[dict[str, Any]] = []
    for time_s in sorted(grouped):
        candidates = grouped[time_s]
        selected = max(candidates, key=lambda item: _finite_float(item.get("injected_volume_m3")) or 0.0)
        aggregated.append(
            {
                "time_s": time_s,
                "time_min": _finite_float(selected.get("time_min")),
                "layer": selected.get("layer", ""),
                "annular_index": selected.get("annular_index", ""),
                "injected_volume_m3": _finite_float(selected.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(selected.get("pw_Pa")),
                "pressure_field": "pw_Pa",
                "source": "legacy",
                "label": LEGACY_PRESSURE_LABEL,
            }
        )
    return aggregated


def _modern_points(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in rows:
        points.append(
            {
                "time_s": _finite_float(row.get("time_s")),
                "injected_volume_m3": _finite_float(row.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(row.get("net_pressure_Pa")),
                "pressure_field": "net_pressure_Pa",
                "source": "modern",
                "label": MODERN_PRESSURE_LABEL,
            }
        )
    return [point for point in points if point["time_s"] is not None]


def _load_modern_result(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _legacy_initial_volume(rows: list[dict[str, str]]) -> tuple[float | None, float | None, str, str]:
    nonzero = [
        _finite_float(row.get("initial_annular_volume_m3"))
        for row in rows
        if (_finite_float(row.get("injected_volume_m3")) or 0.0) > 0.0
    ]
    values = [value for value in nonzero if value is not None]
    if not values:
        return None, None, "NOT_FOUND", "No injected legacy annular row with initial_annular_volume_m3"
    total = values[0]
    return (
        total / (2.0 * math.pi),
        total,
        "DERIVED_FROM_LEGACY_GEOMETRY",
        "Selected from the injected annular audit row; legacy Vi is per-radian internally",
    )


def _modern_initial_volume(result: dict[str, Any]) -> tuple[float | None, float | None, str, str]:
    summary = result.get("summary", {}) if isinstance(result, dict) else {}
    total = summary.get("initial_annular_volume_m3")
    per_radian = summary.get("initial_annular_volume_per_radian_m3")
    total_value = float(total) if isinstance(total, (int, float)) and math.isfinite(float(total)) else None
    per_radian_value = (
        float(per_radian)
        if isinstance(per_radian, (int, float)) and math.isfinite(float(per_radian))
        else None
    )
    if total_value is None and per_radian_value is not None:
        total_value = 2.0 * math.pi * per_radian_value
    if per_radian_value is None and total_value is not None:
        per_radian_value = total_value / (2.0 * math.pi)
    if total_value is not None and per_radian_value is not None:
        return (
            per_radian_value,
            total_value,
            "EXPORTED_BY_MODERN",
            "Read from modern result.json summary",
        )
    return None, None, "NOT_FOUND", "Modern result.json does not export initial annular volume"


def _plot_pressure_vs_time(path: Path, legacy: list[dict[str, Any]], modern: list[dict[str, Any]]) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        [point["time_s"] for point in legacy if point["pressure_Pa"] is not None],
        [point["pressure_Pa"] for point in legacy if point["pressure_Pa"] is not None],
        label=LEGACY_PRESSURE_LABEL,
    )
    ax.plot(
        [point["time_s"] for point in modern if point["pressure_Pa"] is not None],
        [point["pressure_Pa"] for point in modern if point["pressure_Pa"] is not None],
        label=MODERN_PRESSURE_LABEL,
    )
    ax.set_title("LOT Diagnostic — Pressure vs Time — BUZ-67D-PKN")
    ax.set_xlabel("time_s")
    ax.set_ylabel("pressure_Pa")
    ax.text(0.02, 0.02, "DIAGNOSTIC ONLY — not physical validation", transform=ax.transAxes, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def _plot_volume_vs_pressure(path: Path, legacy: list[dict[str, Any]], modern: list[dict[str, Any]]) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        [point["injected_volume_m3"] for point in legacy if point["pressure_Pa"] is not None],
        [point["pressure_Pa"] for point in legacy if point["pressure_Pa"] is not None],
        label=LEGACY_PRESSURE_LABEL,
    )
    ax.plot(
        [point["injected_volume_m3"] for point in modern if point["pressure_Pa"] is not None],
        [point["pressure_Pa"] for point in modern if point["pressure_Pa"] is not None],
        label=MODERN_PRESSURE_LABEL,
    )
    ax.set_title("LOT Diagnostic — Injected Volume vs Pressure — BUZ-67D-PKN")
    ax.set_xlabel("injected_volume_m3")
    ax.set_ylabel("pressure_Pa")
    ax.text(
        0.02,
        0.02,
        "DIAGNOSTIC ONLY — pw_Pa and net_pressure_Pa may differ semantically",
        transform=ax.transAxes,
        fontsize=9,
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def _plot_annular_volume(path: Path, legacy_volume: float, modern_volume: float) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(["legacy", "modern"], [legacy_volume, modern_volume])
    ax.set_title("LOT Diagnostic — Initial Annular Volume — BUZ-67D-PKN")
    ax.set_ylabel("initial_annular_volume_m3")
    ax.text(0.02, 0.02, "DIAGNOSTIC ONLY — not physical validation", transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = args.suffix or ""

    legacy_rows = _read_csv(Path(args.legacy_audit_csv))
    modern_rows = _read_csv(Path(args.modern_timeseries_csv))
    modern_result = _load_modern_result(Path(args.modern_result_json) if args.modern_result_json else None)

    legacy = _aggregate_legacy_by_time(legacy_rows)
    modern = _modern_points(modern_rows)

    volume_pressure_rows = []
    for point in legacy + modern:
        volume_pressure_rows.append(
            {
                "source": point["source"],
                "time_s": point["time_s"],
                "injected_volume_m3": point.get("injected_volume_m3"),
                "pressure_Pa": point.get("pressure_Pa"),
                "pressure_field": point.get("pressure_field"),
                "notes": point.get("label"),
            }
        )
    volume_pressure_csv = output_dir / f"injected_volume_vs_pressure{suffix}.csv"
    _write_csv(volume_pressure_csv, volume_pressure_rows)

    legacy_volume_per_radian, legacy_volume, legacy_volume_status, legacy_volume_notes = _legacy_initial_volume(legacy_rows)
    modern_volume_per_radian, modern_volume, modern_volume_status, modern_volume_notes = _modern_initial_volume(modern_result)
    annular_rows = [
        {
            "source": "legacy",
            "volume_per_radian_m3": legacy_volume_per_radian if legacy_volume_per_radian is not None else "",
            "volume_total_m3": legacy_volume if legacy_volume is not None else "",
            "status": legacy_volume_status,
            "method": legacy_volume_status,
            "notes": legacy_volume_notes,
        },
        {
            "source": "modern",
            "volume_per_radian_m3": modern_volume_per_radian if modern_volume_per_radian is not None else "",
            "volume_total_m3": modern_volume if modern_volume is not None else "",
            "status": modern_volume_status,
            "method": modern_volume_status,
            "notes": modern_volume_notes,
        },
    ]
    annular_status = "BLOCKED_MISSING_VOLUME"
    if legacy_volume is not None and modern_volume is not None:
        difference = legacy_volume - modern_volume
        percent = (difference / modern_volume * 100.0) if modern_volume != 0.0 else None
        annular_rows.extend(
            [
                {
                    "source": "difference_abs_m3",
                    "volume_per_radian_m3": (
                        abs((legacy_volume_per_radian or 0.0) - (modern_volume_per_radian or 0.0))
                        if legacy_volume_per_radian is not None and modern_volume_per_radian is not None
                        else ""
                    ),
                    "volume_total_m3": abs(difference),
                    "status": "DONE",
                    "method": "legacy_minus_modern",
                    "notes": "",
                },
                {
                    "source": "difference_percent",
                    "volume_per_radian_m3": percent if percent is not None else "",
                    "volume_total_m3": percent if percent is not None else "",
                    "status": "DONE",
                    "method": "legacy_minus_modern_over_modern",
                    "notes": "",
                },
            ]
        )
        annular_status = "DONE"
    _write_csv(
        output_dir / "annular_volume_comparison.csv",
        annular_rows,
        ["source", "volume_per_radian_m3", "volume_total_m3", "status", "method", "notes"],
    )

    volume_plot = _plot_volume_vs_pressure(output_dir / f"injected_volume_vs_pressure{suffix}.png", legacy, modern)
    pressure_plot = _plot_pressure_vs_time(output_dir / f"pressure_vs_time{suffix}.png", legacy, modern)
    annular_plot = False
    if legacy_volume is not None and modern_volume is not None:
        annular_plot = _plot_annular_volume(output_dir / "annular_volume_comparison.png", legacy_volume, modern_volume)

    legacy_pressures = [point["pressure_Pa"] for point in legacy if point["pressure_Pa"] is not None]
    modern_pressures = [point["pressure_Pa"] for point in modern if point["pressure_Pa"] is not None]
    metadata = {
        "phase": "10.15B",
        "comparison_type": "audit_run_visual_diagnostic",
        "legacy_compiled": True,
        "legacy_run_completed": True,
        "legacy_instrumented": True,
        "legacy_instrumentation_committable": False,
        "physical_validation": False,
        "numeric_equivalence": False,
        "pressure_semantic_equivalence": False,
        "volume_pressure_plot_generated": volume_plot,
        "pressure_time_plot_generated": pressure_plot,
        "annular_volume_comparison_status": annular_status,
        "annular_volume_plot_generated": annular_plot,
        "legacy": {
            "n_raw_rows": len(legacy_rows),
            "n_aggregated_times": len(legacy),
            "time_s_range": _range([point["time_s"] for point in legacy if point["time_s"] is not None]),
            "pw_Pa_range": _range(legacy_pressures),
            "initial_annular_volume_status": legacy_volume_status,
            "initial_annular_volume_per_radian_m3": legacy_volume_per_radian,
            "initial_annular_volume_m3": legacy_volume,
        },
        "modern": {
            "n_rows": len(modern),
            "time_s_range": _range([point["time_s"] for point in modern if point["time_s"] is not None]),
            "net_pressure_Pa_range": _range(modern_pressures),
            "initial_annular_volume_status": modern_volume_status,
            "initial_annular_volume_per_radian_m3": modern_volume_per_radian,
            "initial_annular_volume_m3": modern_volume,
        },
        "outputs": {
            "injected_volume_vs_pressure_csv": str(volume_pressure_csv),
            "injected_volume_vs_pressure_png": str(output_dir / f"injected_volume_vs_pressure{suffix}.png"),
            "pressure_vs_time_png": str(output_dir / f"pressure_vs_time{suffix}.png"),
            "annular_volume_comparison_csv": str(output_dir / "annular_volume_comparison.csv"),
            "annular_volume_comparison_png": str(output_dir / "annular_volume_comparison.png") if annular_plot else None,
        },
        "caveats": CAVEATS,
    }
    with (output_dir / "level1b_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    legacy_audit_dir = output_dir / "legacy_audit"
    legacy_audit_dir.mkdir(parents=True, exist_ok=True)
    with (legacy_audit_dir / "buz67d_audit_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Level 1B legacy-modern visual diagnostics.")
    parser.add_argument("--legacy-audit-csv", required=True)
    parser.add_argument("--modern-timeseries-csv", required=True)
    parser.add_argument("--modern-result-json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--suffix", default="")
    return parser


def main() -> int:
    parser = build_parser()
    metadata = run_comparison(parser.parse_args())
    print(f"level1b_metadata={metadata['outputs']['injected_volume_vs_pressure_csv']}")
    print(f"volume_pressure_plot_generated={metadata['volume_pressure_plot_generated']}")
    print(f"pressure_time_plot_generated={metadata['pressure_time_plot_generated']}")
    print(f"annular_volume_comparison_status={metadata['annular_volume_comparison_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
