import json

from tools import run_lot_pkn_sensitivity_matrix as runner


V2_FIXTURE = "tests/fixtures/comparison/phase11_2b_parametric_matrix.yaml"


def test_runner_still_accepts_v1_matrix(tmp_path):
    matrix = tmp_path / "v1.yaml"
    matrix.write_text(
        "matrix_id: v1\n"
        "scenarios:\n"
        "  - id: s0\n"
        "    case: cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml\n",
        encoding="utf-8",
    )

    spec = runner.load_matrix(matrix)

    assert spec.schema_version == 1
    assert spec.scenarios[0].case.endswith("buz67d_modern_refined_sens_baseline.yaml")


def test_runner_accepts_v2_matrix(tmp_path):
    args = runner.build_parser().parse_args(["--matrix", V2_FIXTURE, "--output-dir", str(tmp_path / "out"), "--dry-run"])

    metadata = runner.execute(args)

    assert metadata["schema_version"] == 2
    assert metadata["materialized"] is True
    assert metadata["scenario_count"] == 2


def test_v2_dry_run_records_materialized_case_paths(tmp_path):
    args = runner.build_parser().parse_args(["--matrix", V2_FIXTURE, "--output-dir", str(tmp_path / "out"), "--dry-run"])

    metadata = runner.execute(args)

    action = metadata["actions"][0]
    assert action["materialized_case_path"].endswith("cgeom_075.yaml")
    assert "materialized_cases" in action["materialized_case_path"]
    assert not (tmp_path / "out" / "materialized_cases" / "cgeom_075.yaml").exists()


def test_v2_skip_run_can_summarize_synthetic_outputs(tmp_path):
    out = tmp_path / "out"
    for scenario_id in ["cgeom_075", "same_step"]:
        run_dir = out / "runs" / scenario_id
        run_dir.mkdir(parents=True)
        (run_dir / "timeseries.csv").write_text(
            "time_s,wellbore_pressure_Pa,fracture_initiated,fracture_sink_applied_m3\n"
            "0,1000,false,0\n"
            "30,2000,true,0.1\n",
            encoding="utf-8",
        )
    args = runner.build_parser().parse_args(["--matrix", V2_FIXTURE, "--output-dir", str(out), "--skip-run"])

    metadata = runner.execute(args)

    rows = runner.read_csv(out / "summary.csv")
    assert metadata["summary_csv"] is not None
    assert rows[0]["materialized_case_path"].endswith("cgeom_075.yaml")


def test_v1_dry_run_metadata_does_not_materialize(tmp_path):
    matrix = tmp_path / "v1.yaml"
    matrix.write_text(
        "matrix_id: v1\n"
        "scenarios:\n"
        "  - id: s0\n"
        "    case: cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml\n",
        encoding="utf-8",
    )
    args = runner.build_parser().parse_args(["--matrix", str(matrix), "--output-dir", str(tmp_path / "out"), "--dry-run"])

    metadata = runner.execute(args)

    assert metadata["schema_version"] == 1
    assert metadata["materialized"] is False
    assert metadata["actions"][0]["materialized_case_path"] is None


def test_v2_metadata_file_contains_materialized_dir(tmp_path):
    args = runner.build_parser().parse_args(["--matrix", V2_FIXTURE, "--output-dir", str(tmp_path / "out"), "--dry-run"])

    runner.execute(args)

    payload = json.loads((tmp_path / "out" / "metadata.json").read_text(encoding="utf-8"))
    assert payload["materialized"] is True
    assert payload["materialized_dir"].endswith("materialized_cases")
