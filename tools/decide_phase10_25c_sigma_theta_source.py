from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.25C"
MISSING_SUMMARIES = "PHASE10_25C_BLOCKED_MISSING_SUMMARIES"


def _read_first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no summary rows")
    return rows[0]


def _float(value: str | float | int | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _metrics_from_row(row: dict[str, str]) -> dict[str, Any]:
    keys = [
        "classification",
        "relative_error_max_pressure",
        "opening_time_error_s",
        "sink_delay_error_s",
        "pressure_at_opening_relative_error",
        "final_pressure_relative_error",
        "modern_fracture_initiation_time_s",
    ]
    result: dict[str, Any] = {}
    for key in keys:
        if key == "classification":
            result[key] = row.get(key, "")
        else:
            result[key] = _float(row.get(key))
    return result


def _manual_metrics(args: argparse.Namespace) -> dict[str, Any] | None:
    values = {
        "classification": args.manual_classification or "",
        "relative_error_max_pressure": args.manual_relative_error_max_pressure,
        "opening_time_error_s": args.manual_opening_time_error_s,
        "sink_delay_error_s": args.manual_sink_delay_error_s,
        "pressure_at_opening_relative_error": args.manual_pressure_at_opening_relative_error,
        "final_pressure_relative_error": args.manual_final_pressure_relative_error,
        "modern_fracture_initiation_time_s": args.manual_modern_fracture_initiation_time_s,
    }
    if all(value is None or value == "" for value in values.values()):
        return None
    return values


def _load_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    missing: list[str] = []
    phase10_24c: dict[str, Any] | None = None
    phase10_25b: dict[str, Any] | None = None

    if args.phase10_24c_summary and Path(args.phase10_24c_summary).exists():
        phase10_24c = _metrics_from_row(_read_first_row(Path(args.phase10_24c_summary)))
    else:
        missing.append(str(args.phase10_24c_summary))

    if args.phase10_25b_summary and Path(args.phase10_25b_summary).exists():
        phase10_25b = _metrics_from_row(_read_first_row(Path(args.phase10_25b_summary)))
    else:
        missing.append(str(args.phase10_25b_summary))

    manual = _manual_metrics(args)
    if phase10_25b is None and manual is not None:
        phase10_25b = manual
    if phase10_24c is None and manual is not None:
        phase10_24c = manual

    if phase10_24c is None or phase10_25b is None:
        raise FileNotFoundError(MISSING_SUMMARIES + ": " + ", ".join(missing))
    return phase10_24c, phase10_25b, missing


def _is_ok(value: float | None, tolerance: float) -> bool:
    return value is not None and abs(value) <= tolerance


def decide(phase10_24c: dict[str, Any], phase10_25b: dict[str, Any]) -> dict[str, Any]:
    pressure_ok = _is_ok(phase10_25b.get("relative_error_max_pressure"), 0.10)
    opening_ok = _is_ok(phase10_25b.get("opening_time_error_s"), 60.0)
    sink_ok = _is_ok(phase10_25b.get("sink_delay_error_s"), 1.0e-9)
    opening_improved = False
    old_opening = _float(phase10_24c.get("opening_time_error_s"))
    new_opening = _float(phase10_25b.get("opening_time_error_s"))
    if old_opening is not None and new_opening is not None:
        opening_improved = abs(new_opening) < abs(old_opening)

    if pressure_ok and opening_ok and sink_ok:
        decision = "NEXT_MODEL_SALT_WALL_STRESS_RUNTIME"
        rationale = (
            "Refined sigmaTheta resolves timing while preserving pressure and sink delay; "
            "prioritize a runtime salt wall stress source next."
        )
    elif pressure_ok and not opening_ok and not opening_improved:
        decision = "NEXT_MODEL_PRESSURE_SOURCE_TIMING_REVIEW"
        rationale = (
            "Refined sigmaTheta did not move the opening time; pressure scale and sink "
            "delay are already diagnostic-good, so review before/trial/after pressure timing."
        )
    elif pressure_ok and not opening_ok and opening_improved:
        decision = "NEXT_MODEL_SIGMA_THETA_POINT_MAPPING_REVIEW"
        rationale = (
            "Refined sigmaTheta improves but does not resolve opening timing; review layer, "
            "depth, nonlinear-visit and provider sampling alignment."
        )
    elif opening_ok and not pressure_ok:
        decision = "NEXT_MODEL_COMPLIANCE_REVISIT_REQUIRED"
        rationale = (
            "Opening timing is acceptable but pressure scale is not; revisit compliance/pressure "
            "model assumptions before runtime stress wiring."
        )
    elif (
        phase10_25b.get("classification")
        == "SIGMA_THETA_REFINED_TIMESERIES_EFFECTIVE"
    ):
        decision = "NEXT_MODEL_DIAGNOSTIC_ROUTE_SUFFICIENT"
        rationale = "The refined diagnostic route is sufficient for BUZ67D but remains opt-in."
    else:
        decision = "NEXT_MODEL_INCONCLUSIVE"
        rationale = "Available summaries do not support a stronger next-step decision."

    return {
        "phase": PHASE,
        "decision": decision,
        "physical_validation": False,
        "runtime_default_changed": False,
        "phase10_24c": phase10_24c,
        "phase10_25b": phase10_25b,
        "diagnostics": {
            "pressure_ok": pressure_ok,
            "opening_ok": opening_ok,
            "sink_ok": sink_ok,
            "opening_improved": opening_improved,
        },
        "rationale": rationale,
        "caveats": [
            "Decision is diagnostic, not physical validation.",
            "No SaltWallStressDiagnostics runtime provider is connected.",
            "No default LOT/PKN behavior changed.",
            "The refined series comes from temporary LOT_Tese tracing, not from the modern salt runtime.",
        ],
    }


def _write_markdown(path: Path, decision: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 10.25C sigmaTheta source decision",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "This is a diagnostic decision only. It is not physical validation.",
        "",
        "## Rationale",
        "",
        decision["rationale"],
        "",
        "## Metrics",
        "",
        "| Metric | 10.24C | 10.25B |",
        "|---|---:|---:|",
    ]
    for key in [
        "relative_error_max_pressure",
        "opening_time_error_s",
        "sink_delay_error_s",
        "pressure_at_opening_relative_error",
        "final_pressure_relative_error",
    ]:
        lines.append(
            f"| `{key}` | `{decision['phase10_24c'].get(key)}` | `{decision['phase10_25b'].get(key)}` |"
        )
    lines.extend(["", "## Caveats", ""])
    for caveat in decision["caveats"]:
        lines.append(f"- {caveat}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_decision(args: argparse.Namespace) -> dict[str, Any]:
    phase10_24c, phase10_25b, missing = _load_inputs(args)
    result = decide(phase10_24c, phase10_25b)
    result["missing_inputs"] = missing
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(Path(args.output_md), result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decide the Phase 10.25C next sigma-theta source path."
    )
    parser.add_argument("--phase10-24c-summary", type=Path)
    parser.add_argument("--phase10-25b-summary", type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--manual-classification")
    parser.add_argument("--manual-relative-error-max-pressure", type=float)
    parser.add_argument("--manual-opening-time-error-s", type=float)
    parser.add_argument("--manual-sink-delay-error-s", type=float)
    parser.add_argument("--manual-pressure-at-opening-relative-error", type=float)
    parser.add_argument("--manual-final-pressure-relative-error", type=float)
    parser.add_argument("--manual-modern-fracture-initiation-time-s", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        result = run_decision(build_parser().parse_args(argv))
    except FileNotFoundError as exc:
        if MISSING_SUMMARIES in str(exc):
            print(MISSING_SUMMARIES)
            return 2
        raise
    print(json.dumps({"phase": result["phase"], "decision": result["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
