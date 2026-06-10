from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.20C"
CLASSIFICATIONS = {
    "ELASTIC_COMPLIANCE_EFFECTIVE",
    "ELASTIC_COMPLIANCE_PARTIAL",
    "ELASTIC_COMPLIANCE_UNDERCOMPLIANT",
    "ELASTIC_COMPLIANCE_OVERCOMPLIANT",
    "ELASTIC_COMPLIANCE_REQUIRES_CALIBRATION",
    "ELASTIC_COMPLIANCE_INCONCLUSIVE",
}


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


def _first_positive_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    candidates = [row for row in rows if (_float(row.get("time_s")) or 0.0) > 0.0]
    if not candidates:
        return None
    return min(candidates, key=lambda row: _float(row.get("time_s")) or math.inf)


def _first_initiation(rows: list[dict[str, str]]) -> dict[str, float | None]:
    for row in rows:
        initiated = row.get("fracture_initiated", "").strip().lower()
        if initiated not in {"1", "true", "yes"}:
            continue
        pressure = _float(row.get("fracture_initiation_pressure_Pa"))
        if pressure is not None and pressure > 0.0:
            return {
                "time_s": _float(row.get("time_s")),
                "pressure_Pa": pressure,
                "sigma_theta_Pa": _float(row.get("fracture_initiation_sigma_theta_Pa")),
                "margin_Pa": _float(row.get("fracture_initiation_margin_Pa")),
            }
    return {"time_s": None, "pressure_Pa": None, "sigma_theta_Pa": None, "margin_Pa": None}


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _max_pressure_route(rows: list[dict[str, str]]) -> float | None:
    values = _values(rows, "wellbore_pressure_Pa")
    initiation_values = _values(rows, "fracture_initiation_pressure_Pa")
    values.extend(value for value in initiation_values if value > 0.0)
    return max(values) if values else None


def _first_pressure_increment(rows: list[dict[str, str]]) -> float | None:
    first = _first_positive_row(rows)
    if first is None:
        return None
    trial = _float(first.get("fracture_initiation_pressure_Pa"))
    initial = _float(first.get("initial_pressure_Pa"))
    if trial is not None and trial > 0.0 and initial is not None:
        return trial - initial
    return _float(first.get("balance_delta_pressure_Pa"))


def _classify(metrics: dict[str, Any]) -> str:
    legacy_first = metrics.get("legacy_first_dP_Pa")
    elastic_first = metrics.get("modern_first_dP_elastic_compliance_Pa")
    max_rel = metrics.get("relative_error_max_pressure")
    if legacy_first is None or elastic_first is None:
        return "ELASTIC_COMPLIANCE_INCONCLUSIVE"

    first_rel = _relative_error(legacy_first, elastic_first)
    if first_rel is None or not math.isfinite(first_rel):
        return "ELASTIC_COMPLIANCE_INCONCLUSIVE"

    first_close = abs(first_rel) <= 0.05
    max_close = max_rel is not None and math.isfinite(max_rel) and abs(max_rel) <= 0.10
    if first_close and max_close:
        return "ELASTIC_COMPLIANCE_EFFECTIVE"
    if elastic_first > legacy_first and abs(first_rel) > 0.50:
        return "ELASTIC_COMPLIANCE_UNDERCOMPLIANT"
    if elastic_first < legacy_first and abs(first_rel) > 0.50:
        return "ELASTIC_COMPLIANCE_OVERCOMPLIANT"
    if not first_close and max_close:
        return "ELASTIC_COMPLIANCE_REQUIRES_CALIBRATION"
    return "ELASTIC_COMPLIANCE_PARTIAL"


def _points(rows: list[dict[str, str]], pressure_field: str) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    for row in rows:
        time_s = _float(row.get("time_s"))
        pressure = _float(row.get(pressure_field))
        volume = _float(row.get("injected_volume_m3"))
        if time_s is None or pressure is None:
            continue
        points.append(
            {
                "time_s": time_s,
                "pressure_Pa": pressure,
                "volume_m3": 0.0 if volume is None else volume,
            }
        )
    return points


def _plot_outputs(
    output_dir: Path,
    legacy_rows: list[dict[str, str]],
    elastic_rows: list[dict[str, str]],
    no_compliance_rows: list[dict[str, str]] | None,
    constant_rows: list[dict[str, str]] | None,
    sigma_theta_rows: list[dict[str, str]] | None,
    metrics: dict[str, Any],
) -> dict[str, bool]:
    names = [
        "pressure_vs_time_elastic_compliance.png",
        "injected_volume_vs_pressure_elastic_compliance.png",
        "first_steps_pressure_increment_elastic.png",
        "compliance_model_comparison.png",
        "fracture_initiation_comparison.png",
    ]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {name: False for name in names}

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, bool] = {}
    series = [
        ("legacy", _points(legacy_rows, "pw_Pa")),
        ("no_compliance", _points(no_compliance_rows or [], "wellbore_pressure_Pa")),
        ("constant_geometric", _points(constant_rows or [], "wellbore_pressure_Pa")),
        ("elastic_annular_simple", _points(elastic_rows, "wellbore_pressure_Pa")),
        ("sigma_theta_static", _points(sigma_theta_rows or [], "wellbore_pressure_Pa")),
    ]

    def save(name: str) -> None:
        plt.figtext(
            0.5,
            0.01,
            "Phase 10.20C - DIAGNOSTIC ONLY - not physical validation",
            ha="center",
            fontsize=8,
        )
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()
        generated[name] = True

    plt.figure()
    for label, points in series:
      if points:
        plt.plot(
            [point["time_s"] for point in points],
            [point["pressure_Pa"] for point in points],
            label=label,
        )
    plt.xlabel("time_s")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.20C pressure vs time")
    plt.legend()
    save("pressure_vs_time_elastic_compliance.png")

    plt.figure()
    for label, points in series:
      if points:
        plt.plot(
            [point["volume_m3"] for point in points],
            [point["pressure_Pa"] for point in points],
            label=label,
        )
    plt.xlabel("injected_volume_m3")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.20C injected volume vs pressure")
    plt.legend()
    save("injected_volume_vs_pressure_elastic_compliance.png")

    plt.figure()
    labels = [
        "legacy",
        "no_compliance",
        "constant",
        "elastic",
    ]
    values = [
        metrics.get("legacy_first_dP_Pa") or 0.0,
        metrics.get("modern_first_dP_no_compliance_Pa") or 0.0,
        metrics.get("modern_first_dP_constant_compliance_Pa") or 0.0,
        metrics.get("modern_first_dP_elastic_compliance_Pa") or 0.0,
    ]
    plt.bar(labels, values)
    plt.ylabel("first_step_dP_Pa")
    plt.title("Phase 10.20C first-step pressure increment")
    save("first_steps_pressure_increment_elastic.png")

    plt.figure()
    labels = ["C_geom_constant_10_19C", "C_geom_elastic_10_20C", "C_eff_elastic_10_20C"]
    values = [
        metrics.get("C_geom_constant_10_19C") or 0.0,
        metrics.get("C_geom_elastic_10_20C") or 0.0,
        metrics.get("C_eff_elastic_10_20C") or 0.0,
    ]
    plt.bar(labels, values)
    plt.yscale("log")
    plt.ylabel("1/Pa")
    plt.title("Phase 10.20C compliance model comparison")
    save("compliance_model_comparison.png")

    plt.figure()
    labels = ["legacy", "elastic"]
    values = [
        metrics.get("fracture_initiation_time_legacy_s") or 0.0,
        metrics.get("fracture_initiation_time_elastic_s") or 0.0,
    ]
    plt.bar(labels, values)
    plt.ylabel("time_s")
    plt.title("Phase 10.20C fracture initiation time")
    save("fracture_initiation_comparison.png")

    return generated


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    elastic_rows = _read_csv(Path(args.modern_elastic_csv))
    no_rows = _read_csv(Path(args.modern_no_compliance_csv)) if args.modern_no_compliance_csv else None
    constant_rows = _read_csv(Path(args.modern_constant_compliance_csv)) if args.modern_constant_compliance_csv else None
    sigma_rows = _read_csv(Path(args.modern_sigma_theta_static_csv)) if args.modern_sigma_theta_static_csv else None

    legacy_first = _first_positive_row(legacy_rows)
    elastic_first = _first_positive_row(elastic_rows)
    constant_first = _first_positive_row(constant_rows or [])
    no_first = _first_positive_row(no_rows or [])
    initiation = _first_initiation(elastic_rows)
    max_legacy = _max(legacy_rows, "pw_Pa")
    max_elastic = _max_pressure_route(elastic_rows)

    metrics: dict[str, Any] = {
        "legacy_first_dP_Pa": None if legacy_first is None else _float(legacy_first.get("dP")),
        "modern_first_dP_no_compliance_Pa": _first_pressure_increment(no_rows or []),
        "modern_first_dP_constant_compliance_Pa": _first_pressure_increment(constant_rows or []),
        "modern_first_dP_elastic_compliance_Pa": _first_pressure_increment(elastic_rows),
        "max_pressure_legacy_Pa": max_legacy,
        "max_pressure_elastic_compliance_Pa": max_elastic,
        "relative_error_max_pressure": _relative_error(max_legacy, max_elastic),
        "fracture_initiation_time_legacy_s": 510.0,
        "fracture_initiation_time_elastic_s": initiation["time_s"],
        "fracture_initiation_pressure_elastic_Pa": initiation["pressure_Pa"],
        "C_geom_constant_10_19C": None if constant_first is None else _float(constant_first.get("geometric_compressibility_1_Pa")),
        "C_geom_elastic_10_20C": None if elastic_first is None else _float(elastic_first.get("geometric_compressibility_1_Pa")),
        "C_eff_elastic_10_20C": None if elastic_first is None else _float(elastic_first.get("effective_compressibility_1_Pa")),
    }
    classification = _classify(metrics)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plots = _plot_outputs(
        output_dir,
        legacy_rows,
        elastic_rows,
        no_rows,
        constant_rows,
        sigma_rows,
        metrics,
    )
    metadata = {
        "phase": PHASE,
        "status": "PHASE10_20C_BUZ67D_ELASTIC_COMPLIANCE_DIAGNOSTIC_COMPLETE",
        "classification": classification,
        "physical_validation": False,
        "numeric_equivalence": False,
        "runtime_default_changed": False,
        "model": "elastic_annular_simple",
        "metrics": metrics,
        "plots": plots,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "elastic_annular_simple is a reduced opt-in mechanical estimate.",
            "constant_geometric remains the diagnostic baseline inferred from legacy first-step dP.",
            "No Zamora, sigma-theta runtime or full APB/salt coupling is implemented.",
        ],
    }
    with (output_dir / "phase10_20c_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["phase", "classification", *metrics.keys()],
        )
        writer.writeheader()
        writer.writerow({"phase": PHASE, "classification": classification, **metrics})
    (output_dir / "phase10_20c_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.20C BUZ67D elastic annular compliance diagnostic."
    )
    parser.add_argument("--legacy-csv", required=True, type=Path)
    parser.add_argument("--modern-elastic-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--modern-no-compliance-csv", type=Path, default=None)
    parser.add_argument("--modern-constant-compliance-csv", type=Path, default=None)
    parser.add_argument("--modern-sigma-theta-static-csv", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    metadata = run_comparison(build_parser().parse_args(argv))
    if metadata["classification"] not in CLASSIFICATIONS:
        raise RuntimeError(f"Unexpected classification: {metadata['classification']}")
    print(
        json.dumps(
            {
                "phase": metadata["phase"],
                "classification": metadata["classification"],
                "metrics": metadata["metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
