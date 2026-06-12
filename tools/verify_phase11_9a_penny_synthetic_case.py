#!/usr/bin/env python3
"""Verify the Phase 11.9A synthetic PennyShaped diagnostic case."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import yaml


REQUIRED_CAVEATS = [
    "Synthetic diagnostic case only",
    "Not BUZ29 validation",
    "Not legacy equivalence",
]


def _load_case(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"case not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("case root must be a mapping")
    return data


def _number(data: dict[str, Any], section: str, field: str) -> float:
    section_data = data.get(section)
    if not isinstance(section_data, dict):
        raise ValueError(f"missing section: {section}")
    value = section_data.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"missing numeric field: {section}.{field}")
    return float(value)


def evaluate(data: dict[str, Any]) -> dict[str, float]:
    young = _number(data, "elasticity", "young_modulus_Pa")
    nu = _number(data, "elasticity", "poisson_ratio")
    mu = _number(data, "fluid", "viscosity_Pa_min")
    q = _number(data, "injection", "flow_rate_m3_min")
    time = _number(data, "initiation", "elapsed_since_opening_min")
    pw = _number(data, "initiation", "wellbore_pressure_Pa")
    sigma = _number(data, "initiation", "sigma_theta_compression_positive_Pa")
    multiplier = _number(data, "legacy_options", "volume_multiplier")

    if young <= 0.0 or not (0.0 <= nu < 0.5) or mu <= 0.0:
        raise ValueError("invalid elastic/fluid inputs")
    if q < 0.0 or time < 0.0 or pw < 0.0 or sigma <= 0.0 or multiplier < 0.0:
        raise ValueError("invalid pressure, time or multiplier inputs")

    epd = young / (1.0 - nu * nu)
    pressure_factor = pw / sigma
    if q == 0.0 or time == 0.0:
        opening = 0.0
        radius = 0.0
    else:
        opening = 3.65 * ((mu * mu * q**3) / (epd * epd)) ** (1.0 / 9.0) * (
            time ** (1.0 / 9.0)
        )
        radius = 0.572 * ((epd * q**3) / mu) ** (1.0 / 9.0) * (
            time ** (4.0 / 9.0)
        )
    volume = multiplier * (opening / 2.0) ** 2 * radius * math.pi * pressure_factor
    return {
        "plane_strain_modulus_Pa": epd,
        "opening_m": opening,
        "radius_m": radius,
        "pressure_factor": pressure_factor,
        "fracture_volume_proxy_m3": volume,
    }


def verify_case(path: Path) -> dict[str, Any]:
    data = _load_case(path)
    model = data.get("model", {})
    if model.get("type") != "penny_shaped_diagnostic":
        status = "PENNY_SYNTHETIC_CASE_INVALID"
        outputs: dict[str, float] = {}
    else:
        outputs = evaluate(data)
        caveat = str(data.get("diagnostics", {}).get("caveat", ""))
        missing_caveats = [marker for marker in REQUIRED_CAVEATS if marker not in caveat]
        status = (
            "PENNY_SYNTHETIC_CASE_CREATED"
            if not missing_caveats
            else "PENNY_SYNTHETIC_CASE_PARTIAL"
        )
    return {
        "phase": "11.9A",
        "status": status,
        "case": str(path),
        "runtime_schema": False,
        "lot_sim_runtime_case": False,
        "physical_validation": False,
        "legacy_equivalence": False,
        "buz29_validation": False,
        "outputs": outputs,
        "caveats": [
            "Synthetic diagnostic case only.",
            "Not BUZ29 validation.",
            "Not legacy equivalence.",
            "Not an official lot-sim runtime schema route.",
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.9A PennyShaped Synthetic Case Verification",
        "",
        f"- status: `{result['status']}`",
        f"- case: `{result['case']}`",
        "- runtime_schema: `false`",
        "- physical_validation: `false`",
        "- legacy_equivalence: `false`",
        "",
        "## Outputs",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in result["outputs"].items())
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Phase 11.9A synthetic PennyShaped diagnostic case."
    )
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = verify_case(args.case)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)
    print("PHASE=11.9A")
    print(f"STATUS={result['status']}")
    print(f"CASE={args.case}")
    return 0 if result["status"] in {"PENNY_SYNTHETIC_CASE_CREATED", "PENNY_SYNTHETIC_CASE_PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
