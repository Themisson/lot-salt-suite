import json

from tools.reevaluate_phase11_9f_buz29_penny_readiness import (
    AXISYMMETRIC_CAVEAT,
    GATE_DIAGNOSTIC_SAFE,
    NEXT_PHASE_11_10A,
    READINESS_DIAGNOSTIC_SAFE,
    ReadinessInputs,
    build_parser,
    reevaluate_readiness,
    write_markdown,
)


def test_help_contains_phase_description():
    help_text = build_parser().format_help()
    assert "Reevaluate BUZ29 PennyShaped readiness" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_generates_json_and_markdown(tmp_path):
    result = reevaluate_readiness(ReadinessInputs())
    output_json = tmp_path / "readiness.json"
    output_md = tmp_path / "readiness.md"

    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, output_md)

    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert loaded["updated_readiness"] == READINESS_DIAGNOSTIC_SAFE
    assert loaded["can_start_11_10A"] is True
    assert loaded["gate"] == GATE_DIAGNOSTIC_SAFE
    assert loaded["recommended_next_phase"] == NEXT_PHASE_11_10A
    assert AXISYMMETRIC_CAVEAT in loaded["required_caveats"]
    assert "formulação axissimétrica de 1 rad" in markdown


def test_consumable_pressure_opening_with_adapter_safe_opens_gate():
    result = reevaluate_readiness(ReadinessInputs())
    assert result["updated_readiness"] == READINESS_DIAGNOSTIC_SAFE
    assert result["can_start_11_10A"] is True
    assert result["gate"] == GATE_DIAGNOSTIC_SAFE
    assert result["recommended_next_phase"] == NEXT_PHASE_11_10A
    assert result["buz29_candidate_yaml_created"] is False
    assert result["buz29_simulation_executed"] is False
    assert result["physical_validation"] is False


def test_consumable_pressure_opening_but_adapter_inputs_insufficient_keeps_gate_closed():
    result = reevaluate_readiness(
        ReadinessInputs(adapter_ready_status="ADAPTER_READY_INSUFFICIENT")
    )
    assert result["updated_readiness"] == "BUZ29_PENNY_CANDIDATE_PARTIAL"
    assert result["can_start_11_10A"] is False
    assert result["gate"] == "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
    assert "adapter_ready_inputs" in result["blocking_gaps"]
    assert result["recommended_next_phase"] == "PHASE11_9G_COMPLETE_BUZ29_ADAPTER_READY_INPUTS"


def test_inconclusive_when_pressure_opening_semantics_are_ambiguous():
    result = reevaluate_readiness(ReadinessInputs(severe_semantic_ambiguity=True))
    assert result["updated_readiness"] == "BUZ29_PENNY_CANDIDATE_INCONCLUSIVE"
    assert result["can_start_11_10A"] is False
    assert result["gate"] == "BUZ29_PENNY_INCONCLUSIVE_DO_NOT_START_11_10A"
    assert "pressure_opening_semantics" in result["blocking_gaps"]
    assert result["recommended_next_phase"] == (
        "PHASE11_9G_RESOLVE_BUZ29_PRESSURE_OPENING_SEMANTICS"
    )


def test_blocked_by_penny_math_audit_need():
    result = reevaluate_readiness(ReadinessInputs(penny_math_blocks_diagnostic=True))
    assert result["updated_readiness"] == "BUZ29_PENNY_CANDIDATE_PARTIAL"
    assert result["can_start_11_10A"] is False
    assert result["gate"] == "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
    assert "penny_shaped_math_interpretation" in result["blocking_gaps"]
    assert result["recommended_next_phase"] == "PHASE11_8E_AUDIT_PENNY_SHAPED_MODEL_MATH"


def test_missing_pressure_or_opening_keeps_gate_closed():
    result = reevaluate_readiness(
        ReadinessInputs(
            pressure_history_status="PRESSURE_HISTORY_MISSING",
            opening_time_status="OPENING_TIME_FOUND_CONSUMABLE",
            pressure_history_consumable=False,
            opening_time_consumable=True,
        )
    )
    assert result["updated_readiness"] == "BUZ29_PENNY_CANDIDATE_PARTIAL"
    assert result["can_start_11_10A"] is False
    assert result["gate"] == "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
    assert "pressure_history" in result["blocking_gaps"]


def test_axisymmetric_caveat_does_not_block_diagnostic_safe_route():
    result = reevaluate_readiness(ReadinessInputs())
    assert result["axisymmetric_interpretation"] == AXISYMMETRIC_CAVEAT
    assert AXISYMMETRIC_CAVEAT in result["required_caveats"]
    assert result["can_start_11_10A"] is True
