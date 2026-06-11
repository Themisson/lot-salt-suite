import json

import pytest
import yaml

from tools import materialize_lot_pkn_parametric_matrix as materializer


FIXTURE = "tests/fixtures/comparison/phase11_2b_parametric_matrix.yaml"


def parse_args(tmp_path, *extra):
    return materializer.build_parser().parse_args(["--matrix", FIXTURE, "--output-dir", str(tmp_path / "out"), *extra])


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        materializer.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "allow-create" in capsys.readouterr().out


def test_basic_materialization_writes_cases_and_manifest(tmp_path):
    manifest = materializer.materialize(parse_args(tmp_path))

    assert manifest["scenario_count"] == 2
    assert (tmp_path / "out" / "cgeom_075.yaml").exists()
    assert (tmp_path / "out" / "materialization_manifest.json").exists()


def test_numeric_and_string_overrides_are_applied(tmp_path):
    materializer.materialize(parse_args(tmp_path))

    cgeom = yaml.safe_load((tmp_path / "out" / "cgeom_075.yaml").read_text(encoding="utf-8"))
    same_step = yaml.safe_load((tmp_path / "out" / "same_step.yaml").read_text(encoding="utf-8"))

    assert cgeom["lot"]["volumetric_balance"]["compliance"]["geometric_compressibility"]["value"] == pytest.approx(1.3928975203957504e-8)
    assert same_step["lot"]["fracture"]["balance"]["sink_timing"] == "same_step"
    assert same_step["metadata"]["scenario_id"] == "same_step"


def test_missing_override_path_fails(tmp_path):
    matrix = tmp_path / "bad.yaml"
    matrix.write_text(
        "matrix_id: bad\n"
        "schema_version: 2\n"
        "base_case: tests/fixtures/comparison/phase11_2b_base_case.yaml\n"
        "scenarios:\n"
        "  - id: bad\n"
        "    overrides:\n"
        "      lot.missing.path: 1\n",
        encoding="utf-8",
    )
    args = materializer.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out")])

    with pytest.raises(KeyError):
        materializer.materialize(args)


def test_allow_create_allows_new_path(tmp_path):
    matrix = tmp_path / "create.yaml"
    matrix.write_text(
        "matrix_id: create\n"
        "schema_version: 2\n"
        "base_case: tests/fixtures/comparison/phase11_2b_base_case.yaml\n"
        "scenarios:\n"
        "  - id: created\n"
        "    overrides:\n"
        "      lot.new_branch.value: 42\n",
        encoding="utf-8",
    )
    args = materializer.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--allow-create"])

    materializer.materialize(args)

    data = yaml.safe_load((tmp_path / "out" / "created.yaml").read_text(encoding="utf-8"))
    assert data["lot"]["new_branch"]["value"] == 42


def test_dry_run_does_not_write_yaml(tmp_path):
    manifest = materializer.materialize(parse_args(tmp_path, "--dry-run"))

    assert manifest["dry_run"] is True
    assert not (tmp_path / "out" / "cgeom_075.yaml").exists()


def test_manifest_records_overrides(tmp_path):
    materializer.materialize(parse_args(tmp_path))

    payload = json.loads((tmp_path / "out" / "materialization_manifest.json").read_text(encoding="utf-8"))
    assert payload["scenarios"][0]["overrides"]
    assert payload["status"] == "PARAMETRIC_CASE_MATERIALIZER_ADDED"


def test_output_inside_cases_requires_explicit_allow(tmp_path):
    args = materializer.build_parser().parse_args(["--matrix", FIXTURE, "--output-dir", "cases/generated"])

    with pytest.raises(ValueError):
        materializer.materialize(args)
