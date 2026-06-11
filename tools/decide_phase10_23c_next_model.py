from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


PHASE = "10.23C"


def _read_one_row_csv(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"CSV is empty: {path}")
    return dict(rows[0])


def _float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _blocked_missing(path_a: Path, path_b: Path) -> dict[str, Any]:
    missing = [str(path) for path in [path_a, path_b] if not path.exists()]
    return {
        "phase": PHASE,
        "status": "PHASE10_23C_BLOCKED_MISSING_PHASE_SUMMARIES",
        "decision": "NEXT_MODEL_INCONCLUSIVE",
        "missing_inputs": missing,
        "pressure_tabulated_geometric_allowed": False,
        "physical_validation": False,
        "next_phase_recommendation": "Regenerate Phase 10.23A and 10.23B summaries before deciding.",
        "justification": "Required diagnostic summaries are missing.",
    }


def _decision(summary_a: dict[str, str], summary_b: dict[str, str]) -> dict[str, Any]:
    b_class = summary_b.get("classification", "")
    b_rel = _float(summary_b.get("relative_error_max_pressure"))
    b_open = _float(summary_b.get("modern_fracture_initiation_time_s"))
    b_sink_delay = _float(summary_b.get("modern_sink_delay_s"))
    a_class = summary_a.get("classification", "")

    pressure_ok = b_rel is not None and abs(b_rel) <= 0.10
    opening_ok = b_open is not None and abs(b_open - 510.0) <= 60.0
    sink_ok = b_sink_delay is not None and abs(b_sink_delay - 30.0) <= 1.0e-9

    if b_class == "COMBINED_DIAGNOSTIC_EFFECTIVE" and pressure_ok and opening_ok and sink_ok:
        decision = "NEXT_MODEL_CONSTANT_GEOMETRIC_DIAGNOSTIC_SUFFICIENT"
        recommendation = (
            "Keep constant_geometric as diagnostic-only and validate the workflow "
            "against additional controlled wells before adding new runtime physics."
        )
        justification = "Pressure, opening timing and sink delay are all within diagnostic gates."
        sigma_theta_runtime_priority = False
        phase_dependent_compliance_priority = False
    elif pressure_ok and not opening_ok:
        decision = "NEXT_MODEL_SIGMA_THETA_RUNTIME"
        recommendation = (
            "Prioritize an opt-in sigma-theta runtime provider or a better opening "
            "criterion before adding pressure_tabulated_geometric."
        )
        justification = (
            "The combined route matches pressure scale and sink delay, but opening remains shifted."
        )
        sigma_theta_runtime_priority = True
        phase_dependent_compliance_priority = False
    elif sink_ok and not pressure_ok:
        decision = "NEXT_MODEL_PHASE_DEPENDENT_COMPLIANCE"
        recommendation = (
            "Investigate phase-dependent compliance after preserving next-step sink timing."
        )
        justification = "Sink chronology is aligned but pressure scale remains outside tolerance."
        sigma_theta_runtime_priority = False
        phase_dependent_compliance_priority = True
    else:
        decision = "NEXT_MODEL_INCONCLUSIVE"
        recommendation = "Collect additional diagnostics before choosing a model path."
        justification = "The available summaries do not satisfy a clear decision rule."
        sigma_theta_runtime_priority = False
        phase_dependent_compliance_priority = False

    return {
        "phase": PHASE,
        "status": "PHASE10_23C_DECISION_COMPLETE",
        "decision": decision,
        "phase10_23a_classification": a_class,
        "phase10_23b_classification": b_class,
        "metrics": {
            "relative_error_max_pressure": b_rel,
            "modern_fracture_initiation_time_s": b_open,
            "modern_sink_delay_s": b_sink_delay,
            "pressure_ok": pressure_ok,
            "opening_ok": opening_ok,
            "sink_ok": sink_ok,
        },
        "pressure_tabulated_geometric_allowed": False,
        "pressure_tabulated_geometric_status": "NEXT_MODEL_PRESSURE_TABULATED_STILL_BLOCKED",
        "sigma_theta_runtime_priority": sigma_theta_runtime_priority,
        "phase_dependent_compliance_priority": phase_dependent_compliance_priority,
        "physical_validation": False,
        "next_phase_recommendation": recommendation,
        "justification": justification,
        "caveats": [
            "Decision is based on diagnostic summaries, not physical validation.",
            "pressure_tabulated_geometric remains blocked.",
            "No new solver, runtime wiring or legacy instrumentation is implemented in Phase 10.23C.",
        ],
    }


def _write_markdown(path: Path, decision: dict[str, Any]) -> None:
    lines = [
        "# Phase 10.23C next model decision",
        "",
        f"- status: `{decision['status']}`",
        f"- decision: `{decision['decision']}`",
        f"- pressure_tabulated_geometric_allowed: `{decision['pressure_tabulated_geometric_allowed']}`",
        f"- recommendation: {decision['next_phase_recommendation']}",
        "",
        "## Justification",
        "",
        decision["justification"],
        "",
        "## Metrics",
        "",
    ]
    for key, value in decision.get("metrics", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Caveats", ""])
    for caveat in decision.get("caveats", []):
        lines.append(f"- {caveat}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_decision(args: argparse.Namespace) -> dict[str, Any]:
    summary_a = Path(args.phase10_23a_summary)
    summary_b = Path(args.phase10_23b_summary)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not summary_a.exists() or not summary_b.exists():
        decision = _blocked_missing(summary_a, summary_b)
    else:
        decision = _decision(_read_one_row_csv(summary_a), _read_one_row_csv(summary_b))
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    _write_markdown(output_md, decision)
    return decision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decide the next LOT compliance/opening model path from Phase 10.23 summaries."
    )
    parser.add_argument("--phase10-23a-summary", required=True, type=Path)
    parser.add_argument("--phase10-23b-summary", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    decision = run_decision(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": decision["phase"],
                "status": decision["status"],
                "decision": decision["decision"],
                "next_phase_recommendation": decision["next_phase_recommendation"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
