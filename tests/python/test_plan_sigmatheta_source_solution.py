import json
import subprocess
import sys
from pathlib import Path

from tools.plan_sigmatheta_source_solution import build_plan


SCRIPT = Path("tools/plan_sigmatheta_source_solution.py")


def test_help() -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--help"], check=True, text=True)


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-json", str(output)],
        check=True,
        text=True,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["solution_plan_status"] == "SIGMATHETA_SOURCE_SOLUTION_PLAN_READY"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "plan.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-md", str(output)],
        check=True,
        text=True,
    )
    assert "PostDrillingSigmaThetaProvider" in output.read_text(encoding="utf-8")


def test_selected_solution_path_is_semi_physical() -> None:
    assert (
        build_plan()["selected_solution_path"]
        == "SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE"
    )


def test_provider_component_selected() -> None:
    assert build_plan()["proposed_component"] == "PostDrillingSigmaThetaProvider"


def test_implementation_allowed_next() -> None:
    assert build_plan()["implementation_allowed_next"] is True


def test_runtime_dispatch_not_allowed_next() -> None:
    assert build_plan()["runtime_dispatch_allowed_next"] is False


def test_buz29_not_allowed_next() -> None:
    assert build_plan()["buz29_execution_allowed_next"] is False


def test_pkn_behavior_change_not_allowed() -> None:
    assert build_plan()["pkn_behavior_change_allowed"] is False


def test_unknown_source_rejected() -> None:
    assert build_plan()["source_policy"]["unknown"] == "rejected"


def test_semantics_are_explicit() -> None:
    semantics = build_plan()["required_result_semantics"]
    assert semantics["state_time"] == "POST_DRILLING_BEFORE_LOT"
    assert semantics["sign_convention"] == "COMPRESSION_POSITIVE"
    assert semantics["reference_frame"] == "WELLBORE_WALL_TOTAL_STRESS"
