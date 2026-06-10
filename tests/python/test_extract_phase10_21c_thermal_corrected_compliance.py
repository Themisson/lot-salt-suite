from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import pytest

from tools import extract_phase10_21c_thermal_corrected_compliance as phase10_21c


def _write_legacy_case(path: Path) -> None:
    path.write_text(
        """
VectorXd A0(3), Af(3), dA(3);
A0 << 87.39, 104.6, 110.0;
Af << 90.89, 104.6, 112.0;
dA << 4230., 5618., 6000.;
double profTeste = 4374.;
vfluids[0]->setPFluid(11.5, 8E-4, 6.40E-10);
vtemp.push_back(new Temperature(0., profTeste, dA, A0, Af, .25));
""",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _minimal_rows() -> list[dict[str, object]]:
    return [
        {
            "time_min": 0,
            "time_s": 0,
            "dP": 0,
            "pw_Pa": 1000,
            "Q_SI_m3_per_min": 1,
            "injected_volume_m3": 0,
        },
        {
            "time_min": 0.5,
            "time_s": 30,
            "dP": 3_000_000,
            "pw_Pa": 3_001_000,
            "Q_SI_m3_per_min": 1,
            "injected_volume_m3": 0.5,
        },
        {
            "time_min": 1.0,
            "time_s": 60,
            "dP": 4_000_000,
            "pw_Pa": 4_001_000,
            "Q_SI_m3_per_min": 1,
            "injected_volume_m3": 1.0,
        },
        {
            "time_min": 1.5,
            "time_s": 90,
            "dP": 4_500_000,
            "pw_Pa": 4_501_000,
            "Q_SI_m3_per_min": 1,
            "injected_volume_m3": 1.5,
        },
        {
            "time_min": 2.0,
            "time_s": 120,
            "dP": 5_000_000,
            "pw_Pa": 5_001_000,
            "Q_SI_m3_per_min": 1,
            "injected_volume_m3": 2.0,
        },
    ]


def _run(tmp_path: Path, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    legacy_case = tmp_path / "legacy.cpp"
    legacy_csv = tmp_path / "audit.csv"
    out_dir = tmp_path / "out"
    _write_legacy_case(legacy_case)
    _write_csv(legacy_csv, rows or _minimal_rows())
    return phase10_21c.run_extraction(
        argparse.Namespace(
            legacy_case=legacy_case,
            legacy_audit_csv=legacy_csv,
            output_csv=out_dir / "series.csv",
            output_json=out_dir / "summary.json",
            output_dir=out_dir,
            prof_teste_m=4374.0,
            alpha_1_C=8.0e-4,
            compressibility_1_Pa=6.4e-10,
            thermal_evolution="legacy",
            annular_volume_m3_rad=1.0,
            injection_duration_min=12.5,
            legacy_open_time_s=510.0,
        )
    )


def test_phase10_21c_help_exposes_required_arguments() -> None:
    help_text = phase10_21c.build_parser().format_help()

    assert "--legacy-case" in help_text
    assert "--legacy-audit-csv" in help_text
    assert "--prof-teste-m" in help_text
    assert "--thermal-evolution" in help_text


def test_phase10_21c_linear_interpolates_legacy_temperature_profile(tmp_path: Path) -> None:
    legacy_case = tmp_path / "legacy.cpp"
    _write_legacy_case(legacy_case)

    profile = phase10_21c.build_thermal_profile(legacy_case, 4374.0)

    assert profile["T_initial_degC"] == pytest.approx(89.17547550432276)
    assert profile["T_final_degC"] == pytest.approx(92.31236311239194)
    assert profile["DTmax_degC"] == pytest.approx(3.1368876080691734)


def test_phase10_21c_extracts_alpha_and_compressibility_from_legacy_case(tmp_path: Path) -> None:
    legacy_case = tmp_path / "legacy.cpp"
    _write_legacy_case(legacy_case)

    source = legacy_case.read_text(encoding="utf-8")

    assert phase10_21c.parse_fluid_alpha_k(source) == pytest.approx((8.0e-4, 6.4e-10))


def test_phase10_21c_legacy_dtmax_and_thermal_pressure_equivalent() -> None:
    dt = phase10_21c.legacy_thermal_increment_degC(0.5, 3.1368876080691734)
    thermal_pressure = 8.0e-4 * dt / 6.4e-10

    assert dt == pytest.approx(2.091258405379449)
    assert thermal_pressure == pytest.approx(2_614_073.0067243115)


def test_phase10_21c_computes_thermal_fraction_and_mechanical_pressure(tmp_path: Path) -> None:
    _run(tmp_path)
    rows = list(csv.DictReader((tmp_path / "out" / "series.csv").open(encoding="utf-8")))

    first = rows[1]
    assert float(first["thermal_fraction_accumulated"]) == pytest.approx(
        float(first["thermal_pressure_equivalent_Pa"]) / float(first["dP_Pa"])
    )
    assert float(first["dP_mech_subtract_Pa"]) == pytest.approx(
        float(first["dP_Pa"]) - float(first["thermal_pressure_equivalent_Pa"])
    )


def test_phase10_21c_classifies_near_constant_with_synthetic_zero_thermal(tmp_path: Path) -> None:
    legacy_case = tmp_path / "legacy.cpp"
    legacy_csv = tmp_path / "audit.csv"
    out_dir = tmp_path / "out"
    _write_legacy_case(legacy_case)
    _write_csv(
        legacy_csv,
        [
            {"time_min": 0, "time_s": 0, "dP": 0, "Vq_m3_rad": 0},
            {"time_min": 1, "time_s": 60, "dP": 1_000_000, "Vq_m3_rad": 2},
            {"time_min": 2, "time_s": 120, "dP": 2_000_000, "Vq_m3_rad": 4},
            {"time_min": 3, "time_s": 180, "dP": 3_000_000, "Vq_m3_rad": 6},
            {"time_min": 4, "time_s": 240, "dP": 4_000_000, "Vq_m3_rad": 8},
        ],
    )

    summary = phase10_21c.run_extraction(
        argparse.Namespace(
            legacy_case=legacy_case,
            legacy_audit_csv=legacy_csv,
            output_csv=out_dir / "series.csv",
            output_json=out_dir / "summary.json",
            output_dir=out_dir,
            prof_teste_m=4374.0,
            alpha_1_C=1.0e-12,
            compressibility_1_Pa=1.0,
            thermal_evolution="legacy",
            annular_volume_m3_rad=1.0,
            injection_duration_min=12.5,
            legacy_open_time_s=510.0,
        )
    )

    assert summary["subtract_classification"] == "THERMAL_CORRECTED_COMPLIANCE_NEAR_CONSTANT"


def test_phase10_21c_classifies_pressure_dependent(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            {"time_min": 0, "time_s": 0, "dP": 0, "Vq_m3_rad": 0},
            {"time_min": 1, "time_s": 60, "dP": 10_000_000, "Vq_m3_rad": 1},
            {"time_min": 2, "time_s": 120, "dP": 20_000_000, "Vq_m3_rad": 3},
            {"time_min": 3, "time_s": 180, "dP": 30_000_000, "Vq_m3_rad": 6},
            {"time_min": 4, "time_s": 240, "dP": 40_000_000, "Vq_m3_rad": 10},
        ],
    )

    assert summary["add_sign_sensitivity_classification"] in {
        "THERMAL_CORRECTED_COMPLIANCE_PRESSURE_DEPENDENT",
        "THERMAL_CORRECTED_COMPLIANCE_TIME_DEPENDENT",
    }


def test_phase10_21c_rejects_missing_required_fields(tmp_path: Path) -> None:
    legacy_case = tmp_path / "legacy.cpp"
    legacy_csv = tmp_path / "bad.csv"
    _write_legacy_case(legacy_case)
    _write_csv(legacy_csv, [{"time_s": 0, "dP": 0}])

    with pytest.raises(ValueError, match="time_min"):
        phase10_21c.run_extraction(
            argparse.Namespace(
                legacy_case=legacy_case,
                legacy_audit_csv=legacy_csv,
                output_csv=tmp_path / "series.csv",
                output_json=tmp_path / "summary.json",
                output_dir=tmp_path / "out",
                prof_teste_m=4374.0,
                alpha_1_C=8.0e-4,
                compressibility_1_Pa=6.4e-10,
                thermal_evolution="legacy",
                annular_volume_m3_rad=1.0,
                injection_duration_min=12.5,
                legacy_open_time_s=510.0,
            )
        )


def test_phase10_21c_rejects_missing_input_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        phase10_21c.run_extraction(
            argparse.Namespace(
                legacy_case=tmp_path / "missing.cpp",
                legacy_audit_csv=tmp_path / "missing.csv",
                output_csv=tmp_path / "series.csv",
                output_json=tmp_path / "summary.json",
                output_dir=tmp_path / "out",
                prof_teste_m=4374.0,
                alpha_1_C=8.0e-4,
                compressibility_1_Pa=6.4e-10,
                thermal_evolution="legacy",
                annular_volume_m3_rad=1.0,
                injection_duration_min=12.5,
                legacy_open_time_s=510.0,
            )
        )


def test_phase10_21c_records_zero_delta_dp_as_invalid(tmp_path: Path) -> None:
    _run(
        tmp_path,
        [
            {"time_min": 0, "time_s": 0, "dP": 0, "Vq_m3_rad": 0},
            {"time_min": 1, "time_s": 60, "dP": 0, "Vq_m3_rad": 1},
            {"time_min": 2, "time_s": 120, "dP": 1, "Vq_m3_rad": 2},
        ],
    )
    rows = list(csv.DictReader((tmp_path / "out" / "series.csv").open(encoding="utf-8")))

    assert rows[1]["raw_status"] == "SKIPPED_NON_POSITIVE_DELTA_PRESSURE"


def test_phase10_21c_summary_contains_gate_and_plots(tmp_path: Path) -> None:
    summary = _run(tmp_path)

    assert "PRESSURE_TABULATED_STILL_BLOCKED_MISSING_BALANCE_TERMS" in summary["gate"]
    assert set(summary["plots"])
    assert json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))[
        "phase"
    ] == "10.21C"
