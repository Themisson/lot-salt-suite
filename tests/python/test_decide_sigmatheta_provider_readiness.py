from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.decide_sigmatheta_provider_readiness import (
    NEXT_PHASE,
    READINESS_STATUS,
    build_decision,
    main,
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/decide_sigmatheta_provider_readiness.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "PostDrillingSigmaThetaProvider" in capsys.readouterr().out


def test_readiness_status() -> None:
    decision = build_decision()
    assert decision["readiness_status"] == READINESS_STATUS
    assert decision["ready_for_diagnostic_runtime_use"] is True


def test_physical_dispatch_remains_blocked() -> None:
    decision = build_decision()
    assert decision["ready_for_physical_dispatch"] is False
    assert decision["runtime_dispatch_enabled"] is False


def test_real_source_extension_is_allowed_next() -> None:
    decision = build_decision()
    assert decision["ready_for_real_source_extension"] is True
    assert decision["recommended_next_phase"] == NEXT_PHASE


def test_buz29_and_penny_runtime_remain_blocked() -> None:
    decision = build_decision()
    assert decision["buz29_execution_allowed"] is False
    assert decision["penny_shaped_runtime_enabled"] is False


def test_pkn_behavior_is_not_changed() -> None:
    decision = build_decision()
    assert decision["pkn_behavior_changed"] is False


def test_evidence_includes_master_phases() -> None:
    decision = build_decision()
    phases = {item["phase"] for item in decision["evidence"]}
    assert {"master-A", "master-B", "master-C", "master-D", "master-E"} <= phases


def test_remaining_blockers_include_physical_source() -> None:
    decision = build_decision()
    assert "NO_PHYSICAL_SIGMATHETA_RUNTIME_SOURCE_CONSUMED_YET" in decision[
        "remaining_blockers"
    ]


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "readiness.json"
    output_md = tmp_path / "readiness.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/decide_sigmatheta_provider_readiness.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["readiness_status"] == READINESS_STATUS
    assert READINESS_STATUS in output_md.read_text(encoding="utf-8")

