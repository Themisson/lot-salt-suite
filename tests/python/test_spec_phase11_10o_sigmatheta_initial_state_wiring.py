from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.spec_phase11_10o_sigmatheta_initial_state_wiring import (  # noqa: E402
    NEXT_PHASE,
    PREFERRED_SOURCE,
    SPECIFIED,
    build_parser,
    build_spec,
    main,
    write_markdown,
)


def _field_names() -> list[str]:
    return [field["field"] for field in build_spec()["required_fields"]]


def test_help_mentions_initial_state_wiring() -> None:
    help_text = build_parser().format_help()
    assert "sigma-theta initial-state wiring" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "spec.json"
    assert main(["--output-json", str(output_json)]) == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10O"
    assert data["wiring_spec_status"] == SPECIFIED


def test_generates_markdown(tmp_path: Path) -> None:
    output_md = tmp_path / "spec.md"
    write_markdown(build_spec(), output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Sigma-Theta Initial-State Wiring Spec" in text
    assert "FRACTURE_GATE_BLOCKED_UNTIL_SIGMATHETA_INITIALIZED" in text


def test_wiring_spec_status() -> None:
    assert build_spec()["wiring_spec_status"] == SPECIFIED


def test_preferred_source_is_elastic_initial_wellbore_state() -> None:
    assert build_spec()["preferred_source"] == PREFERRED_SOURCE
    assert PREFERRED_SOURCE == "ELASTIC_INITIAL_WELLBORE_STATE"


def test_required_fields_include_initial_sigma_theta() -> None:
    assert "sigma_theta_initial_compression_positive_Pa" in _field_names()


def test_required_fields_include_sigma_theta_initialized() -> None:
    assert "sigma_theta_initialized" in _field_names()


def test_gate_rules_block_uninitialized_sigma_theta() -> None:
    rules = build_spec()["gate_rules"]
    assert any(
        rule["status"] == "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"
        and "sigma_theta_initialized is false" in rule["rule"]
        for rule in rules
    )


def test_pressure_sigmatheta_compatibility_present() -> None:
    compatibility = build_spec()["pressure_sigmatheta_compatibility"]
    assert compatibility
    assert any(
        row["pressure_semantics"] == "WELLBORE_PRESSURE_ABSOLUTE"
        and row["sigma_theta_reference_frame"] == "TOTAL_STRESS"
        for row in compatibility
    )


def test_dispatch_allowed_next_false() -> None:
    assert build_spec()["dispatch_allowed_next"] is False


def test_runtime_execution_allowed_next_false() -> None:
    assert build_spec()["runtime_execution_allowed_next"] is False


def test_implementation_allowed_next_true() -> None:
    assert build_spec()["implementation_allowed_next"] is True


def test_recommended_next_phase_is_guard_implementation() -> None:
    assert build_spec()["recommended_next_phase"] == NEXT_PHASE
    assert NEXT_PHASE == "PHASE11_10P_IMPLEMENT_SIGMATHETA_INITIAL_STATE_WIRING_GUARD"
