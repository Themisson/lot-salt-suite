#!/usr/bin/env python3
"""Plan Phase 10.28B additional-well or BUZ-67D sensitivity route."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PHASE = "10.28B"
READY_ROUTE = "ADDITIONAL_WELL_READY"
SENSITIVITY_ROUTE = "ADDITIONAL_WELL_BLOCKED_SENSITIVITY_SELECTED"
NO_ROUTE = "NO_ACTIONABLE_ROUTE"


@dataclass(frozen=True)
class Candidate:
    path: str
    kind: str
    model_hint: str
    status: str
    reason: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    c_geom_factor: float
    sink_timing: str
    sigma_theta_source: str


def planned_scenarios() -> list[Scenario]:
    return [
        Scenario("S0_baseline", "Baseline modern-refined BUZ-67D", 1.0, "next_step", "refined_time_series"),
        Scenario("S1_lower_compliance", "Lower diagnostic geometric compliance", 0.75, "next_step", "refined_time_series"),
        Scenario("S2_higher_compliance", "Higher diagnostic geometric compliance", 1.25, "next_step", "refined_time_series"),
        Scenario("S3_same_step", "Sink timing comparison at baseline compliance", 1.0, "same_step", "refined_time_series"),
    ]


def _is_probably_comment(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("#")


def active_pkn_source(text: str) -> bool:
    for line in text.splitlines():
        if _is_probably_comment(line):
            continue
        if re.search(r"\bpkn\b", line, flags=re.IGNORECASE):
            if "setLeakoffProps" in line or "PKN" in line.upper():
                return True
    return False


def active_non_pkn_hint(text: str) -> str:
    for label in ("penny-shaped", "circular", "elliptical", "kgd", "zamora"):
        for line in text.splitlines():
            if _is_probably_comment(line):
                continue
            if label.lower() in line.lower():
                return label
    return "unknown"


def find_candidates(legacy_root: Path) -> list[Candidate]:
    if not legacy_root.exists():
        return []

    candidates: list[Candidate] = []
    pattern = re.compile(r"(29D|BUZ29|BUZ-29|BUZ|LOT|pkn|kgd|penny)", flags=re.IGNORECASE)
    for path in sorted(p for p in legacy_root.rglob("*") if p.is_file()):
        if not pattern.search(path.name):
            continue
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".exe", ".o", ".obj"}:
            continue
        kind = "source" if suffix in {".cpp", ".h", ".hpp", ".cxx"} else "output_or_auxiliary"
        model_hint = "unknown"
        status = "CANDIDATE"
        reason = "Name matches BUZ/LOT/PKN search terms."
        if kind == "source":
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
            if active_pkn_source(text):
                model_hint = "PKN"
                status = "POTENTIAL_PKN_SOURCE"
                reason = "Contains an active PKN-like source line; still requires full parameter audit."
            else:
                model_hint = active_non_pkn_hint(text)
                if model_hint != "unknown":
                    status = "NOT_READY_NON_PKN_OR_ALTERNATIVE_MODEL"
                    reason = f"Active model hint is {model_hint}; PKN line is absent or commented."
                else:
                    status = "NEEDS_MORE_AUDIT"
                    reason = "No active PKN evidence found in quick read-only scan."
        elif "PKN" in path.name.upper():
            model_hint = "PKN_output_only"
            status = "OUTPUT_ONLY"
            reason = "PKN appears in output/helper name, but this is not a complete source case."
        candidates.append(Candidate(str(path), kind, model_hint, status, reason))
    return candidates


def decide_route(legacy_root: Path) -> dict:
    candidates = find_candidates(legacy_root)
    buz29_candidates = [c for c in candidates if re.search(r"(29D|BUZ29|BUZ-29)", c.path, re.IGNORECASE)]
    buz29_pkn_sources = [c for c in buz29_candidates if c.status == "POTENTIAL_PKN_SOURCE"]

    blocked_reasons: list[str] = []
    if not legacy_root.exists():
        buz29d_status = "BUZ29D_SOURCE_NOT_FOUND"
        blocked_reasons.append("legance/LOT_Tese is not available in this checkout.")
    elif not buz29_candidates:
        buz29d_status = "BUZ29D_SOURCE_NOT_FOUND"
        blocked_reasons.append("No BUZ-29D candidate was found in the legacy tree.")
    elif buz29_pkn_sources:
        buz29d_status = "BUZ29D_NEEDS_MORE_AUDIT"
        blocked_reasons.append("PKN-like candidates exist but are not yet a fully audited modern-refined case.")
    else:
        buz29d_status = "BUZ29D_NOT_PKN"
        blocked_reasons.append("BUZ-29D sources found in the quick scan are not ready PKN cases; active hints are alternative models or output-only artifacts.")

    route_decision = SENSITIVITY_ROUTE
    sensitivity_status = "SENSITIVITY_MATRIX_READY"
    selected_case = "BUZ67D_MODERN_REFINED_SENSITIVITY_MATRIX"
    recommendation = "RUN_BUZ67D_MODERN_REFINED_SENSITIVITY_MATRIX_IN_10_28C"

    if not candidates and not legacy_root.exists():
        route_decision = SENSITIVITY_ROUTE
    elif buz29d_status == "BUZ29D_NEEDS_MORE_AUDIT":
        route_decision = SENSITIVITY_ROUTE

    return {
        "phase": PHASE,
        "route_decision": route_decision,
        "buz29d_status": buz29d_status,
        "selected_case": selected_case,
        "sensitivity_matrix_status": sensitivity_status,
        "planned_scenarios": [asdict(s) for s in planned_scenarios()],
        "blocked_reasons": blocked_reasons,
        "recommendation_for_10_28C": recommendation,
        "legacy_root": str(legacy_root),
        "candidate_count": len(candidates),
        "candidates": [asdict(c) for c in candidates[:80]],
        "caveats": [
            "BUZ-29D output artifacts alone are not enough to create a modern validation YAML.",
            "The fallback matrix is modern-refined sensitivity, not strict LOT_Tese regression.",
            "No legacy files are modified and no results artifacts are versioned.",
        ],
    }


def render_markdown(decision: dict) -> str:
    lines = [
        "# Phase 10.28B route decision",
        "",
        f"- phase: `{decision['phase']}`",
        f"- route_decision: `{decision['route_decision']}`",
        f"- buz29d_status: `{decision['buz29d_status']}`",
        f"- selected_case: `{decision['selected_case']}`",
        f"- sensitivity_matrix_status: `{decision['sensitivity_matrix_status']}`",
        f"- recommendation_for_10_28C: `{decision['recommendation_for_10_28C']}`",
        "",
        "## Blocked Reasons",
    ]
    lines.extend(f"- {reason}" for reason in decision["blocked_reasons"])
    lines.extend(["", "## Planned Sensitivity Matrix", "", "| Scenario | C_geom factor | sink_timing | sigmaTheta |", "|---|---:|---|---|"])
    for scenario in decision["planned_scenarios"]:
        lines.append(
            f"| {scenario['scenario_id']} | {scenario['c_geom_factor']} | {scenario['sink_timing']} | {scenario['sigma_theta_source']} |"
        )
    lines.extend(["", "## Candidate Sample", "", "| Path | Kind | Model hint | Status | Reason |", "|---|---|---|---|---|"])
    for candidate in decision["candidates"][:20]:
        lines.append(
            f"| `{candidate['path']}` | {candidate['kind']} | {candidate['model_hint']} | {candidate['status']} | {candidate['reason']} |"
        )
    lines.extend(["", "## Caveats"])
    lines.extend(f"- {caveat}" for caveat in decision["caveats"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(decision: dict, output_json: Path | None, output_md: Path | None) -> None:
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(decision), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, default=Path("legance/LOT_Tese"))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision = decide_route(args.legacy_root)
    write_outputs(decision, args.output_json, args.output_md)
    print(f"PHASE={decision['phase']}")
    print(f"ROUTE_DECISION={decision['route_decision']}")
    print(f"BUZ29D_STATUS={decision['buz29d_status']}")
    print(f"SENSITIVITY_MATRIX_STATUS={decision['sensitivity_matrix_status']}")
    print(f"RECOMMENDATION_FOR_10_28C={decision['recommendation_for_10_28C']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
