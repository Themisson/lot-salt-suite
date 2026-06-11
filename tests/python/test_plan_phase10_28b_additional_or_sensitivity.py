import pytest

from tools import plan_phase10_28b_additional_or_sensitivity as plan


def test_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc:
        plan.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "legacy-root" in capsys.readouterr().out


def test_buz29d_found_in_fixture(tmp_path):
    source = tmp_path / "BUZ29-PKN.cpp"
    source.write_text('fluid->setLeakoffProps("pa_min", 3., "pkn");\n', encoding="utf-8")

    candidates = plan.find_candidates(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].model_hint == "PKN"
    assert candidates[0].status == "POTENTIAL_PKN_SOURCE"


def test_buz29d_not_found_uses_sensitivity_fallback(tmp_path):
    decision = plan.decide_route(tmp_path)

    assert decision["buz29d_status"] == "BUZ29D_SOURCE_NOT_FOUND"
    assert decision["route_decision"] == plan.SENSITIVITY_ROUTE
    assert decision["sensitivity_matrix_status"] == "SENSITIVITY_MATRIX_READY"


def test_route_additional_well_ready_logic_detects_pkn_candidate(tmp_path):
    source = tmp_path / "BUZ29-PKN.cpp"
    source.write_text('vfluids[0]->setLeakoffProps("pa_min", 3., "pkn");\n', encoding="utf-8")

    decision = plan.decide_route(tmp_path)

    assert decision["buz29d_status"] == "BUZ29D_NEEDS_MORE_AUDIT"
    assert "PKN-like candidates exist" in decision["blocked_reasons"][0]


def test_route_sensitivity_fallback_for_commented_pkn(tmp_path):
    source = tmp_path / "BUZ29-VISCO-first-well.cpp"
    source.write_text(
        '// vfluids[0]->setLeakoffProps("pa_min", 3., "pkn");\n'
        'vfluids[0]->setLeakoffProps("pa_min", 3., "penny-shaped");\n',
        encoding="utf-8",
    )

    decision = plan.decide_route(tmp_path)

    assert decision["buz29d_status"] == "BUZ29D_NOT_PKN"
    assert decision["route_decision"] == plan.SENSITIVITY_ROUTE


def test_route_blocked_when_legacy_root_missing(tmp_path):
    missing = tmp_path / "missing"

    decision = plan.decide_route(missing)

    assert decision["buz29d_status"] == "BUZ29D_SOURCE_NOT_FOUND"
    assert "not available" in decision["blocked_reasons"][0]


def test_minimal_matrix_is_generated():
    scenarios = plan.planned_scenarios()

    assert [s.scenario_id for s in scenarios] == [
        "S0_baseline",
        "S1_lower_compliance",
        "S2_higher_compliance",
        "S3_same_step",
    ]
    assert {s.c_geom_factor for s in scenarios} == {0.75, 1.0, 1.25}
    assert {s.sink_timing for s in scenarios} == {"next_step", "same_step"}
