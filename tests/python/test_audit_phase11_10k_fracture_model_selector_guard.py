from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.audit_phase11_10k_fracture_model_selector_guard import (  # noqa: E402
    IMPLEMENTED,
    build_audit,
    build_parser,
    main,
    write_markdown,
)


def test_help_mentions_fracture_model_selector_guard() -> None:
    help_text = build_parser().format_help()
    assert "fracture_model selector guard" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "audit.json"
    assert main(["--output-json", str(output_json)]) == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10K"
    assert data["implementation_status"] == IMPLEMENTED


def test_generates_markdown(tmp_path: Path) -> None:
    output_md = tmp_path / "audit.md"
    write_markdown(build_audit(), output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Fracture-Model Selector Guard Audit" in text
    assert "FRACTURE_MODEL_SELECTOR_GUARD_IMPLEMENTED" in text


def test_implementation_status_is_implemented() -> None:
    assert build_audit()["implementation_status"] == IMPLEMENTED


def test_default_fracture_model_is_pkn() -> None:
    assert build_audit()["default_fracture_model"] == "PKN"


def test_missing_field_behavior_defaults_to_pkn() -> None:
    assert build_audit()["missing_field_behavior"] == "DEFAULT_TO_PKN"


def test_explicit_empty_behavior_is_error() -> None:
    assert (
        build_audit()["explicit_empty_behavior"]
        == "ERROR_EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED"
    )


def test_supported_models_include_pkn_and_penny_shaped() -> None:
    supported = build_audit()["supported_models"]
    assert "PKN" in supported
    assert "PENNY_SHAPED" in supported


def test_blocked_models_include_kgd() -> None:
    assert "KGD" in build_audit()["blocked_models"]


def test_parser_integrated_is_false() -> None:
    assert build_audit()["parser_integrated"] is False


def test_schema_integrated_is_false() -> None:
    assert build_audit()["schema_integrated"] is False


def test_runtime_integrated_is_false() -> None:
    assert build_audit()["runtime_integrated"] is False


def test_buz29_executed_is_false() -> None:
    assert build_audit()["buz29_executed"] is False


def test_lot_pkn_behavior_changed_is_false() -> None:
    assert build_audit()["lot_pkn_behavior_changed"] is False
