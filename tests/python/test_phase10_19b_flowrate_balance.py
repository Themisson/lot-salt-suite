from __future__ import annotations

import json
import math
from pathlib import Path

from tools import audit_phase10_19b_flowrate_balance as audit


ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "cases" / "validation" / "buz67d_pkn_legacy_sigma_theta_static.yaml"


def test_phase10_19b_help_exposes_required_arguments() -> None:
    help_text = audit.build_parser().format_help()

    assert "--case" in help_text
    assert "--output-json" in help_text
    assert "--output-csv" in help_text


def test_phase10_19b_converts_half_bpm_to_total_m3_min() -> None:
    result = audit.audit_case(CASE)
    metrics = result["metrics"]

    assert metrics["q_bbl_min"] == 0.5
    assert metrics["q_total_m3_min_legacy"] == 0.5 * 0.158987


def test_phase10_19b_converts_half_bpm_to_per_radian_m3_min() -> None:
    result = audit.audit_case(CASE)
    metrics = result["metrics"]

    expected = 0.5 * 0.158987 / (2.0 * math.pi)
    assert metrics["q_rad_m3_min_legacy"] == expected


def test_phase10_19b_computes_first_30s_injected_volume_per_radian() -> None:
    result = audit.audit_case(CASE)
    metrics = result["metrics"]

    expected = (0.5 * 0.158987 / (2.0 * math.pi) / 60.0) * 30.0
    assert metrics["dV_inj_first_step_rad_m3"] == expected


def test_phase10_19b_classifies_flowrate_convention_as_matching_legacy() -> None:
    result = audit.audit_case(CASE)

    assert result["classification"] == "FLOWRATE_CONVENTION_MATCHES_LEGACY"
    assert result["metrics"]["dP_theoretical_rad_Pa"] > 55.0e6
    assert abs(result["metrics"]["dP_total_vs_rad_relative_difference"]) < 1.0e-5


def test_phase10_19b_uses_legacy_csv_to_classify_missing_compliance(tmp_path: Path) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    legacy_csv.write_text(
        "time_s,dP,pw_Pa\n"
        "0,0,26732215.17314985\n"
        "30,1845413.7784679066,28577628.951617755\n",
        encoding="utf-8",
    )

    result = audit.audit_case(CASE, legacy_csv=legacy_csv)

    assert result["root_cause_classification"] == "ROOT_CAUSE_MISSING_GEOMETRIC_COMPLIANCE"
    assert result["metrics"]["legacy_first_dP_over_theoretical"] < 0.04


def test_phase10_19b_writes_json_and_csv_outputs(tmp_path: Path) -> None:
    output_json = tmp_path / "audit.json"
    output_csv = tmp_path / "audit.csv"
    result = audit.audit_case(CASE)

    audit.write_outputs(result, output_json, output_csv)

    saved = json.loads(output_json.read_text(encoding="utf-8"))
    assert saved["phase"] == "10.19B"
    assert saved["physical_validation"] is False
    assert "dP_pure_fluid_compression" in output_csv.read_text(encoding="utf-8")
