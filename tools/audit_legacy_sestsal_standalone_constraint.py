#!/usr/bin/env python3
"""Audit why legacy SESTSAL should not be used as a standalone validation engine."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


PHASE = "11.10F-aux"
CAUSE = "LEGACY_SESTSAL_REQUIRES_APB1DA_COUPLING"
GATE = "DO_NOT_USE_SESTSAL_STANDALONE_AS_VALIDATION_REFERENCE"
SECONDARY_CAUSE = "ELASTIC_DISPLACEMENT_REFERENCE_MISMATCH"
SECONDARY_GATE = "ALIGN_TOTAL_VS_PERTURBATION_DISPLACEMENT_BEFORE_COMPARISON"
STATUS = "LEGACY_SESTSAL_STANDALONE_CONSTRAINT_RECORDED"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_line_number(text: str, pattern: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if pattern in line:
            return index
    return None


def hydrostatic_norm_sigd(sig_rr: float, sig_tt: float, sig_zz: float) -> float:
    sigd0 = (2.0 * sig_rr - sig_tt - sig_zz) / 3.0
    sigd1 = (-sig_rr + 2.0 * sig_tt - sig_zz) / 3.0
    sigd2 = (-sig_rr - sig_tt + 2.0 * sig_zz) / 3.0
    return math.sqrt(sigd0 * sigd0 + sigd1 * sigd1 + sigd2 * sigd2)


def classify_material(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "division_by_norm_sigd": False,
            "norm_sigd_guard_found": False,
            "line_norm_sigd": None,
            "line_division": None,
        }

    text = _read(path)
    division_by_norm_sigd = bool(re.search(r"1\.\s*/\s*norm_sigd\s*\*\s*sigd", text))
    guard_found = bool(re.search(r"if\s*\([^)]*norm_sigd\s*(?:==|<=|<)", text))
    return {
        "path": str(path),
        "exists": True,
        "division_by_norm_sigd": division_by_norm_sigd,
        "norm_sigd_guard_found": guard_found,
        "line_norm_sigd": find_line_number(text, "norm_sigd ="),
        "line_division": find_line_number(text, "1./norm_sigd"),
    }


def classify_apb1da(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "uses_set_inner_pressure": False,
            "uses_set_inner_temperature": False,
            "uses_solve_thermal_visco_step": False,
            "line_set_inner_pressure": None,
            "line_solve_thermal_visco_step": None,
        }
    text = _read(path)
    return {
        "path": str(path),
        "exists": True,
        "uses_set_inner_pressure": "setInnerPressure" in text,
        "uses_set_inner_temperature": "setInnerTemperature" in text,
        "uses_solve_thermal_visco_step": "solveThermalViscoStep" in text,
        "line_set_inner_pressure": find_line_number(text, "setInnerPressure"),
        "line_solve_thermal_visco_step": find_line_number(text, "solveThermalViscoStep"),
    }


def find_standalone_attempts(root: Path) -> list[str]:
    candidates: list[str] = []
    self_audit_names = {
        "audit_legacy_sestsal_standalone_constraint.py",
        "test_audit_legacy_sestsal_standalone_constraint.py",
        "docs_status.yaml",
    }
    for base in [root / "tests", root / "tools"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.name in self_audit_names:
                continue
            if path.is_file() and path.suffix.lower() in {".py", ".ps1", ".cpp", ".md", ".yaml", ".yml"}:
                text = _read(path)
                if "sestsal" in text.lower() and "standalone" in text.lower():
                    candidates.append(str(path))
    return sorted(candidates)


def build_audit(
    *,
    repo_root: Path,
    lot_tese_material: Path,
    lot_apb_material: Path,
    apb1da: Path,
) -> dict[str, Any]:
    material_audits = [
        classify_material(lot_tese_material),
        classify_material(lot_apb_material),
    ]
    apb_audit = classify_apb1da(apb1da)
    hydro_norm = hydrostatic_norm_sigd(10.0, 10.0, 10.0)
    division_present = any(row["division_by_norm_sigd"] for row in material_audits)
    unguarded = any(row["division_by_norm_sigd"] and not row["norm_sigd_guard_found"] for row in material_audits)
    apb_coupled = (
        apb_audit["uses_set_inner_pressure"]
        and apb_audit["uses_set_inner_temperature"]
        and apb_audit["uses_solve_thermal_visco_step"]
    )

    return {
        "phase": PHASE,
        "status": STATUS,
        "cause": CAUSE,
        "gate": GATE,
        "secondary_cause": SECONDARY_CAUSE,
        "secondary_gate": SECONDARY_GATE,
        "materials": material_audits,
        "apb1da_coupling": apb_audit,
        "hydrostatic_norm_sigd": hydro_norm,
        "hydrostatic_state_divides_by_zero": hydro_norm == 0.0 and unguarded,
        "norm_sigd_zero_generates_nan_risk": hydro_norm == 0.0 and unguarded,
        "division_by_norm_sigd_found": division_present,
        "norm_sigd_guard_missing": unguarded,
        "apb1da_coupled_usage_detected": apb_coupled,
        "standalone_validation_supported": False,
        "standalone_tests_status": "UNSUPPORTED",
        "displacement_reference_comparison_status": "BLOCKED_TOTAL_VS_PERTURBATION_REFERENCE_MISMATCH",
        "standalone_attempts_found": find_standalone_attempts(repo_root),
        "required_actions": [
            "Do not use legacy SESTSAL standalone as validation reference.",
            "Keep legacy SESTSAL evidence tied to APB1da-coupled execution context.",
            "Align total displacement versus perturbation displacement before comparing legacy and modern outputs.",
        ],
    }


def write_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.10F-aux Legacy SESTSAL Standalone Constraint Audit",
        "",
        f"- status: `{audit['status']}`",
        f"- cause: `{audit['cause']}`",
        f"- gate: `{audit['gate']}`",
        f"- secondary_cause: `{audit['secondary_cause']}`",
        f"- secondary_gate: `{audit['secondary_gate']}`",
        f"- standalone_validation_supported: `{str(audit['standalone_validation_supported']).lower()}`",
        f"- hydrostatic_state_divides_by_zero: `{str(audit['hydrostatic_state_divides_by_zero']).lower()}`",
        "",
        "## Material files",
        "",
        "| Path | Division by norm_sigd | Guard found | Line norm_sigd | Line division |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in audit["materials"]:
        lines.append(
            f"| `{row['path']}` | `{row['division_by_norm_sigd']}` | `{row['norm_sigd_guard_found']}` | `{row['line_norm_sigd']}` | `{row['line_division']}` |"
        )
    lines.extend(
        [
            "",
            "## Coupling evidence",
            "",
            f"- APB1da path: `{audit['apb1da_coupling']['path']}`",
            f"- uses_set_inner_pressure: `{audit['apb1da_coupling']['uses_set_inner_pressure']}`",
            f"- uses_set_inner_temperature: `{audit['apb1da_coupling']['uses_set_inner_temperature']}`",
            f"- uses_solve_thermal_visco_step: `{audit['apb1da_coupling']['uses_solve_thermal_visco_step']}`",
            "",
            "## Required actions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in audit["required_actions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit legacy SESTSAL standalone constraints and APB1da coupling dependency."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--lot-tese-material",
        type=Path,
        default=Path("legance/LOT_Tese/src/sestsal/material.cpp"),
    )
    parser.add_argument(
        "--lot-apb-material",
        type=Path,
        default=Path("legance/LOT_APB_v5/src/sestsal/material.cpp"),
    )
    parser.add_argument(
        "--apb1da",
        type=Path,
        default=Path("legance/LOT_Tese/src/apb_code/APB1da.cpp"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    audit = build_audit(
        repo_root=args.repo_root,
        lot_tese_material=args.lot_tese_material,
        lot_apb_material=args.lot_apb_material,
        apb1da=args.apb1da,
    )
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(audit, args.output_md)

    print(f"PHASE={audit['phase']}")
    print(f"STATUS={audit['status']}")
    print(f"CAUSE={audit['cause']}")
    print(f"GATE={audit['gate']}")
    print(f"SECONDARY_CAUSE={audit['secondary_cause']}")
    print(f"SECONDARY_GATE={audit['secondary_gate']}")
    print(f"STANDALONE_VALIDATION_SUPPORTED={str(audit['standalone_validation_supported']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
