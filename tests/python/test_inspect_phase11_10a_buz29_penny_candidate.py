from __future__ import annotations

import json
from pathlib import Path

import yaml

from tools.inspect_phase11_10a_buz29_penny_candidate import (
    AXISYMMETRIC_CAVEAT,
    CLASSIFICATION_BLOCKED,
    CLASSIFICATION_STARTED,
    FUTURE_OUTPUT_REQUIREMENT,
    build_parser,
    inspect_candidate,
    write_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = REPO_ROOT / "cases/validation/non_pkn/buz29_penny_candidate.yaml"


def _candidate_data() -> dict:
    return {
        "case": {
            "id": "buz29_penny_candidate",
            "status": "diagnostic_candidate",
            "active": False,
            "caveat": (
                "Diagnostic candidate only. Not physically validated. "
                "Not legacy equivalent. Not an active simulation case."
            ),
        },
        "source": {
            "legacy_trace": "legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat"
        },
        "track": {"gate": "BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A"},
        "diagnostic_evidence": {
            "pressure_history_status": "PRESSURE_HISTORY_FOUND_CONSUMABLE",
            "opening_time_status": "OPENING_TIME_FOUND_CONSUMABLE",
            "time_points": 131,
            "time_min_min": 0.0,
            "time_max_min": 13.0,
            "opening_time_min": 10.4,
            "available_blocks": ["dP", "dV_leakoff", "V_outflow"],
        },
        "axisymmetric_interpretation": {
            "caveat": AXISYMMETRIC_CAVEAT,
            "future_output_requirement": FUTURE_OUTPUT_REQUIREMENT,
        },
        "adapter_status": {
            "missing_or_deferred": [
                "runtime non-PKN runner",
                "direct sigmaTheta/pw/margin/opened legacy exports",
            ]
        },
        "diagnostics": {
            "physically_validated": False,
            "legacy_equivalent": False,
            "active_simulation_case": False,
        },
    }


def _write_candidate(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "candidate.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_help_mentions_case_argument() -> None:
    help_text = build_parser().format_help()
    assert "BUZ29 PennyShaped diagnostic candidate" in help_text
    assert "--case" in help_text


def test_repository_candidate_starts_partial_diagnostic_route() -> None:
    result = inspect_candidate(CANDIDATE)
    assert result["classification"] == CLASSIFICATION_STARTED
    assert result["route_started"] is True
    assert result["physically_validated"] is False
    assert result["legacy_equivalent"] is False
    assert result["active_simulation_case"] is False
    assert result["axisymmetric_interpretation"] == AXISYMMETRIC_CAVEAT
    assert result["future_output_requirement"] == FUTURE_OUTPUT_REQUIREMENT


def test_valid_candidate_starts_route(tmp_path: Path) -> None:
    result = inspect_candidate(_write_candidate(tmp_path, _candidate_data()))
    assert result["classification"] == CLASSIFICATION_STARTED
    assert result["route_started"] is True
    assert result["blocking_gaps"] == []


def test_missing_caveat_blocks_route(tmp_path: Path) -> None:
    data = _candidate_data()
    data["case"]["caveat"] = "Diagnostic candidate only."
    result = inspect_candidate(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "case.caveat" in result["blocking_gaps"]


def test_active_candidate_blocks_route(tmp_path: Path) -> None:
    data = _candidate_data()
    data["case"]["active"] = True
    result = inspect_candidate(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "case.active" in result["blocking_gaps"]


def test_missing_pressure_history_blocks_route(tmp_path: Path) -> None:
    data = _candidate_data()
    data["diagnostic_evidence"]["pressure_history_status"] = "MISSING"
    result = inspect_candidate(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "diagnostic_evidence.pressure_history_status" in result["blocking_gaps"]


def test_missing_opening_history_blocks_route(tmp_path: Path) -> None:
    data = _candidate_data()
    data["diagnostic_evidence"]["opening_time_status"] = "MISSING"
    result = inspect_candidate(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "diagnostic_evidence.opening_time_status" in result["blocking_gaps"]


def test_missing_axisymmetric_caveat_blocks_route(tmp_path: Path) -> None:
    data = _candidate_data()
    data["axisymmetric_interpretation"]["caveat"] = "MISSING"
    result = inspect_candidate(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "axisymmetric_interpretation.caveat" in result["blocking_gaps"]


def test_missing_future_output_requirement_blocks_route(tmp_path: Path) -> None:
    data = _candidate_data()
    data["axisymmetric_interpretation"]["future_output_requirement"] = "MISSING"
    result = inspect_candidate(_write_candidate(tmp_path, data))
    assert result["classification"] == CLASSIFICATION_BLOCKED
    assert "axisymmetric_interpretation.future_output_requirement" in result["blocking_gaps"]


def test_json_and_markdown_outputs_are_writable(tmp_path: Path) -> None:
    result = inspect_candidate(_write_candidate(tmp_path, _candidate_data()))
    json_path = tmp_path / "inspection.json"
    md_path = tmp_path / "inspection.md"
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, md_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["classification"] == CLASSIFICATION_STARTED
    markdown = md_path.read_text(encoding="utf-8")
    assert "NOT_PHYSICALLY_VALIDATED" in markdown
    assert "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED" in markdown
