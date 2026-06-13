from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.decide_elastic_sigmatheta_source_readiness import (
    NEXT_PHASE,
    READINESS_STATUS,
    build_decision,
    main,
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/decide_elastic_sigmatheta_source_readiness.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "elastic sigma-theta source" in capsys.readouterr().out


def test_decision_flags() -> None:
    decision = build_decision()
    assert decision["readiness_status"] == READINESS_STATUS
    assert decision["ready_for_diagnostic_semiphysical_use"] is True
    assert decision["ready_for_physical_validation"] is False
    assert decision["ready_for_physical_dispatch"] is False
    assert decision["ready_for_kirsch_upgrade_spec"] is True
    assert decision["formula_verified"] is True
    assert decision["sign_convention_verified"] is True
    assert decision["threshold_behavior_verified"] is True
    assert decision["physically_validated"] is False
    assert decision["legacy_equivalent"] is False
    assert decision["runtime_dispatch_enabled"] is False
    assert decision["buz29_execution_allowed"] is False
    assert decision["pkn_behavior_change_allowed"] is False
    assert decision["recommended_next_phase"] == NEXT_PHASE


def test_classifications_include_required_statuses() -> None:
    decision = build_decision()
    classifications = set(decision["classifications"])
    assert "ELASTIC_SIGMATHETA_SOURCE_READY_FOR_KIRSCH_UPGRADE_SPEC" in classifications
    assert "READY_FOR_KIRSCH_OR_AXISYMMETRIC_UPGRADE_SPEC" in classifications
    assert "RUNTIME_DISPATCH_NOT_ENABLED" in classifications
    assert "BUZ29_EXECUTION_BLOCKED" in classifications
    assert "PKN_BEHAVIOR_NOT_CHANGED" in classifications


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "readiness.json"
    output_md = tmp_path / "readiness.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/decide_elastic_sigmatheta_source_readiness.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["readiness_status"] == READINESS_STATUS
    assert data["ready_for_diagnostic_semiphysical_use"] is True
    assert data["ready_for_physical_validation"] is False
    assert data["ready_for_physical_dispatch"] is False
    assert data["ready_for_kirsch_upgrade_spec"] is True
    assert "ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE" in (
        output_md.read_text(encoding="utf-8")
    )
