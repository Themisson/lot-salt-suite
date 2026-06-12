from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools.audit_phase11_11n_sigmatheta_diagnostic_source import build_audit, main


SCRIPT = Path("tools/audit_phase11_11n_sigmatheta_diagnostic_source.py")
FIXTURES = Path("tests/fixtures/comparison/phase11_11n")


def test_help(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit) as exc:
        monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--help"])
        main()
    assert exc.value.code == 0


def test_generates_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "audit.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--fixtures-dir",
            str(FIXTURES),
            "--output-json",
            str(output),
        ],
    )
    assert main() == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "11.11N"


def test_generates_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "audit.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--fixtures-dir",
            str(FIXTURES),
            "--output-md",
            str(output),
        ],
    )
    assert main() == 0
    assert "SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED" in output.read_text(
        encoding="utf-8"
    )


def test_implementation_status_present() -> None:
    audit = build_audit(FIXTURES)
    assert audit["implementation_status"] == "SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED"


def test_source_type_is_explicit_diagnostic_input() -> None:
    audit = build_audit(FIXTURES)
    assert audit["source_type"] == "EXPLICIT_DIAGNOSTIC_INPUT"
    assert audit["synthetic_fixture_source_allowed"] is True


def test_physically_validated_false() -> None:
    assert build_audit(FIXTURES)["physically_validated"] is False


def test_legacy_equivalent_false() -> None:
    assert build_audit(FIXTURES)["legacy_equivalent"] is False


def test_runtime_dispatch_enabled_false() -> None:
    assert build_audit(FIXTURES)["runtime_dispatch_enabled"] is False


def test_buz29_execution_allowed_false() -> None:
    assert build_audit(FIXTURES)["buz29_execution_allowed"] is False


def test_pkn_behavior_changed_false() -> None:
    assert build_audit(FIXTURES)["pkn_behavior_changed"] is False


def test_penny_shaped_runtime_enabled_false() -> None:
    assert build_audit(FIXTURES)["penny_shaped_runtime_enabled"] is False


def test_limited_gate_can_be_fed_diagnostically() -> None:
    assert build_audit(FIXTURES)["limited_gate_can_be_fed_diagnostically"] is True
