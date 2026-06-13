from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.plan_phase11_11m_sigmatheta_source_completion import build_plan, main


SCRIPT = Path("tools/plan_phase11_11m_sigmatheta_source_completion.py")


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--help"])
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "sigma-theta source completion" in capsys.readouterr().out


def test_plan_status_records_diagnostic_only_path() -> None:
    plan = build_plan()
    assert (
        plan["plan_status"]
        == "LIMITED_GATE_REMAINS_DIAGNOSTIC_SIGMATHETA_SOURCE_PLAN_RECORDED"
    )
    assert plan["limited_gate_status"] == "DIAGNOSTIC_ONLY"


def test_no_implementation_is_performed() -> None:
    plan = build_plan()
    assert plan["implementation_performed"] is False


def test_runtime_dispatch_stays_disabled() -> None:
    plan = build_plan()
    assert plan["runtime_dispatch_enabled"] is False


def test_buz29_execution_stays_blocked() -> None:
    plan = build_plan()
    assert plan["buz29_execution_allowed"] is False


def test_pkn_behavior_is_not_changed() -> None:
    plan = build_plan()
    assert plan["pkn_behavior_changed"] is False


def test_penny_runtime_stays_disabled() -> None:
    plan = build_plan()
    assert plan["penny_shaped_runtime_enabled"] is False


def test_blocking_reasons_include_missing_sigmatheta_sources() -> None:
    plan = build_plan()
    assert "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE" in plan["blocking_reasons"]
    assert "MISSING_RUNTIME_SIGMATHETA_CURRENT_SOURCE" in plan["blocking_reasons"]


def test_completion_steps_include_pressure_and_reference_resolution() -> None:
    plan = build_plan()
    steps = {item["step"] for item in plan["completion_steps"]}
    assert "resolve_pressure_semantics" in steps
    assert "resolve_reference_frame" in steps


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "plan.json"
    output_md = tmp_path / "plan.md"
    monkeypatch.setattr(sys, "argv", [
        str(SCRIPT),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ])
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["recommended_next_phase"] == "PHASE11_11N_IMPLEMENT_OR_CONNECT_SIGMATHETA_SOURCE"
    assert "MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE" in output_md.read_text(
        encoding="utf-8"
    )
