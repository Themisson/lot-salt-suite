from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.plan_elastic_sigmatheta_upgrade_implementation import (
    PROPOSED_SOURCE,
    SELECTED_FORMULA,
    STATUS,
    main,
    plan,
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/plan_elastic_sigmatheta_upgrade_implementation.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "elastic sigma-theta upgrade" in capsys.readouterr().out


def test_plan_selects_axisymmetric_source() -> None:
    report = plan()
    assert report["plan_status"] == STATUS
    assert report["selected_formula"] == SELECTED_FORMULA
    assert report["proposed_provider_source"] == PROPOSED_SOURCE
    assert report["implementation_allowed_next"] is True
    assert "far_field_stress_compression_positive_Pa" in report["minimum_fields"]
    assert "wellbore_pressure_Pa" in report["minimum_fields"]


def test_safety_flags_remain_closed() -> None:
    report = plan()
    assert report["runtime_dispatch_enabled"] is False
    assert report["buz29_execution_allowed"] is False
    assert report["pkn_behavior_change_allowed"] is False
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False


def test_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "plan.json"
    output_md = tmp_path / "plan.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/plan_elastic_sigmatheta_upgrade_implementation.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["plan_status"] == STATUS
    assert data["proposed_provider_source"] == PROPOSED_SOURCE
    assert "AXISYMMETRIC_ELASTIC_WELLBORE_STATE" in output_md.read_text(
        encoding="utf-8"
    )
