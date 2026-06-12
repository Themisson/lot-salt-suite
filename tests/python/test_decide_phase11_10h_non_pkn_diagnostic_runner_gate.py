from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.decide_phase11_10h_non_pkn_diagnostic_runner_gate import (  # noqa: E402
    BLOCKED_BY_INPUTS,
    BLOCKED_BY_SEMANTICS,
    INCONCLUSIVE,
    NEXT_SPEC,
    SPEC_ALLOWED,
    SPEC_PARTIAL,
    build_decision,
    build_parser,
    decide_gate,
    main,
    write_markdown,
)


def test_help_mentions_non_pkn_gate() -> None:
    help_text = build_parser().format_help()
    assert "non-PKN diagnostic runner gate" in help_text
    assert "--output-json" in help_text
    assert "--adapter-header" in help_text


def test_generates_json(tmp_path: Path) -> None:
    output_json = tmp_path / "gate.json"
    exit_code = main(["--output-json", str(output_json)])

    assert exit_code == 0
    result = json.loads(output_json.read_text(encoding="utf-8"))
    assert result["phase"] == "11.10H"
    assert result["decision"] == SPEC_PARTIAL


def test_generates_markdown(tmp_path: Path) -> None:
    result = build_decision(
        {
            "adapter_header": ROOT / "include/lot/PennyShapedDiagnosticAdapter.hpp",
            "adapter_source": ROOT / "src/lot/PennyShapedDiagnosticAdapter.cpp",
            "writer_header": ROOT / "include/lot/PennyShapedDiagnosticWriter.hpp",
            "writer_source": ROOT / "src/lot/PennyShapedDiagnosticWriter.cpp",
            "candidate": ROOT / "cases/validation/non_pkn/buz29_penny_candidate.yaml",
            "adapter_doc": ROOT / "docs/75_buz29_penny_adapter_ready_inputs.md",
            "writer_doc": ROOT / "docs/81_penny_diagnostic_writer_implementation.md",
        }
    )
    output_md = tmp_path / "gate.md"
    write_markdown(result, output_md)
    text = output_md.read_text(encoding="utf-8")
    assert "Non-PKN Diagnostic Runner Gate" in text
    assert "runner_implementation_allowed_now" in text


def test_decision_present_for_repository_state() -> None:
    result = build_decision(
        {
            "adapter_header": ROOT / "include/lot/PennyShapedDiagnosticAdapter.hpp",
            "adapter_source": ROOT / "src/lot/PennyShapedDiagnosticAdapter.cpp",
            "writer_header": ROOT / "include/lot/PennyShapedDiagnosticWriter.hpp",
            "writer_source": ROOT / "src/lot/PennyShapedDiagnosticWriter.cpp",
            "candidate": ROOT / "cases/validation/non_pkn/buz29_penny_candidate.yaml",
            "adapter_doc": ROOT / "docs/75_buz29_penny_adapter_ready_inputs.md",
            "writer_doc": ROOT / "docs/81_penny_diagnostic_writer_implementation.md",
        }
    )
    assert result["decision"] == SPEC_PARTIAL
    assert result["adapter_available"] is True
    assert result["writer_available"] is True
    assert result["adapter_ready"] is False
    assert result["partial_adapter_ready"] is True


def test_runner_and_runtime_remain_disallowed() -> None:
    result = build_decision(
        {
            "adapter_header": ROOT / "include/lot/PennyShapedDiagnosticAdapter.hpp",
            "adapter_source": ROOT / "src/lot/PennyShapedDiagnosticAdapter.cpp",
            "writer_header": ROOT / "include/lot/PennyShapedDiagnosticWriter.hpp",
            "writer_source": ROOT / "src/lot/PennyShapedDiagnosticWriter.cpp",
            "candidate": ROOT / "cases/validation/non_pkn/buz29_penny_candidate.yaml",
            "adapter_doc": ROOT / "docs/75_buz29_penny_adapter_ready_inputs.md",
            "writer_doc": ROOT / "docs/81_penny_diagnostic_writer_implementation.md",
        }
    )
    assert result["runner_implementation_allowed_now"] is False
    assert result["buz29_runtime_execution_allowed"] is False
    assert result["lot_pkn_impact_allowed"] is False
    assert result["recommended_next_phase"] == NEXT_SPEC


def test_case_spec_partial() -> None:
    decision, next_phase = decide_gate(
        adapter_available=True,
        writer_available=True,
        candidate_available=True,
        adapter_ready=False,
        partial_adapter_ready=True,
        semantic_blocker=True,
        missing_inputs=["sigma_theta_compression_positive_Pa"],
    )
    assert decision == SPEC_PARTIAL
    assert next_phase == NEXT_SPEC


def test_case_spec_allowed() -> None:
    decision, next_phase = decide_gate(
        adapter_available=True,
        writer_available=True,
        candidate_available=True,
        adapter_ready=True,
        partial_adapter_ready=False,
        semantic_blocker=False,
        missing_inputs=[],
    )
    assert decision == SPEC_ALLOWED
    assert next_phase == NEXT_SPEC


def test_case_blocked_by_inputs() -> None:
    decision, _next_phase = decide_gate(
        adapter_available=True,
        writer_available=True,
        candidate_available=True,
        adapter_ready=False,
        partial_adapter_ready=False,
        semantic_blocker=False,
        missing_inputs=["young_modulus_Pa"],
    )
    assert decision == BLOCKED_BY_INPUTS


def test_case_blocked_by_semantics() -> None:
    decision, _next_phase = decide_gate(
        adapter_available=True,
        writer_available=True,
        candidate_available=True,
        adapter_ready=False,
        partial_adapter_ready=False,
        semantic_blocker=True,
        missing_inputs=[],
    )
    assert decision == BLOCKED_BY_SEMANTICS


def test_case_inconclusive() -> None:
    decision, _next_phase = decide_gate(
        adapter_available=False,
        writer_available=True,
        candidate_available=True,
        adapter_ready=False,
        partial_adapter_ready=False,
        semantic_blocker=False,
        missing_inputs=[],
    )
    assert decision == INCONCLUSIVE
