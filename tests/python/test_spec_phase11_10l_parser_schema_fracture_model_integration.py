from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.spec_phase11_10l_parser_schema_fracture_model_integration import (  # noqa: E402
    SPECIFIED,
    build_parser,
    build_spec,
    main,
    write_markdown,
)


def test_help_mentions_parser_schema_integration() -> None:
    help_text = build_parser().format_help()
    assert "parser/schema integration" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "spec.json"
    assert main(["--output-json", str(output_json)]) == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10L"
    assert data["integration_spec_status"] == SPECIFIED


def test_generates_markdown(tmp_path: Path) -> None:
    output_md = tmp_path / "spec.md"
    write_markdown(build_spec(), output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Parser/Schema Integration Spec" in text
    assert "FRACTURE_MODEL_FIELD_LOT_FRACTURE_FRACTURE_MODEL" in text


def test_integration_spec_status() -> None:
    assert build_spec()["integration_spec_status"] == SPECIFIED


def test_field_is_lot_fracture_fracture_model() -> None:
    assert build_spec()["field"] == "lot.fracture.fracture_model"


def test_default_fracture_model_is_pkn() -> None:
    assert build_spec()["default_fracture_model"] == "PKN"


def test_missing_field_behavior_defaults_to_pkn() -> None:
    assert build_spec()["missing_field_behavior"] == "DEFAULT_TO_PKN"


def test_explicit_empty_behavior_is_error() -> None:
    assert (
        build_spec()["explicit_empty_behavior"]
        == "ERROR_EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED"
    )


def test_unsupported_model_behavior_is_error() -> None:
    assert build_spec()["unsupported_model_behavior"] == "ERROR_UNSUPPORTED_FRACTURE_MODEL"


def test_allowed_canonical_values_include_pkn_and_penny_shaped() -> None:
    values = build_spec()["allowed_canonical_values"]
    assert "PKN" in values
    assert "PENNY_SHAPED" in values


def test_schema_policy_present() -> None:
    assert build_spec()["schema_policy"] == "SCHEMA_STRICT_CANONICAL_ONLY"


def test_parser_integration_allowed_next() -> None:
    assert build_spec()["parser_integration_allowed_next"] is True


def test_schema_integration_allowed_next() -> None:
    assert build_spec()["schema_integration_allowed_next"] is True


def test_runtime_execution_allowed_next_false() -> None:
    assert build_spec()["runtime_execution_allowed_next"] is False


def test_buz29_execution_allowed_next_false() -> None:
    assert build_spec()["buz29_execution_allowed_next"] is False


def test_lot_pkn_behavior_change_allowed_false() -> None:
    assert build_spec()["lot_pkn_behavior_change_allowed"] is False
