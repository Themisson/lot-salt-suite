from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.spec_phase11_10q_fracture_gate_dispatch_with_sigmatheta_guard import (  # noqa: E402
    NEXT_PHASE,
    SPECIFIED,
    build_parser,
    build_spec,
    main,
    write_markdown,
)


def test_help_mentions_fracture_gate_dispatch() -> None:
    help_text = build_parser().format_help()
    assert "fracture gate dispatch" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "spec.json"
    assert main(["--output-json", str(output_json)]) == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10Q"
    assert data["dispatch_spec_status"] == SPECIFIED


def test_generates_markdown(tmp_path: Path) -> None:
    output_md = tmp_path / "spec.md"
    write_markdown(build_spec(), output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Fracture Gate Dispatch with Sigma-Theta Guard Spec" in text
    assert "FRACTURE_GATE_BLOCKED_BY_SIGMATHETA_GUARD" in text


def test_dispatch_spec_status_present() -> None:
    assert build_spec()["dispatch_spec_status"] == SPECIFIED


def test_sigmatheta_guard_required_true() -> None:
    assert build_spec()["sigmatheta_guard_required"] is True


def test_fracture_model_selector_required_true() -> None:
    assert build_spec()["fracture_model_selector_required"] is True


def test_dispatch_allowed_next_false() -> None:
    assert build_spec()["dispatch_allowed_next"] is False


def test_runtime_execution_allowed_next_false() -> None:
    assert build_spec()["runtime_execution_allowed_next"] is False


def test_buz29_execution_allowed_next_false() -> None:
    assert build_spec()["buz29_execution_allowed_next"] is False


def test_requires_pressure_sigmatheta_criterion_spec_true() -> None:
    assert build_spec()["requires_pressure_sigmatheta_criterion_spec"] is True


def test_requires_sign_convention_resolution_true() -> None:
    assert build_spec()["requires_sign_convention_resolution"] is True


def test_gate_states_present() -> None:
    states = [row["state"] for row in build_spec()["gate_states"]]
    assert "FRACTURE_GATE_BLOCKED_BY_SIGMATHETA_GUARD" in states
    assert "FRACTURE_GATE_READY_FOR_CRITERION_EVALUATION" in states


def test_required_fields_present() -> None:
    fields = build_spec()["required_fields"]
    assert "selected_fracture_model" in fields
    assert "sigma_theta_guard_status" in fields


def test_blocking_rules_present() -> None:
    statuses = [row["status"] for row in build_spec()["blocking_rules"]]
    assert "SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH" in statuses
    assert "PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED" in statuses


def test_recommended_next_phase_is_pressure_sigmatheta_criterion_spec() -> None:
    assert build_spec()["recommended_next_phase"] == NEXT_PHASE
    assert NEXT_PHASE == "PHASE11_10R_SPECIFY_PRESSURE_SIGMATHETA_FRACTURE_CRITERION"
