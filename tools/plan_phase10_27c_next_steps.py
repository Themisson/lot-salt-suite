from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "10.27C"
SOURCE = "DOCUMENTED_PHASE_SUMMARY"


PLANNED_PHASES: list[dict[str, str]] = [
    {
        "phase": "10.28A",
        "route": "modern-refined",
        "objective": "modern-refined validation package for additional wells/cases",
        "precondition": "BUZ-67D modern-refined package documented and accepted",
        "expected_output": "Additional documented diagnostic case packages",
        "status": "planned",
    },
    {
        "phase": "10.28B",
        "route": "modern-refined",
        "objective": "modern-refined sensitivity study: mesh/domain/sampling",
        "precondition": "At least one stable modern-refined diagnostic package",
        "expected_output": "Sensitivity matrix for geometry, mesh and sigmaTheta sampling choices",
        "status": "planned",
    },
    {
        "phase": "10.28C",
        "route": "publication/reporting",
        "objective": "prepare publication-grade comparison plots",
        "precondition": "Modern-refined metrics and caveats frozen",
        "expected_output": "Plot/report package for thesis or article use",
        "status": "planned",
    },
    {
        "phase": "10.29A",
        "route": "legacy-equivalence",
        "objective": "APBSalt1D legacy-equivalence radial solver feasibility",
        "precondition": "Strict LOT_Tese regression remains a stated objective",
        "expected_output": "Feasibility decision for APBSalt1D-equivalent radial solver",
        "status": "planned_optional",
    },
    {
        "phase": "10.29B",
        "route": "legacy-equivalence",
        "objective": "APBSalt1D sampling bridge design, if radial samples become available",
        "precondition": "Spatial sigmaTheta samples or APBSalt1D-equivalent solver exist",
        "expected_output": "Sampling bridge design or explicit blocker",
        "status": "blocked_by_spatial_samples",
    },
    {
        "phase": "10.30A",
        "route": "salt-runtime",
        "objective": "SaltWallStressDiagnostics runtime integration plan",
        "precondition": "Decision to prioritize physical modern sigmaTheta source",
        "expected_output": "Runtime integration design preserving lot-pkn default behavior",
        "status": "planned",
    },
    {
        "phase": "10.30B",
        "route": "salt-runtime",
        "objective": "SigmaThetaProvider real salt runtime prototype",
        "precondition": "10.30A integration plan accepted",
        "expected_output": "Opt-in prototype using real salt wall stress diagnostics",
        "status": "planned",
    },
    {
        "phase": "10.31A",
        "route": "thermal/balance",
        "objective": "thermal term explicit modeling audit",
        "precondition": "Modern-refined pressure path remains diagnostically useful",
        "expected_output": "Thermal term audit and implementation gate",
        "status": "planned",
    },
    {
        "phase": "10.31B",
        "route": "thermal/balance",
        "objective": "dMl/leakoff explicit balance audit",
        "precondition": "Thermal/balance audit sequence remains in scope",
        "expected_output": "Explicit balance audit for leakoff/mass terms",
        "status": "planned",
    },
]


PRIORITIES: list[dict[str, str]] = [
    {
        "priority": "1",
        "phase": "10.28A / 10.28B",
        "justification": "Consolidates modern-refined evidence without forcing legacy mesh equivalence.",
        "risk": "Case-specific conclusions if only BUZ-67D is used.",
        "benefit": "Builds defensible modern validation before new runtime coupling.",
    },
    {
        "priority": "2",
        "phase": "10.28C",
        "justification": "Turns the documented diagnostic package into reviewable figures.",
        "risk": "Plots can be overinterpreted without caveats.",
        "benefit": "Improves thesis/article communication and technical review.",
    },
    {
        "priority": "3",
        "phase": "10.30A / 10.30B",
        "justification": "Moves toward a physical modern sigmaTheta source.",
        "risk": "Runtime salt coupling can expand architecture and validation scope.",
        "benefit": "Reduces dependence on diagnostic time-series providers.",
    },
    {
        "priority": "4",
        "phase": "10.29A / 10.29B",
        "justification": "Only needed for strict LOT_Tese regression.",
        "risk": "May reproduce legacy behavior without improving physical validation.",
        "benefit": "Can isolate whether the 510 s opening is a mesh/domain artifact.",
    },
]


BLOCKED_GATES = [
    "APBSALT1D_SAMPLING_BRIDGE_BLOCKED",
    "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY",
    "APBSALT1D_SOLVER_EQUIVALENCE_REQUIRED_FOR_STRICT_MATCH",
    "SIGMATHETA_RUNTIME_STILL_FUTURE_WORK",
]


RISK_REGISTER = [
    "modern-refined mode is not strict LOT_Tese regression",
    "constant_geometric remains a diagnostic baseline",
    "APBSalt1D metadata is not consumed without spatial sigmaTheta samples",
    "pressure_source/timing analysis remains blocked by geometry for legacy-equivalence claims",
    "SaltWallStressDiagnostics runtime integration is future work",
]


def build_roadmap() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "source": SOURCE,
        "current_recommended_next_phase": "10.28A",
        "current_recommended_next_phase_classification": (
            "NEXT_PHASE_MODERN_REFINED_VALIDATION_OR_SENSITIVITY"
        ),
        "status": "POST_10_27_ROADMAP_RECORDED",
        "planned_phases": PLANNED_PHASES,
        "priorities": PRIORITIES,
        "blocked_gates": BLOCKED_GATES,
        "risk_register": RISK_REGISTER,
    }


def _write_markdown(roadmap: dict[str, Any], path: Path) -> None:
    lines = [
        "# Post-10.27 roadmap",
        "",
        f"- source: `{roadmap['source']}`",
        f"- status: `{roadmap['status']}`",
        f"- current_recommended_next_phase: `{roadmap['current_recommended_next_phase']}`",
        f"- classification: `{roadmap['current_recommended_next_phase_classification']}`",
        "",
        "## Planned phases",
        "",
        "| Phase | Route | Objective | Precondition | Expected output | Status |",
        "|---|---|---|---|---|---|",
    ]
    for phase in roadmap["planned_phases"]:
        lines.append(
            "| {phase} | {route} | {objective} | {precondition} | {expected_output} | {status} |".format(
                **phase
            )
        )
    lines.extend(
        [
            "",
            "## Priorities",
            "",
            "| Priority | Phase | Justification | Risk | Benefit |",
            "|---:|---|---|---|---|",
        ]
    )
    for item in roadmap["priorities"]:
        lines.append(
            "| {priority} | {phase} | {justification} | {risk} | {benefit} |".format(
                **item
            )
        )
    lines.extend(["", "## Blocked gates", ""])
    lines.extend(f"- `{gate}`" for gate in roadmap["blocked_gates"])
    lines.extend(["", "## Risk register", ""])
    lines.extend(f"- {risk}" for risk in roadmap["risk_register"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan Phase 10.27C post-10.27 validation roadmap."
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    roadmap = build_roadmap()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(roadmap, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(roadmap, args.output_md)

    print(
        json.dumps(
            {
                "phase": roadmap["phase"],
                "status": roadmap["status"],
                "current_recommended_next_phase": roadmap[
                    "current_recommended_next_phase"
                ],
                "classification": roadmap[
                    "current_recommended_next_phase_classification"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
