#!/usr/bin/env python3
"""Validate the Phase 11.7C selected non-PKN YAML/IO specification fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import yaml


PHASE = "11.7C"
STATUS_VALID = "SELECTED_MODEL_YAML_SPEC_VALID"
STATUS_PARTIAL = "SELECTED_MODEL_YAML_SPEC_PARTIAL"
STATUS_INVALID = "SELECTED_MODEL_YAML_SPEC_INVALID"
STATUS_INCONCLUSIVE = "SELECTED_MODEL_YAML_SPEC_INCONCLUSIVE"
SELECTED_TRACK = "PENNY_SHAPED"
MODEL_TYPE = "penny_shaped"
SCHEMA_STATUS = "SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA"
NEXT_PHASE = "PHASE11_8A_MINIMAL_SELECTED_NON_PKN_MODEL"

REQUIRED_OUTPUTS = {
    "opening_m",
    "radius_m",
    "pressure_factor",
    "fracture_volume_proxy_m3",
}

REQUIRED_VALUE_UNIT_PATHS = {
    "fracture_model.elasticity.young_modulus": "Pa",
    "fracture_model.elasticity.poisson_ratio": "dimensionless",
    "fracture_model.fluid.viscosity": "Pa_min",
    "fracture_model.injection.flow_rate": "m3_min",
    "fracture_model.initiation.elapsed_since_opening": "min",
    "fracture_model.initiation.wellbore_pressure": "Pa",
    "fracture_model.initiation.sigma_theta_compression_positive": "Pa",
}


def _get_path(data: dict, dotted_path: str):
    current = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def load_yaml(path: Path) -> dict:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("YAML root must be a mapping")
    return loaded


def validate_spec(data: dict) -> dict:
    missing: list[str] = []
    mismatches: list[str] = []

    if data.get("selected_track") != SELECTED_TRACK:
        mismatches.append("selected_track")

    model = data.get("fracture_model")
    if not isinstance(model, dict):
        missing.append("fracture_model")
        model = {}

    if model.get("type") != MODEL_TYPE:
        mismatches.append("fracture_model.type")
    if model.get("status") != SCHEMA_STATUS:
        mismatches.append("fracture_model.status")

    for dotted_path, expected_unit in REQUIRED_VALUE_UNIT_PATHS.items():
        node = _get_path(data, dotted_path)
        if not isinstance(node, dict):
            missing.append(dotted_path)
            continue
        if "value" not in node:
            missing.append(f"{dotted_path}.value")
        if node.get("unit") != expected_unit:
            mismatches.append(f"{dotted_path}.unit")

    volume_multiplier = _get_path(data, "fracture_model.legacy_options.volume_multiplier")
    if volume_multiplier is None:
        missing.append("fracture_model.legacy_options.volume_multiplier")

    outputs = set(model.get("expected_outputs", []))
    missing_outputs = sorted(REQUIRED_OUTPUTS - outputs)
    missing.extend(f"fracture_model.expected_outputs.{item}" for item in missing_outputs)

    if not missing and not mismatches:
        status = STATUS_VALID
    elif missing and len(missing) >= len(REQUIRED_VALUE_UNIT_PATHS):
        status = STATUS_INVALID
    elif missing or mismatches:
        status = STATUS_PARTIAL
    else:
        status = STATUS_INCONCLUSIVE

    return {
        "phase": PHASE,
        "status": status,
        "selected_track": data.get("selected_track"),
        "model_type": model.get("type"),
        "schema_status": model.get("status"),
        "missing": missing,
        "mismatches": mismatches,
        "required_outputs": sorted(REQUIRED_OUTPUTS),
        "recommended_next_phase": NEXT_PHASE,
        "runtime_schema_changed": False,
        "physical_validation": False,
        "legacy_equivalence": False,
    }


def write_markdown(path: Path, result: dict) -> None:
    lines = [
        "# Phase 11.7C selected model YAML/IO spec validation",
        "",
        f"- `phase`: `{result['phase']}`",
        f"- `status`: `{result['status']}`",
        f"- `selected_track`: `{result['selected_track']}`",
        f"- `model_type`: `{result['model_type']}`",
        f"- `schema_status`: `{result['schema_status']}`",
        f"- `recommended_next_phase`: `{result['recommended_next_phase']}`",
        "",
        "This validation covers a versioned specification fixture only. It does not validate a runtime schema, parser path, or physical model.",
        "",
        "## Required outputs",
        "",
    ]
    for item in result["required_outputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Missing fields", ""])
    if result["missing"]:
        lines.extend(f"- `{item}`" for item in result["missing"])
    else:
        lines.append("- none")
    lines.extend(["", "## Mismatches", ""])
    if result["mismatches"]:
        lines.extend(f"- `{item}`" for item in result["mismatches"])
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_spec(load_yaml(args.fixture))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, result)
    print(f"PHASE={result['phase']}")
    print(f"STATUS={result['status']}")
    print(f"SELECTED_TRACK={result['selected_track']}")
    print(f"MODEL_TYPE={result['model_type']}")
    print(f"NEXT_PHASE={result['recommended_next_phase']}")
    return 0 if result["status"] in {STATUS_VALID, STATUS_PARTIAL} else 1


if __name__ == "__main__":
    raise SystemExit(main())
