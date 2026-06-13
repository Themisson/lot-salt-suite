import json
import sys
from pathlib import Path

from tools.decide_elastic_sigmatheta_upgrade_readiness import (
    READY_STATUS,
    SOURCE,
    build_decision,
    main,
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/decide_elastic_sigmatheta_upgrade_readiness.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "axisymmetric elastic sigma-theta upgrade" in capsys.readouterr().out


def test_ready_for_diagnostic_use() -> None:
    decision = build_decision()
    assert decision["readiness_status"] == READY_STATUS
    assert decision["source"] == SOURCE
    assert decision["ready_for_diagnostic_use"] is True


def test_physical_and_runtime_gates_remain_closed() -> None:
    decision = build_decision()
    assert decision["ready_for_controlled_physical_comparison"] is False
    assert decision["ready_for_physical_dispatch"] is False
    assert decision["physically_validated"] is False
    assert decision["legacy_equivalent"] is False
    assert decision["runtime_dispatch_enabled"] is False
    assert decision["buz29_execution_allowed"] is False
    assert decision["pkn_behavior_change_allowed"] is False
    assert decision["penny_shaped_runtime_enabled"] is False


def test_kirsch_remains_blocked() -> None:
    decision = build_decision()
    assert decision["kirsch_full_blocked"] is True
    assert "sigma_H" in decision["kirsch_blocking_fields"]
    assert "sigma_h" in decision["kirsch_blocking_fields"]
    assert "azimuth_angle_rad" in decision["kirsch_blocking_fields"]


def test_partial_when_source_or_analytic_gate_missing() -> None:
    assert build_decision(analytic_valid=False)["readiness_status"] != READY_STATUS
    assert build_decision(source_implemented=False)["readiness_status"] != READY_STATUS


def test_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/decide_elastic_sigmatheta_upgrade_readiness.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["readiness_status"] == READY_STATUS
    assert payload["source"] == SOURCE
    assert SOURCE in output_md.read_text(encoding="utf-8")
