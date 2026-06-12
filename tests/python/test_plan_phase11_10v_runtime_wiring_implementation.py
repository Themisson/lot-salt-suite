import json
from pathlib import Path

import pytest

from tools import plan_phase11_10v_runtime_wiring_implementation as plan_tool


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        plan_tool.main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "Phase 11.10V" in output
    assert "--output-json" in output
    assert "--output-md" in output


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"
    assert plan_tool.main(["--output-json", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["phase"] == "11.10V"
    assert payload["plan_status"] == "RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "plan.md"
    assert plan_tool.main(["--output-md", str(output)]) == 0

    text = output.read_text(encoding="utf-8")
    assert "Phase 11.10V runtime wiring implementation plan" in text
    assert "PHASE11_10W_IMPLEMENT_FRACTURE_GATE_RUNTIME_WIRING" in text


def test_plan_status_marker() -> None:
    plan = plan_tool.build_plan()
    assert "PHASE11_10V_RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED" in plan["classifications"]
    assert plan["plan_status"] == "RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED"


def test_implementation_allowed_next() -> None:
    assert plan_tool.build_plan()["implementation_allowed_next"] is True


def test_runtime_execution_still_blocked() -> None:
    assert plan_tool.build_plan()["runtime_execution_allowed_next"] is False


def test_buz29_execution_still_blocked() -> None:
    assert plan_tool.build_plan()["buz29_execution_allowed_next"] is False


def test_pkn_behavior_change_not_allowed() -> None:
    assert plan_tool.build_plan()["pkn_behavior_change_allowed"] is False


def test_proposed_files_include_runtime_wiring_component() -> None:
    proposed = plan_tool.build_plan()["proposed_files"]
    assert "include/lot/FractureGateRuntimeWiring.hpp" in proposed
    assert "src/lot/FractureGateRuntimeWiring.cpp" in proposed
    assert "tests/cpp/test_fracture_gate_runtime_wiring.cpp" in proposed


def test_required_test_scenarios_include_all_11_10u_fixtures() -> None:
    scenarios = set(plan_tool.build_plan()["required_test_scenarios"])
    assert scenarios == {
        "missing_model_defaults_pkn_not_reached",
        "explicit_pkn_initiated_dispatch_eligible",
        "explicit_penny_initiated_diagnostic_eligible",
        "sigmatheta_guard_blocks_dispatch",
        "pressure_sigmatheta_criterion_blocks_dispatch",
        "unsupported_kgd_model_blocked",
        "explicit_empty_model_blocked",
    }


def test_recommended_next_phase() -> None:
    assert (
        plan_tool.build_plan()["recommended_next_phase"]
        == "PHASE11_10W_IMPLEMENT_FRACTURE_GATE_RUNTIME_WIRING"
    )
