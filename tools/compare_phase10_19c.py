from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.19C"
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


def _first_positive_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    candidates = [row for row in rows if (_float(row.get("time_s")) or 0.0) > 0.0]
    if not candidates:
        return None
    return min(candidates, key=lambda row: _float(row.get("time_s")) or math.inf)


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = _values(rows, field)
    return max(values) if values else None


def _relative_error(reference: float | None, value: float | None) -> float | None:
    if reference is None or value is None or reference == 0.0:
        return None
    return (value - reference) / abs(reference)


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


def _classify(metrics: dict[str, Any]) -> str:
    legacy_first = metrics.get("legacy_first_dP_Pa")
    modern_first = metrics.get("modern_first_dP_with_compliance_Pa")
    max_rel = metrics.get("relative_error_max_pressure")
    if legacy_first is None or modern_first is None:
        return "INCONCLUSIVE"
    first_rel = _relative_error(legacy_first, modern_first)
    if first_rel is None or not math.isfinite(first_rel):
        return "COMPLIANCE_ERROR"
    first_matches = abs(first_rel) <= 0.05
    max_matches = max_rel is not None and math.isfinite(max_rel) and abs(max_rel) <= 0.10
    if first_matches and max_matches:
        return "COMPLIANCE_EFFECTIVE"
    if first_matches and not max_matches:
        return "COMPLIANCE_MATCHES_FIRST_STEP_BUT_NOT_CURVE"
    if abs(first_rel) < 0.5:
        return "COMPLIANCE_PARTIAL"
    return "COMPLIANCE_NO_IMPROVEMENT"


def _points(rows: list[dict[str, str]], pressure_field: str) -> list[dict[str, float]]:
    points = []
    for row in rows:
        time_s = _float(row.get("time_s"))
        pressure = _float(row.get(pressure_field))
        volume = _float(row.get("injected_volume_m3"))
        if time_s is None or pressure is None:
            continue
        points.append({"time_s": time_s, "pressure_Pa": pressure, "volume_m3": volume or 0.0})
    return points


def _plot_outputs(
    output_dir: Path,
    legacy_rows: list[dict[str, str]],
    modern_rows: list[dict[str, str]],
    no_compliance_rows: list[dict[str, str]] | None,
    metrics: dict[str, Any],
) -> dict[str, bool]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {
            "pressure_vs_time_compliance.png": False,
            "injected_volume_vs_pressure_compliance.png": False,
            "first_steps_pressure_increment.png": False,
            "compliance_diagnostics.png": False,
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, bool] = {}
    legacy = _points(legacy_rows, "pw_Pa")
    modern = _points(modern_rows, "wellbore_pressure_Pa")
    previous = _points(no_compliance_rows or [], "wellbore_pressure_Pa")

    def save(name: str) -> None:
        plt.figtext(0.5, 0.01, "Phase 10.19C - DIAGNOSTIC ONLY - constant compliance approximation",
                    ha="center", fontsize=8)
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        plt.savefig(output_dir / name, dpi=150)
        plt.close()
        generated[name] = True

    plt.figure()
    if legacy:
        plt.plot([p["time_s"] for p in legacy], [p["pressure_Pa"] for p in legacy],
                 label="Legacy audited")
    if previous:
        plt.plot([p["time_s"] for p in previous], [p["pressure_Pa"] for p in previous],
                 label="Modern no compliance")
    if modern:
        plt.plot([p["time_s"] for p in modern], [p["pressure_Pa"] for p in modern],
                 label="Modern with compliance")
    plt.xlabel("time_s")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.19C pressure vs time")
    plt.legend()
    save("pressure_vs_time_compliance.png")

    plt.figure()
    if legacy:
        plt.plot([p["volume_m3"] for p in legacy], [p["pressure_Pa"] for p in legacy],
                 label="Legacy audited")
    if modern:
        plt.plot([p["volume_m3"] for p in modern], [p["pressure_Pa"] for p in modern],
                 label="Modern with compliance")
    plt.xlabel("injected_volume_m3")
    plt.ylabel("pressure_Pa")
    plt.title("Phase 10.19C injected volume vs pressure")
    plt.legend()
    save("injected_volume_vs_pressure_compliance.png")

    plt.figure()
    labels = ["legacy", "no_compliance", "with_compliance"]
    values = [
        metrics.get("legacy_first_dP_Pa") or 0.0,
        metrics.get("modern_first_dP_no_compliance_Pa") or 0.0,
        metrics.get("modern_first_dP_with_compliance_Pa") or 0.0,
    ]
    plt.bar(labels, values)
    plt.ylabel("first_step_dP_Pa")
    plt.title("Phase 10.19C first-step pressure increment")
    save("first_steps_pressure_increment.png")

    plt.figure()
    labels = [
        "fluid_C",
        "geom_C",
        "eff_C",
        "first_dP",
    ]
    values = [
        metrics.get("fluid_compressibility_1_Pa") or 0.0,
        metrics.get("geometric_compressibility_1_Pa") or 0.0,
        metrics.get("effective_compressibility_1_Pa") or 0.0,
        metrics.get("modern_first_dP_with_compliance_Pa") or 0.0,
    ]
    plt.bar(labels, values)
    plt.yscale("symlog", linthresh=1.0e-8)
    plt.title("Phase 10.19C compliance diagnostics")
    save("compliance_diagnostics.png")

    return generated


def run_comparison(args: argparse.Namespace) -> dict[str, Any]:
    legacy_rows = _read_csv(Path(args.legacy_csv))
    modern_rows = _read_csv(Path(args.modern_csv))
    no_compliance_rows = (
        _read_csv(Path(args.modern_10_19a_csv))
        if args.modern_10_19a_csv is not None
        else None
    )

    legacy_first = _first_positive_row(legacy_rows)
    modern_first = _first_positive_row(modern_rows)
    previous_first = _first_positive_row(no_compliance_rows or [])
    initiation = _first_initiation(modern_rows)
    max_legacy = _max(legacy_rows, "pw_Pa")
    max_modern = _max(modern_rows, "wellbore_pressure_Pa")
    no_compliance_first_dP = None
    if previous_first is not None:
        trial = _float(previous_first.get("fracture_initiation_pressure_Pa"))
        initial = _float(previous_first.get("initial_pressure_Pa"))
        if trial is not None and trial > 0.0 and initial is not None:
            no_compliance_first_dP = trial - initial
        else:
            no_compliance_first_dP = _float(
                previous_first.get("balance_delta_pressure_Pa")
            )

    metrics: dict[str, Any] = {
        "legacy_first_dP_Pa": None if legacy_first is None else _float(legacy_first.get("dP")),
        "modern_first_dP_no_compliance_Pa": no_compliance_first_dP,
        "modern_first_dP_with_compliance_Pa": None
        if modern_first is None
        else _float(modern_first.get("balance_delta_pressure_Pa")),
        "max_pressure_legacy_Pa": max_legacy,
        "max_pressure_with_compliance_Pa": max_modern,
        "relative_error_max_pressure": _relative_error(max_legacy, max_modern),
        "fracture_initiation_time_s": initiation["time_s"],
        "fracture_initiation_pressure_Pa": initiation["pressure_Pa"],
        "effective_compressibility_1_Pa": None
        if modern_first is None
        else _float(modern_first.get("effective_compressibility_1_Pa")),
        "geometric_compressibility_1_Pa": None
        if modern_first is None
        else _float(modern_first.get("geometric_compressibility_1_Pa")),
        "fluid_compressibility_1_Pa": None
        if modern_first is None
        else _float(modern_first.get("fluid_compressibility_1_Pa")),
    }
    classification = _classify(metrics)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plots = _plot_outputs(output_dir, legacy_rows, modern_rows, no_compliance_rows, metrics)

    metadata = {
        "phase": PHASE,
        "classification": classification,
        "physical_validation": False,
        "numeric_equivalence": False,
        "metrics": metrics,
        "plots": plots,
        "caveats": [
            "Diagnostic only; not physical validation.",
            "Constant compliance is inferred from first-step legacy dP.",
            "This is not a validated casing/formation mechanics model.",
            "No Zamora, sigma-theta runtime or full APB/salt coupling is implemented.",
        ],
    }

    with (output_dir / "phase10_19c_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["phase", "classification", *metrics.keys()],
        )
        writer.writeheader()
        writer.writerow({"phase": PHASE, "classification": classification, **metrics})
    (output_dir / "phase10_19c_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Phase 10.19C opt-in geometric compliance diagnostic."
    )
    parser.add_argument("--legacy-csv", required=True, type=Path)
    parser.add_argument("--modern-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--modern-10-18b-csv", type=Path, default=None)
    parser.add_argument("--modern-10-19a-csv", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    metadata = run_comparison(build_parser().parse_args(argv))
    print(json.dumps({
        "classification": metadata["classification"],
        "metrics": metadata["metrics"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
