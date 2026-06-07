from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


PHASE = "10.18A"
CLASSIFICATION_CHOICES = {
    "VOLUMETRIC_BALANCE_CLOSER_TO_LEGACY",
    "VOLUMETRIC_BALANCE_SIMILAR_TO_PKN_DIRECT",
    "VOLUMETRIC_BALANCE_WORSE_THAN_PKN_DIRECT",
    "VOLUMETRIC_BALANCE_ERROR_DETECTED",
    "INCONCLUSIVE_MISSING_REFERENCE",
}


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


def _finite_values(rows: list[dict[str, str]], field: str) -> list[float]:
    values = [_finite_float(row.get(field)) for row in rows]
    return [value for value in values if value is not None]


def _range(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values), "mean": mean(values)}


def _pressure_range(rows: list[dict[str, str]], field: str) -> dict[str, float] | None:
    return _range(_finite_values(rows, field))


def _span(values: list[float]) -> float | None:
    if not values:
        return None
    return max(values) - min(values)


def _aggregate_legacy_by_time(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        if time_s is None:
            continue
        grouped.setdefault(time_s, []).append(row)

    points: list[dict[str, Any]] = []
    for time_s in sorted(grouped):
        candidates = grouped[time_s]
        selected = max(candidates, key=lambda item: _finite_float(item.get("injected_volume_m3")) or 0.0)
        points.append(
            {
                "source": "legacy_audit",
                "time_s": time_s,
                "injected_volume_m3": _finite_float(selected.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(selected.get("pw_Pa")),
            }
        )
    return points


def _modern_points(rows: list[dict[str, str]], pressure_field: str, source: str) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in rows:
        points.append(
            {
                "source": source,
                "time_s": _finite_float(row.get("time_s")),
                "injected_volume_m3": _finite_float(row.get("injected_volume_m3")),
                "pressure_Pa": _finite_float(row.get(pressure_field)),
            }
        )
    return [point for point in points if point["time_s"] is not None]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(path: Path, metadata: dict[str, Any]) -> None:
    rows = [
        {
            "metric": "classification",
            "legacy": "",
            "pkn_direct": "",
            "volumetric_balance": metadata["classification"],
        },
        {
            "metric": "max_pressure_Pa",
            "legacy": metadata["legacy"].get("max_pressure_Pa"),
            "pkn_direct": metadata.get("pkn_direct", {}).get("max_pressure_Pa"),
            "volumetric_balance": metadata["volumetric_balance"].get("max_pressure_Pa"),
        },
        {
            "metric": "pressure_range_Pa",
            "legacy": metadata["legacy"].get("pressure_range_Pa"),
            "pkn_direct": metadata.get("pkn_direct", {}).get("pressure_range_Pa"),
            "volumetric_balance": metadata["volumetric_balance"].get("pressure_range_Pa"),
        },
        {
            "metric": "n_records",
            "legacy": metadata["legacy"].get("n_records"),
            "pkn_direct": metadata.get("pkn_direct", {}).get("n_records"),
            "volumetric_balance": metadata["volumetric_balance"].get("n_records"),
        },
    ]
    _write_csv(path, rows, ["metric", "legacy", "pkn_direct", "volumetric_balance"])


def _max_pressure_difference(reference: dict[str, float] | None, target: dict[str, float] | None) -> dict[str, float | None]:
    if not reference or not target:
        return {"absolute_Pa": None, "relative": None}
    absolute = abs(target["max"] - reference["max"])
    relative = absolute / abs(reference["max"]) if reference["max"] != 0.0 else None
    return {"absolute_Pa": absolute, "relative": relative}


def _classify(
    legacy_range: dict[str, float] | None,
    direct_range: dict[str, float] | None,
    volumetric_range: dict[str, float] | None,
) -> str:
    if legacy_range is None or volumetric_range is None:
        return "INCONCLUSIVE_MISSING_REFERENCE"
    if volumetric_range["max"] < 0.0 or not math.isfinite(volumetric_range["max"]):
        return "VOLUMETRIC_BALANCE_ERROR_DETECTED"
    if direct_range is None:
        return "INCONCLUSIVE_MISSING_REFERENCE"

    direct_diff = abs(direct_range["max"] - legacy_range["max"])
    volumetric_diff = abs(volumetric_range["max"] - legacy_range["max"])
    tolerance = max(1.0, abs(legacy_range["max"])) * 0.05
    if volumetric_diff + tolerance < direct_diff:
        return "VOLUMETRIC_BALANCE_CLOSER_TO_LEGACY"
    if direct_diff + tolerance < volumetric_diff:
        return "VOLUMETRIC_BALANCE_WORSE_THAN_PKN_DIRECT"
    return "VOLUMETRIC_BALANCE_SIMILAR_TO_PKN_DIRECT"


def _plot_volume_vs_pressure(
    path: Path,
    legacy_points: list[dict[str, Any]],
    volumetric_points: list[dict[str, Any]],
    direct_points: list[dict[str, Any]] | None,
) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        [p["injected_volume_m3"] for p in legacy_points if p["pressure_Pa"] is not None],
        [p["pressure_Pa"] for p in legacy_points if p["pressure_Pa"] is not None],
        label="Legacy audit: injected_volume_m3 vs pw_Pa",
    )
    if direct_points:
        ax.plot(
            [p["injected_volume_m3"] for p in direct_points if p["pressure_Pa"] is not None],
            [p["pressure_Pa"] for p in direct_points if p["pressure_Pa"] is not None],
            label="Modern pkn_direct: injected_volume_m3 vs net_pressure_Pa",
        )
    ax.plot(
        [p["injected_volume_m3"] for p in volumetric_points if p["pressure_Pa"] is not None],
        [p["pressure_Pa"] for p in volumetric_points if p["pressure_Pa"] is not None],
        label="Modern volumetric_balance: injected_volume_m3 vs wellbore_pressure_Pa",
    )
    ax.set_title("Phase 10.18A - Volume vs Pressure - Volumetric Balance Diagnostic")
    ax.set_xlabel("injected_volume_m3")
    ax.set_ylabel("pressure_Pa")
    ax.text(0.02, 0.02, "DIAGNOSTIC ONLY - pw_Pa and model pressure definitions may differ.", transform=ax.transAxes, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def _plot_pressure_vs_time(
    path: Path,
    legacy_points: list[dict[str, Any]],
    volumetric_points: list[dict[str, Any]],
    direct_points: list[dict[str, Any]] | None,
) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        [p["time_s"] for p in legacy_points if p["pressure_Pa"] is not None],
        [p["pressure_Pa"] for p in legacy_points if p["pressure_Pa"] is not None],
        label="Legacy audit: time_s vs pw_Pa",
    )
    if direct_points:
        ax.plot(
            [p["time_s"] for p in direct_points if p["pressure_Pa"] is not None],
            [p["pressure_Pa"] for p in direct_points if p["pressure_Pa"] is not None],
            label="Modern pkn_direct: time_s vs net_pressure_Pa",
        )
    ax.plot(
        [p["time_s"] for p in volumetric_points if p["pressure_Pa"] is not None],
        [p["pressure_Pa"] for p in volumetric_points if p["pressure_Pa"] is not None],
        label="Modern volumetric_balance: time_s vs wellbore_pressure_Pa",
    )
    ax.set_title("Phase 10.18A - Pressure vs Time - Volumetric Balance Diagnostic")
    ax.set_xlabel("time_s")
    ax.set_ylabel("pressure_Pa")
    ax.text(0.02, 0.02, "DIAGNOSTIC ONLY - not physical validation.", transform=ax.transAxes, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def _plot_balance_components(path: Path, rows: list[dict[str, str]]) -> tuple[bool, list[str], list[str]]:
    fields = [
        "balance_injected_volume_increment_m3",
        "balance_effective_volume_increment_m3",
        "balance_fracture_volume_increment_m3",
        "balance_leakoff_volume_increment_m3",
        "balance_delta_pressure_Pa",
    ]
    if not rows:
        return False, [], fields
    available = [field for field in fields if field in rows[0] and _finite_values(rows, field)]
    missing = [field for field in fields if field not in available]
    if not available:
        return False, [], missing

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False, available, missing

    times = _finite_values(rows, "time_s")
    fig, ax = plt.subplots(figsize=(9, 5))
    for field in available:
        values = _finite_values(rows, field)
        if len(values) == len(times):
            ax.plot(times, values, label=field)
    ax.set_title("Phase 10.18A - Volumetric Balance Components")
    ax.set_xlabel("time_s")
    ax.set_ylabel("component value")
    ax.text(0.02, 0.02, "DIAGNOSTIC ONLY - component definitions are model-specific.", transform=ax.transAxes, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True, available, missing


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_csv = Path(args.legacy_csv)
    volumetric_csv = Path(args.modern_volumetric_csv)
    direct_csv = Path(args.modern_direct_csv) if args.modern_direct_csv else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    legacy_rows = _read_csv(legacy_csv)
    volumetric_rows = _read_csv(volumetric_csv)
    direct_rows = _read_csv(direct_csv) if direct_csv else []

    legacy_range = _pressure_range(legacy_rows, "pw_Pa")
    volumetric_range = _pressure_range(volumetric_rows, "wellbore_pressure_Pa")
    direct_range = _pressure_range(direct_rows, "net_pressure_Pa") if direct_rows else None
    classification = _classify(legacy_range, direct_range, volumetric_range)

    legacy_times = _finite_values(legacy_rows, "time_s")
    volumetric_times = _finite_values(volumetric_rows, "time_s")
    direct_times = _finite_values(direct_rows, "time_s") if direct_rows else []
    legacy_volumes = _finite_values(legacy_rows, "injected_volume_m3")
    volumetric_volumes = _finite_values(volumetric_rows, "injected_volume_m3")
    direct_volumes = _finite_values(direct_rows, "injected_volume_m3") if direct_rows else []

    legacy_points = _aggregate_legacy_by_time(legacy_rows)
    volumetric_points = _modern_points(volumetric_rows, "wellbore_pressure_Pa", "modern_volumetric_balance")
    direct_points = _modern_points(direct_rows, "net_pressure_Pa", "modern_pkn_direct") if direct_rows else None

    volume_plot = _plot_volume_vs_pressure(
        output_dir / "injected_volume_vs_pressure_volumetric.png",
        legacy_points,
        volumetric_points,
        direct_points,
    )
    time_plot = _plot_pressure_vs_time(
        output_dir / "pressure_vs_time_volumetric.png",
        legacy_points,
        volumetric_points,
        direct_points,
    )
    balance_plot, balance_available, balance_missing = _plot_balance_components(
        output_dir / "volume_balance_components.png", volumetric_rows
    )

    legacy_max_diff_volumetric = _max_pressure_difference(legacy_range, volumetric_range)
    legacy_max_diff_direct = _max_pressure_difference(legacy_range, direct_range)

    metadata: dict[str, Any] = {
        "phase": PHASE,
        "status": "PHASE10_18A_VOLUMETRIC_BALANCE_DIAGNOSTIC_COMPLETE",
        "classification": classification,
        "physical_validation": False,
        "numeric_equivalence": False,
        "pressure_semantic_equivalence": False,
        "legacy_csv": str(legacy_csv),
        "modern_volumetric_csv": str(volumetric_csv),
        "modern_direct_csv": str(direct_csv) if direct_csv else None,
        "legacy": {
            "pressure_field": "pw_Pa",
            "n_records": len(legacy_rows),
            "pressure_range": legacy_range,
            "pressure_range_Pa": _span(_finite_values(legacy_rows, "pw_Pa")),
            "max_pressure_Pa": legacy_range["max"] if legacy_range else None,
            "time_range": _range(legacy_times),
            "time_range_s": _span(legacy_times),
            "volume_range": _range(legacy_volumes),
            "volume_range_m3": _span(legacy_volumes),
        },
        "volumetric_balance": {
            "pressure_field": "wellbore_pressure_Pa",
            "n_records": len(volumetric_rows),
            "pressure_range": volumetric_range,
            "pressure_range_Pa": _span(_finite_values(volumetric_rows, "wellbore_pressure_Pa")),
            "max_pressure_Pa": volumetric_range["max"] if volumetric_range else None,
            "time_range": _range(volumetric_times),
            "time_range_s": _span(volumetric_times),
            "volume_range": _range(volumetric_volumes),
            "volume_range_m3": _span(volumetric_volumes),
        },
        "differences": {
            "legacy_vs_volumetric_max_pressure": legacy_max_diff_volumetric,
            "legacy_vs_pkn_direct_max_pressure": legacy_max_diff_direct,
        },
        "plots": {
            "injected_volume_vs_pressure_volumetric": volume_plot,
            "pressure_vs_time_volumetric": time_plot,
            "volume_balance_components": balance_plot,
        },
        "balance_components": {
            "available": balance_available,
            "missing": balance_missing,
        },
        "caveats": [
            "DIAGNOSTIC ONLY - not physical validation.",
            "Legacy pw_Pa and modern pressure definitions may differ.",
            "volumetric_balance is opt-in and does not change pkn_direct default behavior.",
            "No shut-in, accommodation, Zamora, sigmaTheta, margin or opened comparison is performed.",
        ],
    }
    if direct_rows:
        metadata["pkn_direct"] = {
            "pressure_field": "net_pressure_Pa",
            "n_records": len(direct_rows),
            "pressure_range": direct_range,
            "pressure_range_Pa": _span(_finite_values(direct_rows, "net_pressure_Pa")),
            "max_pressure_Pa": direct_range["max"] if direct_range else None,
            "time_range": _range(direct_times),
            "time_range_s": _span(direct_times),
            "volume_range": _range(direct_volumes),
            "volume_range_m3": _span(direct_volumes),
        }

    with (output_dir / "phase10_18a_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    _write_summary(output_dir / "phase10_18a_summary.csv", metadata)
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 10.18A volumetric_balance diagnostic plots and metrics.")
    parser.add_argument("--legacy-csv", required=True, help="Legacy audit CSV with pw_Pa and injected_volume_m3.")
    parser.add_argument("--modern-volumetric-csv", required=True, help="Modern volumetric_balance timeseries.csv.")
    parser.add_argument("--modern-direct-csv", help="Optional modern pkn_direct timeseries.csv.")
    parser.add_argument("--output-dir", required=True, help="Directory for diagnostic summary, metadata and plots.")
    return parser.parse_args()


def main() -> None:
    metadata = run_comparison(parse_args())
    if metadata["classification"] not in CLASSIFICATION_CHOICES:
        raise RuntimeError(f"Unexpected classification: {metadata['classification']}")
    print(json.dumps({"phase": metadata["phase"], "classification": metadata["classification"]}, indent=2))


if __name__ == "__main__":
    main()
