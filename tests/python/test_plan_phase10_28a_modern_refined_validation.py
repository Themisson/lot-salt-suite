from __future__ import annotations

import sys

import pytest

from tools import plan_phase10_28a_modern_refined_validation as plan


def test_help(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["plan_phase10_28a_modern_refined_validation.py", "--help"],
    )
    with pytest.raises(SystemExit) as exc:
        plan.parse_args()
    assert exc.value.code == 0
    assert "Plan Phase 10.28A" in capsys.readouterr().out


def test_summary_contains_required_markers() -> None:
    output = "\n".join(plan.build_summary_lines())
    assert "PHASE=10.28A" in output
    assert "MODE=MODERN_REFINED_VALIDATION_PACKAGE" in output
    assert "LEGACY_EQUIVALENCE=SEPARATE_TRACK" in output
    assert "BASE_CASE=BUZ67D_MODERN_REFINED" in output
    assert "NEXT_GATE=ADDITIONAL_WELLS_OR_SENSITIVITY_MATRIX" in output
    assert "PROTECTED_SCOPE_UNCHANGED=true" in output


def test_summary_is_deterministic() -> None:
    assert plan.build_summary_lines() == plan.build_summary_lines()


def test_main_prints_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["plan_phase10_28a_modern_refined_validation.py"])
    assert plan.main() == 0
    output = capsys.readouterr().out
    assert "PHASE=10.28A" in output
    assert "PROTECTED_SCOPE_UNCHANGED=true" in output
