#!/usr/bin/env python3
"""Phase 10.20A mechanical annular compliance audit helper.

This script is intentionally diagnostic. It does not read or mutate legacy
sources and it does not feed the runtime solver.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


K_FLUID_1_PA = 6.4e-10
C_EFF_DIAG_1_PA = 1.9211966938610006e-8
C_GEOM_DIAG_1_PA = 1.8571966938610005e-8
LEGACY_FIRST_DP_PA = 1845413.7784679066
MODERN_FIRST_DP_NO_COMPLIANCE_PA = 55397022.29498486


def inch_to_m(value: float) -> float:
    return value * 0.0254


def elastic_annular_simple_compressibility(
    *,
    inner_radius_m: float,
    outer_radius_m: float,
    inner_wall_thickness_m: float,
    inner_young_modulus_Pa: float,
    inner_poisson_ratio: float,
    formation_young_modulus_Pa: float,
    formation_poisson_ratio: float,
) -> dict[str, float]:
    """Return a simple equivalent geometric compressibility in 1/Pa.

    The approximation linearizes the per-radian annular area:

        V = 0.5 * (b^2 - a^2) * h
        dV / V ~= 2 * (b * u_b - a * u_a) / (b^2 - a^2)

    where the inner boundary moves inward under annular pressure and the outer
    formation boundary moves outward. The returned value is a positive
    magnitude and is meant as an opt-in diagnostic estimate.
    """

    if inner_radius_m <= 0.0 or outer_radius_m <= inner_radius_m:
        raise ValueError("outer_radius_m must be greater than inner_radius_m > 0")
    if inner_wall_thickness_m <= 0.0:
        raise ValueError("inner_wall_thickness_m must be positive")
    if inner_young_modulus_Pa <= 0.0 or formation_young_modulus_Pa <= 0.0:
        raise ValueError("Young moduli must be positive")
    if not (0.0 <= inner_poisson_ratio < 0.5):
        raise ValueError("inner_poisson_ratio must be in [0, 0.5)")
    if not (0.0 <= formation_poisson_ratio < 0.5):
        raise ValueError("formation_poisson_ratio must be in [0, 0.5)")

    inner_radial_compliance_m_per_Pa = (
        inner_radius_m * inner_radius_m
    ) / (inner_young_modulus_Pa * inner_wall_thickness_m)
    formation_radial_compliance_m_per_Pa = (
        (1.0 + formation_poisson_ratio) * outer_radius_m
    ) / formation_young_modulus_Pa

    denominator = outer_radius_m * outer_radius_m - inner_radius_m * inner_radius_m
    geometric_compressibility_1_Pa = 2.0 * (
        inner_radius_m * inner_radial_compliance_m_per_Pa
        + outer_radius_m * formation_radial_compliance_m_per_Pa
    ) / denominator

    return {
        "inner_radial_compliance_m_per_Pa": inner_radial_compliance_m_per_Pa,
        "formation_radial_compliance_m_per_Pa": formation_radial_compliance_m_per_Pa,
        "geometric_compressibility_1_Pa": geometric_compressibility_1_Pa,
        "effective_compressibility_1_Pa": K_FLUID_1_PA
        + geometric_compressibility_1_Pa,
        "ratio_to_diagnostic_geometric_compliance": (
            geometric_compressibility_1_Pa / C_GEOM_DIAG_1_PA
        ),
    }


def default_buz67d_inputs() -> dict[str, float]:
    drill_pipe_outer_radius_m = inch_to_m(5.5) / 2.0
    drill_pipe_inner_radius_m = inch_to_m(4.67) / 2.0
    borehole_radius_m = inch_to_m(13.5) / 2.0
    return {
        "inner_radius_m": drill_pipe_outer_radius_m,
        "outer_radius_m": borehole_radius_m,
        "inner_wall_thickness_m": drill_pipe_outer_radius_m
        - drill_pipe_inner_radius_m,
        "inner_young_modulus_Pa": 210.0e9,
        "inner_poisson_ratio": 0.30,
        "formation_young_modulus_Pa": 20.4e9,
        "formation_poisson_ratio": 0.36,
    }


def build_report() -> dict[str, object]:
    inputs = default_buz67d_inputs()
    estimate = elastic_annular_simple_compressibility(**inputs)
    predicted_first_dp = (
        MODERN_FIRST_DP_NO_COMPLIANCE_PA
        * K_FLUID_1_PA
        / estimate["effective_compressibility_1_Pa"]
    )
    return {
        "phase": "10.20A",
        "gate": "MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL",
        "classification": "ELASTIC_SIMPLE_FORMULATION_READY_AS_DIAGNOSTIC",
        "legacy_formula": {
            "dV_geom_m3_per_rad": "0.5 * h * ((b + u_outer)^2 - (a + u_inner)^2) - Vi",
            "pressure_balance": "dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k",
        },
        "diagnostic_baseline_10_19c": {
            "fluid_compressibility_1_Pa": K_FLUID_1_PA,
            "geometric_compressibility_1_Pa": C_GEOM_DIAG_1_PA,
            "effective_compressibility_1_Pa": C_EFF_DIAG_1_PA,
            "legacy_first_dP_Pa": LEGACY_FIRST_DP_PA,
        },
        "buz67d_default_inputs": inputs,
        "elastic_annular_simple_estimate": estimate,
        "predicted_first_dP_elastic_simple_Pa": predicted_first_dp,
        "caveat": (
            "Simple radial equivalent compliance is not a full APB/salt "
            "mechanical solve and is expected to under-represent the diagnostic "
            "constant compliance inferred from one legacy step."
        ),
    }


def write_outputs(report: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase10_20a_mechanical_compliance_audit.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    flat = {
        "gate": report["gate"],
        "classification": report["classification"],
        **report["diagnostic_baseline_10_19c"],
        **report["elastic_annular_simple_estimate"],
        "predicted_first_dP_elastic_simple_Pa": report[
            "predicted_first_dP_elastic_simple_Pa"
        ],
    }
    with (output_dir / "phase10_20a_mechanical_compliance_audit.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat))
        writer.writeheader()
        writer.writerow(flat)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Phase 10.20A mechanical annular compliance formulation."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory for JSON/CSV diagnostic outputs.",
    )
    args = parser.parse_args()

    report = build_report()
    if args.output_dir:
        write_outputs(report, args.output_dir)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
