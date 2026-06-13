from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.diagnose_elastic_sigmatheta_upgrade_fields import (
    RECOMMENDED_PATH,
    STATUS,
    diagnose,
    main,
)


def test_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["tools/diagnose_elastic_sigmatheta_upgrade_fields.py", "--help"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    assert "elastic sigma-theta upgrade" in capsys.readouterr().out


def test_field_diagnosis_selects_axisymmetric_path() -> None:
    report = diagnose()
    assert report["diagnosis_status"] == STATUS
    assert report["has_kirsch_required_fields"] is False
    assert report["has_axisymmetric_required_fields"] is True
    assert report["has_simplified_required_fields"] is True
    assert report["recommended_formula_path"] == RECOMMENDED_PATH
    assert report["implementation_allowed_next"] is True


def test_safety_flags_remain_closed() -> None:
    report = diagnose()
    assert report["runtime_dispatch_enabled"] is False
    assert report["buz29_execution_allowed"] is False
    assert report["pkn_behavior_change_allowed"] is False
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False


def test_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    output_json = tmp_path / "diagnosis.json"
    output_md = tmp_path / "diagnosis.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/diagnose_elastic_sigmatheta_upgrade_fields.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
    )
    assert main() == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["diagnosis_status"] == STATUS
    assert data["recommended_formula_path"] == RECOMMENDED_PATH
    assert "AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE" in output_md.read_text(
        encoding="utf-8"
    )
