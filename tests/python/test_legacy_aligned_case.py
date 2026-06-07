from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
PARAMETERS_PATH = ROOT / "tests" / "fixtures" / "comparison" / "buz67d_legacy_parameters.json"
GATE_PATH = ROOT / "tests" / "fixtures" / "comparison" / "level1_readiness_gate.json"
ALIGNED_YAML_PATH = ROOT / "cases" / "validation" / "buz67d_pkn_legacy_aligned.yaml"
MIGRATED_YAML_PATH = ROOT / "cases" / "lot_tese_migrated" / "buz67d_pkn.yaml"

VALID_CLASSIFICATIONS = {
    "CONTROLLED_EQUIVALENT",
    "CONTROLLED_LEGACY_ALIGNED_PARTIAL",
    "BLOCKED_INSUFFICIENT_LEGACY_PARAMETERS",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def assert_unchanged_against_head(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "diff", "--quiet", "--", rel],
        cwd=ROOT,
        check=True,
    )


def test_legacy_parameters_json_exists_and_parseable() -> None:
    assert PARAMETERS_PATH.exists()
    data = load_json(PARAMETERS_PATH)

    assert data["phase"] == "10.14EF"
    assert data["case_id"] == "8-BUZ-67D-PKN"
    assert data["parameters"]


def test_legacy_parameters_has_temporal() -> None:
    data = load_json(PARAMETERS_PATH)

    assert data["parameters"]["temporal"]["total_time_s"]["value"] == 750.0
    assert data["parameters"]["temporal"]["total_time_min"]["value"] == 12.5
    assert data["parameters"]["temporal"]["dt_s"]["value"] == 30.0


def test_legacy_parameters_extraction_status() -> None:
    data = load_json(PARAMETERS_PATH)

    assert data["extraction_status"] in {"EXTRACTED", "PARTIALLY_EXTRACTED"}


def test_case_classification_is_valid() -> None:
    data = load_json(PARAMETERS_PATH)

    assert data["case_classification"] in VALID_CLASSIFICATIONS


def test_aligned_yaml_exists_if_not_blocked() -> None:
    data = load_json(PARAMETERS_PATH)

    if data["case_classification"] == "BLOCKED_INSUFFICIENT_LEGACY_PARAMETERS":
        assert not ALIGNED_YAML_PATH.exists()
    else:
        assert ALIGNED_YAML_PATH.exists()


def test_aligned_yaml_duration_is_750s() -> None:
    if not ALIGNED_YAML_PATH.exists():
        return

    data = load_yaml(ALIGNED_YAML_PATH)

    total_time = data["lot"]["injection"]["schedule"]["total_time"]
    assert total_time["value"] == 12.5
    assert total_time["unit"] == "min"
    assert data["time"]["total_h"] == 0.2083333333
    assert total_time["value"] * 60.0 == 750.0


def test_aligned_yaml_is_different_from_migrated() -> None:
    if not ALIGNED_YAML_PATH.exists():
        return

    assert ALIGNED_YAML_PATH.read_text(encoding="utf-8") != MIGRATED_YAML_PATH.read_text(encoding="utf-8")


def test_original_migrated_case_unchanged() -> None:
    assert_unchanged_against_head(MIGRATED_YAML_PATH)


def test_existing_validation_cases_unchanged() -> None:
    for path in (
        ROOT / "cases" / "validation" / "lot_pkn_minimal.yaml",
        ROOT / "cases" / "validation" / "lot_pkn_with_leakoff.yaml",
    ):
        assert_unchanged_against_head(path)


def test_level1_gate_updated() -> None:
    gate = load_json(GATE_PATH)
    parameters = load_json(PARAMETERS_PATH)

    if parameters["case_classification"] == "BLOCKED_INSUFFICIENT_LEGACY_PARAMETERS":
        assert gate["status"] == "LEVEL1_BLOCKED_INSUFFICIENT_LEGACY_PARAMETERS"
    elif parameters["case_classification"] == "CONTROLLED_EQUIVALENT":
        assert gate["status"] in {
            "LEVEL1_CONTROLLED_EQUIVALENT_CASE_CREATED_RUN_PENDING",
            "LEVEL1_STRUCTURAL_DIAGNOSTIC_COMPLETE",
        }
        assert gate["case_equivalence"]["status"] == "CONTROLLED_EQUIVALENT"
    else:
        assert gate["status"] == "LEVEL1_LEGACY_ALIGNED_PARTIAL_CASE_CREATED_RUN_PENDING"
        assert gate["case_equivalence"]["status"] == "CONTROLLED_LEGACY_ALIGNED_PARTIAL"


def test_level1_still_not_ready() -> None:
    gate = load_json(GATE_PATH)

    assert gate["level1_ready"] is False
    assert gate["physical_validation"] is False
    assert gate["numeric_equivalence"] is False


def test_fallbacks_documented_in_parameters() -> None:
    data = load_json(PARAMETERS_PATH)

    if data["case_classification"] == "CONTROLLED_LEGACY_ALIGNED_PARTIAL":
        statuses: list[str] = []
        for group in data["parameters"].values():
            for parameter in group.values():
                if isinstance(parameter, dict):
                    statuses.append(str(parameter.get("status")))
        assert "INFERRED_FROM_MIGRATED_CASE" in statuses
