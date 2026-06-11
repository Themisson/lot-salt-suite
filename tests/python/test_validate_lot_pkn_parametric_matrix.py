import json

import pytest

from tools import validate_lot_pkn_parametric_matrix as validator


def write_v1(path):
    case = "cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml"
    path.write_text(
        "matrix_id: v1_fixture\n"
        "scenarios:\n"
        f"  - id: s0\n    case: {case}\n"
        f"  - id: s1\n    case: {case}\n",
        encoding="utf-8",
    )


def write_v2(path, base_case="cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml"):
    path.write_text(
        "matrix_id: v2_fixture\n"
        "schema_version: 2\n"
        f"base_case: {base_case}\n"
        "scenarios:\n"
        "  - id: s0\n"
        "    overrides:\n"
        "      lot.fracture.balance.sink_timing: next_step\n"
        "  - id: s1\n"
        "    overrides:\n"
        "      lot.fracture.balance.sink_timing: same_step\n",
        encoding="utf-8",
    )


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        validator.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "strict" in capsys.readouterr().out


def test_valid_v1_matrix(tmp_path):
    matrix = tmp_path / "v1.yaml"
    write_v1(matrix)

    payload = validator.validate_matrix(matrix)

    assert payload["status"] == "MATRIX_V1_VALID"
    assert payload["schema_version"] == 1


def test_valid_v2_matrix(tmp_path):
    matrix = tmp_path / "v2.yaml"
    write_v2(matrix)

    payload = validator.validate_matrix(matrix)

    assert payload["status"] == "MATRIX_V2_VALID"
    assert payload["scenario_count"] == 2


def test_missing_base_case_is_rejected(tmp_path):
    matrix = tmp_path / "v2.yaml"
    write_v2(matrix, base_case="missing.yaml")

    payload = validator.validate_matrix(matrix)

    assert payload["status"] == "MATRIX_MISSING_BASE_CASE"
    assert payload["valid"] is False


def test_missing_scenario_case_is_rejected_for_v1(tmp_path):
    matrix = tmp_path / "bad.yaml"
    matrix.write_text("matrix_id: bad\nscenarios:\n  - id: s0\n", encoding="utf-8")

    payload = validator.validate_matrix(matrix)

    assert payload["status"] == "MATRIX_MISSING_SCENARIO_CASE"


def test_duplicate_ids_are_rejected(tmp_path):
    matrix = tmp_path / "dup.yaml"
    case = "cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml"
    matrix.write_text(
        "matrix_id: dup\n"
        "scenarios:\n"
        f"  - id: s0\n    case: {case}\n"
        f"  - id: s0\n    case: {case}\n",
        encoding="utf-8",
    )

    payload = validator.validate_matrix(matrix)

    assert payload["status"] == "MATRIX_DUPLICATE_SCENARIO_ID"


def test_unsupported_version_is_rejected(tmp_path):
    matrix = tmp_path / "bad_version.yaml"
    matrix.write_text("matrix_id: bad\nschema_version: 99\nscenarios: []\n", encoding="utf-8")

    payload = validator.validate_matrix(matrix)

    assert payload["status"] == "MATRIX_UNSUPPORTED_VERSION"


def test_json_output(capsys, tmp_path):
    matrix = tmp_path / "v1.yaml"
    write_v1(matrix)

    exit_code = validator.main(["--matrix", str(matrix), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "MATRIX_V1_VALID"
