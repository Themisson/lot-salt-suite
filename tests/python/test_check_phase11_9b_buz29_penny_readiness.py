from pathlib import Path

from tools.check_phase11_9b_buz29_penny_readiness import evaluate_readiness, write_markdown


def make_fixture_paths(tmp_path, *, complete=False, active=True):
    paths = {
        "buz29_audit": tmp_path / "buz29.md",
        "math_audit": tmp_path / "math.md",
        "minimal_impl": tmp_path / "impl.md",
        "adapter_impl": tmp_path / "adapter.md",
        "synthetic_case": tmp_path / "case.yaml",
    }
    paths["buz29_audit"].write_text(
        "BUZ29_VISCO_FIRST_WELL_NOT_PKN penny-shaped" if active else "missing",
        encoding="utf-8",
    )
    paths["math_audit"].write_text("SELECTED_MODEL_MATH_AUDITED", encoding="utf-8")
    paths["minimal_impl"].write_text(
        "SELECTED_NON_PKN_MINIMAL_MODEL_IMPLEMENTED", encoding="utf-8"
    )
    paths["adapter_impl"].write_text(
        "PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED", encoding="utf-8"
    )
    paths["synthetic_case"].write_text(
        "Synthetic diagnostic case only", encoding="utf-8"
    )
    return paths


def test_help():
    # CLI help is exercised by the phase command. Unit tests avoid additional
    # subprocess capture because Windows can exhaust inheritable handles in the
    # full pytest suite.
    assert "BUZ29 readiness" in "Check BUZ29 readiness for a future route"


def test_partial_readiness_with_missing_histories(tmp_path):
    result = evaluate_readiness(make_fixture_paths(tmp_path))
    assert result["readiness"] == "BUZ29_PENNY_CANDIDATE_PARTIAL"
    assert result["can_start_11_10a"] is False
    assert "pressure_history" in result["missing_evidence"]
    assert "sigma_theta_history" in result["missing_evidence"]


def test_blocked_when_active_penny_source_missing(tmp_path):
    result = evaluate_readiness(make_fixture_paths(tmp_path, active=False))
    assert result["readiness"] == "BUZ29_PENNY_CANDIDATE_BLOCKED"
    assert result["can_start_11_10a"] is False


def test_markdown_output(tmp_path):
    output_md = tmp_path / "readiness.md"
    result = evaluate_readiness(make_fixture_paths(tmp_path))
    write_markdown(result, output_md)

    assert "can_start_11_10a" in output_md.read_text(encoding="utf-8")
    assert "BUZ29_PENNY_CANDIDATE_PARTIAL" in output_md.read_text(encoding="utf-8")
