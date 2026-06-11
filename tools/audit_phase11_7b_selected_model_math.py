#!/usr/bin/env python3
"""Audit the selected non-PKN model mathematics for Phase 11.7B."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


PHASE = "11.7B"
SELECTED_TRACK = "PENNY_SHAPED"
STATUS = "SELECTED_MODEL_MATH_AUDITED"
IMPLEMENTATION_READINESS = "MINIMAL_IMPLEMENTATION_READY_DIAGNOSTIC_ONLY"


def build_audit() -> dict:
    equations = [
        {
            "name": "plane_strain_modulus",
            "expression": "EPd = E / (1 - nu^2)",
            "legacy_source": "legance/LOT_Tese/src/apb_code/APB1da.cpp:1220-1221",
            "status": "EXTRACTED",
        },
        {
            "name": "shear_modulus",
            "expression": "G = E / (2 * (1 + nu))",
            "legacy_source": "legance/LOT_Tese/src/apb_code/APB1da.cpp:1222 and 1323",
            "status": "EXTRACTED",
        },
        {
            "name": "opening_legacy_penny_shaped",
            "expression": "w0 = 3.65 * ((mu^2 * Qinj^3) / EPd^2)^(1/9) * time^(1/9)",
            "legacy_source": "legance/LOT_Tese/src/apb_code/APB1da.cpp:1330",
            "status": "EXTRACTED",
        },
        {
            "name": "radius_legacy_penny_shaped",
            "expression": "R = 0.572 * ((EPd * Qinj^3) / mu)^(1/9) * time^(4/9)",
            "legacy_source": "legance/LOT_Tese/src/apb_code/APB1da.cpp:1331",
            "status": "EXTRACTED",
        },
        {
            "name": "opening_pressure_factor",
            "expression": "pressureFactor = pw / sigmaTheta",
            "legacy_source": "legance/LOT_Tese/src/apb_code/APB1da.cpp:1335",
            "status": "EXTRACTED",
        },
        {
            "name": "leakoff_volume_proxy",
            "expression": "dV_leakoff = 10 * (w0 / 2)^2 * R * pi * pressureFactor",
            "legacy_source": "legance/LOT_Tese/src/apb_code/APB1da.cpp:1338",
            "status": "EXTRACTED",
        },
    ]
    variables = [
        {"symbol": "E", "unit": "Pa", "meaning": "Young modulus from active rock layer", "status": "EXTRACTED"},
        {"symbol": "nu", "unit": "-", "meaning": "Poisson ratio from active rock layer", "status": "EXTRACTED"},
        {"symbol": "EPd", "unit": "Pa", "meaning": "plane-strain elastic modulus proxy", "status": "EXTRACTED"},
        {"symbol": "mu", "unit": "Pa*min", "meaning": "converted LOT fluid viscosity when strViscosity is pa_min", "status": "EXTRACTED"},
        {"symbol": "Qinj", "unit": "m3/min", "meaning": "injection flow converted by ConvflowRate", "status": "EXTRACTED"},
        {"symbol": "time", "unit": "min", "meaning": "t - firstTimePwExceedsSigmaMin", "status": "EXTRACTED"},
        {"symbol": "pw", "unit": "Pa", "meaning": "wellbore/annular pressure pi + dP", "status": "EXTRACTED"},
        {"symbol": "sigmaTheta", "unit": "Pa", "meaning": "-mdl->getSigmaTheta(), compression-positive threshold", "status": "EXTRACTED"},
        {"symbol": "w0", "unit": "m", "meaning": "maximum penny-shaped fracture opening proxy", "status": "INFERRED_FROM_DIMENSIONAL_CONTRACT"},
        {"symbol": "R", "unit": "m", "meaning": "penny-shaped fracture radius proxy", "status": "INFERRED_FROM_DIMENSIONAL_CONTRACT"},
    ]
    return {
        "phase": PHASE,
        "selected_track": SELECTED_TRACK,
        "status": STATUS,
        "legacy_sources": [
            "legance/LOT_Tese/src/apb_code/APB1da.cpp",
            "legance/LOT_Tese/include/apb_code/APB1da.h",
            "legance/LOT_Tese/src/apb_code/Fluids.cpp",
            "legance/LOT_Tese/include/apb_code/Fluids.h",
            "legance/LOT_Tese/BUZ29-VISCO-first-well.cpp",
        ],
        "equations": equations,
        "variables": variables,
        "units": ["Pa", "m", "min", "m3/min", "Pa*min"],
        "required_inputs": [
            "young_modulus_Pa",
            "poisson_ratio",
            "viscosity_Pa_min",
            "flow_rate_m3_min",
            "elapsed_since_opening_min",
            "wellbore_pressure_Pa",
            "sigma_theta_compression_positive_Pa",
        ],
        "expected_outputs": [
            "opening_m",
            "radius_m",
            "pressure_factor",
            "fracture_volume_proxy_m3",
        ],
        "implementation_readiness": IMPLEMENTATION_READINESS,
        "blocking_gaps": [
            "Full legacy equivalence still depends on APB/salt state, sigmaTheta source, and pressure history.",
            "The factor 10 in dV_leakoff is empirical/legacy-specific and should remain explicit.",
        ],
        "recommended_next_phase": "PHASE11_7C_SELECTED_MODEL_YAML_IO_SPEC",
        "caveats": [
            "Mathematics audited only; no modern model is implemented in Phase 11.7B.",
            "Minimum implementation can cover isolated formulas, not BUZ29 validation.",
        ],
    }


def write_markdown(path: Path, audit: dict) -> None:
    lines = [
        "# Phase 11.7B selected non-PKN model math audit",
        "",
        "## Summary",
        "",
        f"- `selected_track`: `{audit['selected_track']}`",
        f"- `status`: `{audit['status']}`",
        f"- `implementation_readiness`: `{audit['implementation_readiness']}`",
        f"- `recommended_next_phase`: `{audit['recommended_next_phase']}`",
        "",
        "A auditoria matemática da 11.7B não implementa o modelo moderno. Ela define a base técnica mínima para especificação de YAML/IO e implementação posterior.",
        "",
        "## Legacy sources",
        "",
    ]
    for source in audit["legacy_sources"]:
        lines.append(f"- `{source}`")
    lines.extend(["", "## Equations", "", "| Item | Expression | Legacy source | Status |", "|---|---|---|---|"])
    for equation in audit["equations"]:
        lines.append(
            f"| `{equation['name']}` | `{equation['expression']}` | `{equation['legacy_source']}` | `{equation['status']}` |"
        )
    lines.extend(["", "## Variables and units", "", "| Symbol | Unit | Meaning | Status |", "|---|---|---|---|"])
    for variable in audit["variables"]:
        lines.append(
            f"| `{variable['symbol']}` | `{variable['unit']}` | {variable['meaning']} | `{variable['status']}` |"
        )
    lines.extend(["", "## Required inputs", ""])
    for item in audit["required_inputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Expected outputs", ""])
    for item in audit["expected_outputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocking gaps", ""])
    for gap in audit["blocking_gaps"]:
        lines.append(f"- {gap}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    audit = build_audit()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, audit)
    print(f"PHASE={audit['phase']}")
    print(f"STATUS={audit['status']}")
    print(f"SELECTED_TRACK={audit['selected_track']}")
    print(f"IMPLEMENTATION_READINESS={audit['implementation_readiness']}")
    print(f"NEXT_PHASE={audit['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
