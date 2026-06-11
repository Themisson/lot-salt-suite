from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools import plan_phase10_27c_next_steps as plan


def run_main(monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    monkeypatch.setattr(
        sys,
        "argv",
        ["plan_phase10_27c_next_steps.py", *args],
    )
    return plan.main()


def test_help(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["plan_phase10_27c_next_steps.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        plan.parse_args()
    assert exc.value.code == 0
    assert "Plan Phase 10.27C" in capsys.readouterr().out


def test_generates_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"
    assert run_main(monkeypatch, "--output-json", str(output_json), "--output-md", str(output_md)) == 0

    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["status"] == "POST_10_27_ROADMAP_RECORDED"
    assert data["current_recommended_next_phase"] == "10.28A"


def test_generates_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"
    assert run_main(monkeypatch, "--output-json", str(output_json), "--output-md", str(output_md)) == 0

    text = output_md.read_text(encoding="utf-8")
    assert "# Post-10.27 roadmap" in text
    assert "NEXT_PHASE_MODERN_REFINED_VALIDATION_OR_SENSITIVITY" in text


def test_contains_phase_10_28a(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"
    run_main(monkeypatch, "--output-json", str(output_json), "--output-md", str(output_md))
    data = json.loads(output_json.read_text(encoding="utf-8"))

    phases = {item["phase"]: item for item in data["planned_phases"]}
    assert "10.28A" in phases
    assert phases["10.28A"]["route"] == "modern-refined"


def test_contains_phase_10_29a(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"
    run_main(monkeypatch, "--output-json", str(output_json), "--output-md", str(output_md))
    data = json.loads(output_json.read_text(encoding="utf-8"))

    phases = {item["phase"]: item for item in data["planned_phases"]}
    assert "10.29A" in phases
    assert phases["10.29A"]["route"] == "legacy-equivalence"


def test_contains_phase_10_30a(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"
    run_main(monkeypatch, "--output-json", str(output_json), "--output-md", str(output_md))
    data = json.loads(output_json.read_text(encoding="utf-8"))

    phases = {item["phase"]: item for item in data["planned_phases"]}
    assert "10.30A" in phases
    assert phases["10.30A"]["route"] == "salt-runtime"


def test_next_phase_is_modern_refined_validation_or_sensitivity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_json = tmp_path / "roadmap.json"
    output_md = tmp_path / "roadmap.md"
    run_main(monkeypatch, "--output-json", str(output_json), "--output-md", str(output_md))
    data = json.loads(output_json.read_text(encoding="utf-8"))

    assert (
        data["current_recommended_next_phase_classification"]
        == "NEXT_PHASE_MODERN_REFINED_VALIDATION_OR_SENSITIVITY"
    )
    assert data["current_recommended_next_phase"] == "10.28A"
