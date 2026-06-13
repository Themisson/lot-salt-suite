from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.decide_elastic_sigmatheta_upgrade_formula import (
    SELECTED_FORMULA,
    STATUS,
    decide,
    main,
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/decide_elastic_sigmatheta_upgrade_formula.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "elastic sigma-theta upgrade formula" in capsys.readouterr().out


def test_selects_axisymmetric_formula() -> None:
    report = decide()
    assert report["formula_decision_status"] == STATUS
    assert report["selected_formula"] == SELECTED_FORMULA
    assert report["implementation_allowed_next"] is True


def test_safety_flags_remain_closed() -> None:
    report = decide()
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False
    assert report["runtime_dispatch_enabled"] is False
    assert report["buz29_execution_allowed"] is False
    assert report["pkn_behavior_change_allowed"] is False
    assert report["penny_shaped_runtime_enabled"] is False


def test_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/decide_elastic_sigmatheta_upgrade_formula.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["formula_decision_status"] == STATUS
    assert data["selected_formula"] == SELECTED_FORMULA
    assert "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE" in output_md.read_text(
        encoding="utf-8"
    )
