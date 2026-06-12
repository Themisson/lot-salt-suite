from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.decide_phase11_10i_unified_fracture_model_selection import (  # noqa: E402
    DECISION,
    NEXT_PHASE,
    build_decision,
    build_parser,
    main,
    write_markdown,
)


def test_help_mentions_unified_fracture_model_selection() -> None:
    help_text = build_parser().format_help()
    assert "unified fracture-model selection" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "decision.json"
    exit_code = main(["--output-json", str(output_json)])

    assert exit_code == 0
    result = json.loads(output_json.read_text(encoding="utf-8"))
    assert result["phase"] == "11.10I"
    assert result["decision"] == DECISION


def test_generates_markdown(tmp_path: Path) -> None:
    result = build_decision()
    output_md = tmp_path / "decision.md"
    write_markdown(result, output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Unified Fracture-Model Selection" in text
    assert "PKN_DEFAULT_FRACTURE_MODEL" in text
    assert "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY" in text


def test_decision_is_unified_runtime_selected() -> None:
    result = build_decision()
    assert result["decision"] == "UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED"
    assert "UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED" in result["required_classifications"]


def test_default_fracture_model_is_pkn() -> None:
    result = build_decision()
    assert result["default_fracture_model"] == "PKN"
    assert result["missing_fracture_model_behavior"] == "DEFAULT_TO_PKN"
    assert "PKN_DEFAULT_FRACTURE_MODEL" in result["required_classifications"]


def test_supported_models_are_pkn_and_penny_shaped() -> None:
    result = build_decision()
    assert result["supported_fracture_models"] == ["PKN", "PENNY_SHAPED"]
    assert "PKN" in result["supported_fracture_models"]
    assert "PENNY_SHAPED" in result["supported_fracture_models"]


def test_penny_shaped_is_explicit_opt_in_only() -> None:
    result = build_decision()
    assert result["explicit_opt_in_models"] == ["PENNY_SHAPED"]
    assert "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY" in result["required_classifications"]
    assert result["penny_shaped_runtime_status"] == "DIAGNOSTIC_ONLY_NOT_PHYSICALLY_VALIDATED"


def test_blocked_models_include_kgd_and_radial() -> None:
    result = build_decision()
    assert "KGD" in result["blocked_fracture_models"]
    assert "KGD_CIRCULAR" in result["blocked_fracture_models"]
    assert "RADIAL" in result["blocked_fracture_models"]
    assert "UNSUPPORTED_FRACTURE_MODELS_BLOCKED" in result["required_classifications"]


def test_selection_field_and_initiation_gate() -> None:
    result = build_decision()
    assert result["selection_field"] == "lot.fracture.fracture_model"
    assert result["fracture_initiation_gate_required"] is True
    assert "wellbore_pressure_Pa" in result["fracture_initiation_gate_fields"]
    assert "sigma_theta_compression_positive_Pa" in result["fracture_initiation_gate_fields"]


def test_sigma_theta_sign_convention_is_required() -> None:
    result = build_decision()
    assert result["criterion_requires_sign_convention"] is True
    assert "compression-positive" in result["sigma_theta_sign_convention"]


def test_no_runtime_or_parser_schema_change_allowed_now() -> None:
    result = build_decision()
    assert result["runtime_implementation_allowed_now"] is False
    assert result["parser_schema_change_allowed_now"] is False
    assert result["buz29_penny_execution_allowed_now"] is False
    assert result["lot_pkn_behavior_change_allowed_now"] is False


def test_recommended_next_phase() -> None:
    result = build_decision()
    assert result["recommended_next_phase"] == NEXT_PHASE
