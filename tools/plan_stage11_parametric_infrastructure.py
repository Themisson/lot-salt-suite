#!/usr/bin/env python3
"""Plan Stage 11 parametric infrastructure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


PLANNED_PHASES = [
    {
        "phase": "11.1B",
        "objective": "Create a canonical multi-study sensitivity matrix index.",
        "input": "Existing BUZ-67D C_geom sensitivity matrix.",
        "output": "Versioned studies_index.yaml and listing/validation tool.",
        "gate": "Existing matrix remains valid and discoverable.",
        "risk": "Index becomes another hardcoded list if not validated.",
    },
    {
        "phase": "11.2A",
        "objective": "Define a more expressive parametric matrix schema.",
        "input": "Current matrix YAML and runner behavior.",
        "output": "Documented matrix schema proposal and parser checks.",
        "gate": "No runtime solver change required.",
        "risk": "Schema expansion can outpace actual use cases.",
    },
    {
        "phase": "11.2B",
        "objective": "Generate derived cases from base_case plus explicit overrides.",
        "input": "Base case YAML and matrix overrides.",
        "output": "Reproducible generated case set under controlled output paths.",
        "gate": "Generated cases are diagnostic and not production inputs.",
        "risk": "Python must not become mandatory runtime preprocessing.",
    },
    {
        "phase": "11.3A",
        "objective": "Aggregate multiple matrices.",
        "input": "Study index and matrix summaries.",
        "output": "Multi-matrix summary metadata.",
        "gate": "All referenced studies pass validation.",
        "risk": "Comparisons may mix non-equivalent routes.",
    },
    {
        "phase": "11.3B",
        "objective": "Create comparative reports between matrices.",
        "input": "Aggregated summaries.",
        "output": "JSON/Markdown report with caveats and rankings.",
        "gate": "No physical validation claims are added.",
        "risk": "Diagnostic rankings can be misread as calibration.",
    },
    {
        "phase": "11.4A",
        "objective": "Add traceable parameter provenance.",
        "input": "Matrix, cases, and documented source values.",
        "output": "Provenance fields for parameter origin and caveats.",
        "gate": "No invented field data.",
        "risk": "Incomplete provenance can create false confidence.",
    },
    {
        "phase": "11.5A",
        "objective": "Prepare modern-refined packages for additional cases when data are sufficient.",
        "input": "Audited additional well data.",
        "output": "New modern-refined package or documented blocker.",
        "gate": "Case data are complete and compatible.",
        "risk": "Forcing non-PKN or incomplete cases into PKN YAML.",
    },
]


def build_plan() -> dict:
    return {
        "stage": 11,
        "primary_goal": "PARAMETRIC_INFRASTRUCTURE",
        "source": "DOCUMENTED_PHASE_SUMMARY",
        "inherited_from_stage10": [
            "BUZ67D_MODERN_REFINED_REPRODUCIBLE_PACKAGE",
            "VERSIONED_BUZ67D_CGEOM_SENSITIVITY_MATRIX",
            "GENERIC_LOT_PKN_SENSITIVITY_RUNNER",
            "SENSITIVITY_REPORT_GENERATOR",
        ],
        "recommended_first_implementation": "STAGE11_1B_MULTI_STUDY_MATRIX_INDEX",
        "planned_phases": PLANNED_PHASES,
        "blocked_items": [
            "APBSalt1D solver equivalence",
            "sigmaTheta runtime real provider",
            "SaltCreepTimeBridge runtime coupling",
            "automatic physical calibration",
            "pressure_tabulated_geometric",
        ],
        "global_acceptance": [
            "No protected case changes.",
            "No solver behavior changes.",
            "Generated results remain local.",
            "Each study declares route and caveats.",
            "Diagnostics are not promoted to physical validation.",
        ],
    }


def write_markdown(path: Path, plan: dict) -> None:
    lines = [
        "# Stage 11 parametric infrastructure plan",
        "",
        f"- stage: `{plan['stage']}`",
        f"- primary_goal: `{plan['primary_goal']}`",
        f"- recommended_first_implementation: `{plan['recommended_first_implementation']}`",
        f"- source: `{plan['source']}`",
        "",
        "## Planned Phases",
        "",
        "| Phase | Objective | Gate | Risk |",
        "|---|---|---|---|",
    ]
    for phase in plan["planned_phases"]:
        lines.append(f"| `{phase['phase']}` | {phase['objective']} | {phase['gate']} | {phase['risk']} |")
    lines.extend(["", "## Blocked Items", ""])
    lines.extend(f"- {item}" for item in plan["blocked_items"])
    lines.extend(["", "## Global Acceptance", ""])
    lines.extend(f"- {item}" for item in plan["global_acceptance"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    plan = build_plan()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, plan)
    print(f"STAGE={plan['stage']}")
    print(f"PRIMARY_GOAL={plan['primary_goal']}")
    print(f"RECOMMENDED_FIRST_IMPLEMENTATION={plan['recommended_first_implementation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
