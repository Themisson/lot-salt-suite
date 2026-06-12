from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.spec_phase11_10j_fracture_model_selector_guard import (  # noqa: E402
    GUARD_SPEC_STATUS,
    NEXT_DECIDE_PARSER,
    NEXT_IMPLEMENT,
    NEXT_RECONCILE_PKN,
    PARTIAL_STATUS,
    BLOCKED_STATUS,
    build_parser,
    build_spec,
    decide_guard,
    main,
    write_markdown,
)


def test_help_mentions_selector_guard() -> None:
    help_text = build_parser().format_help()
    assert "fracture_model selector guard" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "guard.json"
    assert main(["--output-json", str(output_json)]) == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["phase"] == "11.10J"
    assert data["guard_spec_status"] == GUARD_SPEC_STATUS


def test_generates_markdown(tmp_path: Path) -> None:
    output_md = tmp_path / "guard.md"
    write_markdown(build_spec(), output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Fracture-Model Selector Guard" in text
    assert "EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED" in text


def test_default_absent_field_selects_pkn() -> None:
    spec = build_spec()
    assert spec["default_fracture_model"] == "PKN"
    assert spec["missing_field_behavior"] == "DEFAULT_TO_PKN"
    absent = next(item for item in spec["selector_cases"] if item["case"] == "field_absent")
    assert absent["canonical_model"] == "PKN"
    assert absent["error"] is False


def test_explicit_pkn_is_accepted() -> None:
    explicit = next(item for item in build_spec()["selector_cases"] if item["case"] == "explicit_pkn")
    assert explicit["canonical_model"] == "PKN"
    assert explicit["status"] == "EXPLICIT_PKN_ACCEPTED"


def test_explicit_penny_shaped_is_opt_in_only() -> None:
    spec = build_spec()
    assert spec["explicit_opt_in_models"] == ["PENNY_SHAPED"]
    penny = next(item for item in spec["selector_cases"] if item["case"] == "explicit_penny_shaped")
    assert penny["canonical_model"] == "PENNY_SHAPED"
    assert penny["status"] == "PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY"


def test_explicit_empty_is_rejected() -> None:
    spec = build_spec()
    assert spec["explicit_empty_behavior"] == "REJECT_AS_INVALID"
    empty = next(item for item in spec["selector_cases"] if item["case"] == "explicit_empty")
    assert empty["error"] is True
    assert empty["status"] == "EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED"


def test_unsupported_kgd_is_blocked() -> None:
    spec = build_spec()
    assert "KGD" in spec["blocked_models"]
    kgd = next(item for item in spec["selector_cases"] if item["case"] == "unsupported_kgd")
    assert kgd["error"] is True
    assert kgd["status"] == "UNSUPPORTED_FRACTURE_MODEL_REJECTED"


def test_normalization_rules_cover_pkn_aliases() -> None:
    rules = {(item["input"], item["canonical"]) for item in build_spec()["normalization_rules"]}
    assert ("pkn", "PKN") in rules
    assert ("lot-pkn", "PKN") in rules
    assert ("lot_pkn", "PKN") in rules


def test_normalization_rules_cover_penny_aliases() -> None:
    rules = {(item["input"], item["canonical"]) for item in build_spec()["normalization_rules"]}
    assert ("penny", "PENNY_SHAPED") in rules
    assert ("penny-shaped", "PENNY_SHAPED") in rules
    assert ("penny_shaped", "PENNY_SHAPED") in rules


def test_fracture_initiation_gate_required() -> None:
    spec = build_spec()
    assert spec["fracture_initiation_gate_required"] is True
    assert "FRACTURE_INITIATION_GATE_REQUIRED" in spec["required_statuses"]


def test_sigma_theta_sign_convention_required() -> None:
    spec = build_spec()
    assert spec["criterion_requires_sign_convention"] is True
    assert "SIGMATHETA_SIGN_CONVENTION_REQUIRED" in spec["required_statuses"]


def test_no_runtime_or_parser_change_allowed_now() -> None:
    spec = build_spec()
    assert spec["runtime_implementation_allowed_now"] is False
    assert spec["parser_schema_change_allowed_now"] is False
    assert spec["buz29_penny_execution_allowed_now"] is False


def test_decision_all_specified_allows_next_implementation() -> None:
    status, next_phase = decide_guard()
    assert status == GUARD_SPEC_STATUS
    assert next_phase == NEXT_IMPLEMENT


def test_decision_parser_ambiguity_is_partial() -> None:
    status, next_phase = decide_guard(parser_ambiguity=True)
    assert status == PARTIAL_STATUS
    assert next_phase == NEXT_DECIDE_PARSER


def test_decision_missing_pkn_default_is_blocked() -> None:
    status, next_phase = decide_guard(default_specified=False)
    assert status == BLOCKED_STATUS
    assert next_phase == NEXT_RECONCILE_PKN
