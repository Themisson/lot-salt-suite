from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import decide_phase10_26c_apbsalt1d_consumption as phase10_26c  # noqa: E402


CASE = ROOT / "cases" / "validation" / "buz67d_pkn_legacy_apbsalt1d_equiv_sigma_theta.yaml"


def _minimal_case(path: Path, *, include_ratio: bool = True) -> None:
    ratio_line = "        ratio: 10.0\n" if include_ratio else ""
    path.write_text(
        f"""
lot:
  fracture:
    initiation:
      sigma_theta_runtime_geometry:
        mode: apbsalt1d_legacy_equivalent
        outer_radius:
          value: 8.0
          unit: m
        radial_elements: 15
{ratio_line}        integration_order: 3
        sampling:
          mode: legacy_elem0_sig_2_0
          source: "mdl->getElem(0)->getSigmaTheta(); sig(2,0)"
        consumption_status: APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED
""".lstrip(),
        encoding="utf-8",
    )


def test_help() -> None:
    help_text = phase10_26c.build_parser().format_help()

    assert "--case" in help_text
    assert "--output-json" in help_text
    assert "--output-md" in help_text


def test_metadata_only_confirmed_for_current_case() -> None:
    decision = phase10_26c.decide(CASE)

    assert decision["apbsalt1d_consumption_status"] == "APBSALT1D_METADATA_ONLY_CONFIRMED"
    assert decision["next_phase_recommendation"] == "NEXT_PHASE_IMPLEMENT_SAMPLING_BRIDGE"
    assert decision["metadata_is_consumed"] is False
    assert "mesh_ratio_configurable" in decision["missing_capabilities"]
    assert "legacy_elem0_sig_2_0_sampling_available" in decision["missing_capabilities"]
    assert decision["pressure_source_timing_gate"].startswith("BLOCKED")


def test_real_consumption_ready_with_full_capabilities() -> None:
    capabilities = dict.fromkeys(phase10_26c.DEFAULT_CAPABILITIES, True)

    decision = phase10_26c.decide(CASE, capabilities)

    assert decision["apbsalt1d_consumption_status"] == "APBSALT1D_REAL_CONSUMPTION_READY"
    assert decision["next_phase_recommendation"] == "NEXT_PHASE_IMPLEMENT_APBSALT1D_SAMPLER"
    assert decision["metadata_is_consumed"] is True


def test_requires_radial_solver_when_mesh_generation_is_missing() -> None:
    capabilities = dict(phase10_26c.DEFAULT_CAPABILITIES)
    capabilities["radial_mesh_generation"] = False

    decision = phase10_26c.decide(CASE, capabilities)

    assert (
        decision["apbsalt1d_consumption_status"]
        == "APBSALT1D_REAL_CONSUMPTION_REQUIRES_RADIAL_SOLVER"
    )
    assert "radial_mesh_generation" in decision["missing_capabilities"]


def test_requires_sampling_bridge_when_wall_stress_exists_but_legacy_sampling_is_missing() -> None:
    capabilities = dict.fromkeys(phase10_26c.DEFAULT_CAPABILITIES, True)
    capabilities["legacy_elem0_sig_2_0_sampling_available"] = False
    capabilities["lot_provider_can_consume_wall_stress"] = False

    decision = phase10_26c.decide(CASE, capabilities)

    assert decision["apbsalt1d_consumption_status"] == "APBSALT1D_METADATA_ONLY_CONFIRMED"
    assert decision["next_phase_recommendation"] == "NEXT_PHASE_IMPLEMENT_SAMPLING_BRIDGE"
    assert "legacy_elem0_sig_2_0_sampling_available" in decision["missing_capabilities"]


def test_missing_yaml_fields_are_rejected(tmp_path: Path) -> None:
    case_path = tmp_path / "missing_ratio.yaml"
    _minimal_case(case_path, include_ratio=False)

    with pytest.raises(ValueError, match="ratio"):
        phase10_26c.decide(case_path)


def test_cli_writes_decision_outputs(tmp_path: Path) -> None:
    output_json = tmp_path / "decision.json"
    output_md = tmp_path / "decision.md"

    decision = phase10_26c.run(
        phase10_26c.build_parser().parse_args(
            [
                "--case",
                str(CASE),
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ]
        )
    )

    assert decision["phase"] == "10.26C"
    assert output_json.exists()
    assert output_md.exists()
