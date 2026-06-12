import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import decide_phase11_11c_runtime_wiring_readiness as tool  # noqa: E402


SCRIPT = Path("tools/decide_phase11_11c_runtime_wiring_readiness.py")


def test_help_contract_is_declared() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11C" in text
    assert "--output-json" in text


def test_decision_status() -> None:
    data = tool.decision()
    assert data["readiness_status"] == "RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC"


def test_pkn_regression_safe_and_output_isolated() -> None:
    data = tool.decision()
    assert data["pkn_regression_safe"] is True
    assert data["diagnostic_output_isolated"] is True


def test_runtime_dispatch_stays_disabled() -> None:
    data = tool.decision()
    assert data["runtime_dispatch_allowed"] is False
    assert data["runtime_physical_dispatch_enabled"] is False


def test_buz29_and_penny_remain_blocked() -> None:
    data = tool.decision()
    assert data["buz29_execution_allowed"] is False
    assert data["penny_runtime_allowed"] is False


def test_recommended_next_phase_is_11_11d() -> None:
    data = tool.decision()
    assert (
        data["recommended_next_phase"]
        == "PHASE11_11D_SPECIFY_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION"
    )


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"

    assert tool.main(["--output-json", str(output_json), "--output-md", str(output_md)]) == 0

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["readiness_status"] == "RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC"
    text = output_md.read_text(encoding="utf-8")
    assert "runtime_dispatch_allowed" in text
