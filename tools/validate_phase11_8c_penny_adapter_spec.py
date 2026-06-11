#!/usr/bin/env python3
"""Validate the Phase 11.8C PennyShaped diagnostic adapter fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_NUMERIC_FIELDS = {
    "elasticity": ["young_modulus_Pa", "poisson_ratio"],
    "fluid": ["viscosity_Pa_min"],
    "injection": ["flow_rate_m3_min"],
    "initiation": [
        "elapsed_since_opening_min",
        "wellbore_pressure_Pa",
        "sigma_theta_compression_positive_Pa",
    ],
    "legacy_options": ["volume_multiplier"],
}

REQUIRED_OUTPUTS = {
    "plane_strain_modulus_Pa",
    "opening_m",
    "radius_m",
    "pressure_factor",
    "fracture_volume_proxy_m3",
}

REQUIRED_CAVEAT_MARKERS = [
    "Diagnostic adapter",
    "not BUZ29 validation",
    "not legacy equivalence",
]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"fixture not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("fixture root must be a mapping")
    return data


def validate_fixture(path: Path) -> dict[str, Any]:
    data = _read_yaml(path)
    missing_fields: list[str] = []
    invalid_fields: list[str] = []

    model = data.get("model", {})
    if model.get("type") != "penny_shaped_diagnostic":
        invalid_fields.append("model.type")
    if model.get("integration_path") != "diagnostic_adapter":
        invalid_fields.append("model.integration_path")

    for section, fields in REQUIRED_NUMERIC_FIELDS.items():
        section_data = data.get(section)
        if not isinstance(section_data, dict):
            missing_fields.append(section)
            continue
        for field in fields:
            key = f"{section}.{field}"
            value = section_data.get(field)
            if value is None:
                missing_fields.append(key)
            elif not _is_number(value):
                invalid_fields.append(key)

    outputs = set(data.get("expected_outputs") or [])
    missing_outputs = sorted(REQUIRED_OUTPUTS.difference(outputs))

    caveat = str(data.get("diagnostics", {}).get("caveat", ""))
    missing_caveats = [marker for marker in REQUIRED_CAVEAT_MARKERS if marker not in caveat]

    if missing_fields or invalid_fields or missing_outputs:
        status = "PENNY_ADAPTER_SPEC_INVALID"
    elif missing_caveats:
        status = "PENNY_ADAPTER_SPEC_PARTIAL"
    else:
        status = "PENNY_ADAPTER_SPEC_VALID"

    return {
        "phase": "11.8C",
        "status": status,
        "fixture": str(path),
        "model_type": model.get("type"),
        "integration_path": model.get("integration_path"),
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "missing_outputs": missing_outputs,
        "missing_caveats": missing_caveats,
        "expected_outputs": sorted(outputs),
        "physical_validation": False,
        "legacy_equivalence": False,
        "buz29_validation": False,
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phase 11.8C PennyShaped Diagnostic Adapter Spec",
        "",
        f"- status: `{result['status']}`",
        f"- fixture: `{result['fixture']}`",
        f"- model_type: `{result.get('model_type')}`",
        f"- integration_path: `{result.get('integration_path')}`",
        "- physical_validation: `false`",
        "- legacy_equivalence: `false`",
        "- buz29_validation: `false`",
        "",
        "## Missing Fields",
        "",
    ]
    lines.extend(f"- `{item}`" for item in result["missing_fields"] or ["none"])
    lines.extend(["", "## Invalid Fields", ""])
    lines.extend(f"- `{item}`" for item in result["invalid_fields"] or ["none"])
    lines.extend(["", "## Missing Outputs", ""])
    lines.extend(f"- `{item}`" for item in result["missing_outputs"] or ["none"])
    lines.extend(["", "## Missing Caveat Markers", ""])
    lines.extend(f"- `{item}`" for item in result["missing_caveats"] or ["none"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Phase 11.8C PennyShaped diagnostic adapter fixture."
    )
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = validate_fixture(args.fixture)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)
    print(f"PHASE=11.8C")
    print(f"STATUS={result['status']}")
    print(f"FIXTURE={args.fixture}")
    return 0 if result["status"] in {"PENNY_ADAPTER_SPEC_VALID", "PENNY_ADAPTER_SPEC_PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
