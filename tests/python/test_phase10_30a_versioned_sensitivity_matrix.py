from pathlib import Path

import yaml


MATRIX = Path("cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml")


def load_matrix():
    return yaml.safe_load(MATRIX.read_text(encoding="utf-8"))


def test_matrix_yaml_exists():
    assert MATRIX.exists()


def test_matrix_id_and_baseline_are_declared():
    matrix = load_matrix()

    assert matrix["matrix_id"] == "buz67d_modern_refined_cgeom_sensitivity"
    assert matrix["baseline_scenario"] == "cgeom_100_next_step"
    assert matrix["mode"] == "lot-pkn"


def test_all_scenarios_have_id_and_case():
    matrix = load_matrix()

    for scenario in matrix["scenarios"]:
        assert scenario.get("id")
        assert scenario.get("case")


def test_referenced_cases_exist():
    matrix = load_matrix()

    for scenario in matrix["scenarios"]:
        assert Path(scenario["case"]).exists(), scenario["case"]


def test_required_cgeom_scenarios_are_present():
    ids = {scenario["id"] for scenario in load_matrix()["scenarios"]}

    assert "cgeom_075_next_step" in ids
    assert "cgeom_100_same_step" in ids


def test_matrix_includes_expected_factor_set():
    factors = {
        float(scenario["metadata"]["cgeom_factor"])
        for scenario in load_matrix()["scenarios"]
        if scenario.get("metadata", {}).get("sink_timing") == "next_step"
    }

    assert factors == {0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 1.00, 1.25}
