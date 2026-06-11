from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import yaml


PHASE = "10.25A"
REQUIRED_COLUMNS = {
    "step",
    "time_min",
    "time_s",
    "dt_min",
    "dt_s",
    "idAnnular",
    "idLayer",
    "depth_influence_m",
    "thickness_m",
    "pi_Pa",
    "dP_Pa",
    "pw_Pa",
    "sigmaTheta_raw_Pa",
    "sigmaTheta_compression_positive_Pa",
    "margin_Pa",
    "opened",
    "opened_before_step",
    "opened_after_step",
    "fracture_started_this_step",
    "sink_positive",
    "sink_started_this_step",
    "dV_leakoff_m3_rad",
    "dV_leakoff_increment_m3_rad",
    "Qinj_m3_rad_min",
}
BOOL_COLUMNS = {
    "opened",
    "opened_before_step",
    "opened_after_step",
    "fracture_started_this_step",
    "sink_positive",
    "sink_started_this_step",
}


def _float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _bool(value: object) -> bool | None:
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def read_trace(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError(f"trace missing required columns: {missing}")
        rows: list[dict[str, Any]] = []
        for raw in reader:
            row: dict[str, Any] = dict(raw)
            for key in row:
                if key in BOOL_COLUMNS:
                    row[key] = _bool(row[key])
                elif key != "":
                    parsed = _float(row[key])
                    if parsed is not None:
                        row[key] = parsed
            rows.append(row)
    if not rows:
        raise ValueError("trace has no rows")
    return rows


def read_yaml_sigma_theta_series(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    values = (
        loaded.get("lot", {})
        .get("fracture", {})
        .get("initiation", {})
        .get("sigma_theta_series", {})
        .get("values", [])
    )
    points: list[dict[str, Any]] = []
    for item in values:
        time = item.get("time", {})
        sigma = item.get("sigma_theta_compression_positive", {})
        depth = item.get("influence_depth", {})
        time_s = _unit_value(time, expected_unit="s")
        sigma_pa = _unit_value(sigma, expected_unit="Pa")
        points.append(
            {
                "time_s": time_s,
                "sigmaTheta_compression_positive_Pa": sigma_pa,
                "layer_id": item.get("layer_id", ""),
                "influence_depth_m": _unit_value(depth, expected_unit="m"),
            }
        )
    if not points:
        raise ValueError("YAML sigma_theta_series has no points")
    return sorted(points, key=lambda row: row["time_s"])


def _unit_value(node: dict[str, Any], *, expected_unit: str) -> float:
    if node.get("unit") != expected_unit:
        raise ValueError(f"expected unit {expected_unit}, got {node.get('unit')}")
    value = _float(node.get("value"))
    if value is None:
        raise ValueError(f"invalid value for unit {expected_unit}")
    return value


def _first_row(rows: list[dict[str, Any]], predicate: Any) -> dict[str, Any] | None:
    for row in sorted(rows, key=lambda r: (r.get("time_s") or 0.0, r.get("step") or 0.0)):
        if predicate(row):
            return row
    return None


def _primary_key(rows: list[dict[str, Any]]) -> tuple[int, int]:
    opened = _first_row(rows, lambda row: row.get("opened") is True)
    if opened is None:
        candidate = min(rows, key=lambda row: abs(row.get("margin_Pa") or 0.0))
        return int(candidate["idAnnular"]), int(candidate["idLayer"])
    return int(opened["idAnnular"]), int(opened["idLayer"])


def _dedupe_primary_series(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annular, layer = _primary_key(rows)
    chosen: dict[float, dict[str, Any]] = {}
    for row in rows:
        if int(row["idAnnular"]) != annular or int(row["idLayer"]) != layer:
            continue
        time_s = float(row["time_s"])
        if time_s not in chosen or float(row["step"]) > float(chosen[time_s]["step"]):
            chosen[time_s] = row
    return [chosen[key] for key in sorted(chosen)]


def _interp(points: list[tuple[float, float]], time_s: float) -> float | None:
    if not points:
        return None
    points = sorted(points)
    if time_s <= points[0][0]:
        return points[0][1]
    if time_s >= points[-1][0]:
        return points[-1][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t0 <= time_s <= t1:
            if t1 == t0:
                return v1
            frac = (time_s - t0) / (t1 - t0)
            return v0 + frac * (v1 - v0)
    return None


def _diff_stats(
    refined_points: list[dict[str, Any]], yaml_points: list[dict[str, Any]]
) -> dict[str, Any]:
    refined = [
        (float(row["time_s"]), float(row["sigmaTheta_compression_positive_Pa"]))
        for row in refined_points
    ]
    yaml_series = [
        (float(row["time_s"]), float(row["sigmaTheta_compression_positive_Pa"]))
        for row in yaml_points
    ]
    diffs: list[float] = []
    for time_s, refined_sigma in refined:
        yaml_sigma = _interp(yaml_series, time_s)
        if yaml_sigma is not None:
            diffs.append(abs(yaml_sigma - refined_sigma))
    return {
        "max_abs_difference_between_yaml_and_refined": max(diffs) if diffs else None,
        "mean_abs_difference_between_yaml_and_refined": mean(diffs) if diffs else None,
    }


def analyze(rows: list[dict[str, Any]], yaml_points: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    series = _dedupe_primary_series(rows)
    first_open = _first_row(rows, lambda row: row.get("opened") is True)
    first_sink = _first_row(rows, lambda row: row.get("sink_positive") is True)
    refined_series = [
        (
            float(row["time_s"]),
            float(row["sigmaTheta_compression_positive_Pa"]),
        )
        for row in series
    ]
    yaml_series = [
        (
            float(row["time_s"]),
            float(row["sigmaTheta_compression_positive_Pa"]),
        )
        for row in yaml_points
    ]
    diff_stats = _diff_stats(series, yaml_points)
    complete = (
        first_open is not None
        and first_sink is not None
        and len(series) >= 2
        and min(row["time_s"] for row in series) <= 510.0
        and max(row["time_s"] for row in series) >= 660.0
    )
    yaml_too_sparse = len(yaml_points) <= 3 and len(series) > len(yaml_points)
    max_diff = diff_stats["max_abs_difference_between_yaml_and_refined"]
    yaml_differs = max_diff is not None and max_diff > 1.0e5
    classifications = [
        "SIGMA_THETA_REFINED_SERIES_COMPLETE"
        if complete
        else "SIGMA_THETA_REFINED_SERIES_PARTIAL",
        "SIGMA_THETA_YAML_SERIES_TOO_SPARSE"
        if yaml_too_sparse
        else (
            "SIGMA_THETA_YAML_SERIES_DIFFERS_FROM_REFINED"
            if yaml_differs
            else "SIGMA_THETA_YAML_SERIES_MATCHES_REFINED"
        ),
        "SIGMA_THETA_SOURCE_MISMATCH_EXPLAINS_OPENING_SHIFT"
        if yaml_too_sparse and yaml_differs
        else "SIGMA_THETA_SOURCE_MISMATCH_INCONCLUSIVE",
    ]
    gate = (
        "SIGMA_THETA_REFINED_PROVIDER_UPDATE_ALLOWED"
        if complete
        else "SIGMA_THETA_REFINED_PROVIDER_BLOCKED_INSUFFICIENT_SERIES"
    )
    first_open_s = first_open.get("time_s") if first_open else None
    first_sink_s = first_sink.get("time_s") if first_sink else None
    summary = {
        "phase": PHASE,
        "classifications": classifications,
        "gate": gate,
        "primary_idAnnular": _primary_key(rows)[0],
        "primary_idLayer": _primary_key(rows)[1],
        "legacy_first_opened_time_s": first_open_s,
        "legacy_first_opened_step": first_open.get("step") if first_open else None,
        "legacy_first_pw_Pa": first_open.get("pw_Pa") if first_open else None,
        "legacy_first_sigmaTheta_Pa": first_open.get("sigmaTheta_compression_positive_Pa") if first_open else None,
        "legacy_first_margin_Pa": first_open.get("margin_Pa") if first_open else None,
        "legacy_first_sink_positive_time_s": first_sink_s,
        "sink_delay_s": None if first_open_s is None or first_sink_s is None else first_sink_s - first_open_s,
        "number_of_sigmaTheta_points": len(series),
        "time_range": [min(row["time_s"] for row in series), max(row["time_s"] for row in series)],
        "sigmaTheta_min": min(row["sigmaTheta_compression_positive_Pa"] for row in series),
        "sigmaTheta_max": max(row["sigmaTheta_compression_positive_Pa"] for row in series),
        "sigmaTheta_at_510s": _interp(refined_series, 510.0),
        "sigmaTheta_at_660s": _interp(refined_series, 660.0),
        "n_points_yaml": len(yaml_points),
        "time_range_yaml": [min(row["time_s"] for row in yaml_points), max(row["time_s"] for row in yaml_points)],
        "sigmaTheta_at_510s_yaml": _interp(yaml_series, 510.0),
        "sigmaTheta_at_660s_yaml": _interp(yaml_series, 660.0),
        **diff_stats,
        "audit_map": [
            {
                "conceito": "sigmaTheta",
                "arquivo": "legance/LOT_Tese/src/apb_code/APB1da.cpp",
                "funcao": "APB1da::calculateLOTFracturedSaltRock",
                "variavel": "sigmaTheta = -line_up[lu].mdl->getSigmaTheta()",
                "momento": "apos atualizar o modelo de sal e antes de if (pw > sigmaTheta)",
            },
            {
                "conceito": "pw",
                "arquivo": "legance/LOT_Tese/src/apb_code/APB1da.cpp",
                "funcao": "APB1da::calculateLOTFracturedSaltRock",
                "variavel": "pw = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)",
                "momento": "antes da recuperacao de sigmaTheta",
            },
            {
                "conceito": "opened",
                "arquivo": "legance/LOT_Tese/src/apb_code/APB1da.cpp",
                "funcao": "APB1da::calculateLOTFracturedSaltRock",
                "variavel": "if (pw > sigmaTheta)",
                "momento": "criterio legado estrito; igualdade nao abre",
            },
        ],
        "caveats": [
            "temporary LOT_Tese instrumentation only; no legance edits are committed",
            "refined series samples the legacy criterion path, not SaltWallStressDiagnostics runtime",
            "multiple nonlinear visits can occur at the same time_s; exported provider series keeps the last sample per time for the first opening layer",
            "diagnostic only; not physical validation",
        ],
    }
    return series, summary


def write_series(series: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "time_s",
        "sigmaTheta_compression_positive_Pa",
        "sigmaTheta_raw_Pa",
        "idAnnular",
        "idLayer",
        "depth_influence_m",
        "thickness_m",
        "pw_Pa",
        "margin_Pa",
        "opened",
        "sink_positive",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in series:
            writer.writerow({field: row.get(field) for field in fieldnames})


def write_plots(series: list[dict[str, Any]], yaml_points: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    names = [
        "sigma_theta_refined_vs_time.png",
        "pw_sigmaTheta_margin_refined.png",
        "yaml_vs_refined_sigma_theta.png",
        "opening_crossing_refined.png",
        "sink_timing_refined.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        for name in names:
            (output_dir / name).write_text("matplotlib unavailable\n", encoding="utf-8")
        return

    times = [row["time_s"] for row in series]
    sigma = [row["sigmaTheta_compression_positive_Pa"] for row in series]
    pw = [row["pw_Pa"] for row in series]
    margin = [row["margin_Pa"] for row in series]
    opened = [1 if row["opened"] else 0 for row in series]
    sink = [1 if row["sink_positive"] else 0 for row in series]

    plt.figure()
    plt.plot(times, sigma, label="refined sigmaTheta")
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "sigma_theta_refined_vs_time.png")
    plt.close()

    plt.figure()
    plt.plot(times, pw, label="pw")
    plt.plot(times, sigma, label="sigmaTheta")
    plt.plot(times, margin, label="margin")
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "pw_sigmaTheta_margin_refined.png")
    plt.close()

    plt.figure()
    plt.plot(times, sigma, label="refined")
    plt.plot(
        [row["time_s"] for row in yaml_points],
        [row["sigmaTheta_compression_positive_Pa"] for row in yaml_points],
        marker="o",
        label="yaml 10.24B",
    )
    plt.xlabel("time_s")
    plt.ylabel("Pa")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "yaml_vs_refined_sigma_theta.png")
    plt.close()

    plt.figure()
    plt.plot(times, margin, label="margin")
    plt.axhline(0.0, color="black", linewidth=0.8)
    plt.step(times, opened, where="post", label="opened")
    plt.xlabel("time_s")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "opening_crossing_refined.png")
    plt.close()

    plt.figure()
    plt.step(times, opened, where="post", label="opened")
    plt.step(times, sink, where="post", label="sink_positive")
    plt.xlabel("time_s")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "sink_timing_refined.png")
    plt.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Phase 10.25A refined LOT_Tese sigmaTheta trace."
    )
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--existing-yaml", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = read_trace(args.trace)
    yaml_points = read_yaml_sigma_theta_series(args.existing_yaml)
    series, summary = analyze(rows, yaml_points)
    write_series(series, args.output_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = args.output_dir / "legacy_sigma_theta_refined_trace_metadata.json"
    metadata_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_plots(series, yaml_points, args.output_dir)
    print(json.dumps({"phase": PHASE, "gate": summary["gate"], "classifications": summary["classifications"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
