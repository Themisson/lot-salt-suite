from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools import extract_phase10_21a_apparent_compliance as phase10_21a


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _run(tmp_path: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    legacy = tmp_path / "legacy_trace.csv"
    out_dir = tmp_path / "out"
    _write_csv(legacy, rows)
    return phase10_21a.run_extraction(
        argparse.Namespace(
            legacy_trace=legacy,
            output_csv=out_dir / "apparent_compliance_series.csv",
            output_json=out_dir / "apparent_compliance_summary.json",
            output_dir=out_dir,
            annular_volume_m3_rad=1.0,
            fluid_compressibility_1_Pa=1.0,
            injection_duration_min=10.0,
            legacy_open_time_s=100.0,
        )
    )


def test_phase10_21a_help_exposes_required_arguments() -> None:
    help_text = phase10_21a.build_parser().format_help()

    assert "--legacy-trace" in help_text
    assert "--output-csv" in help_text
    assert "--output-json" in help_text
    assert "--annular-volume-m3-rad" in help_text


def test_phase10_21a_computes_incremental_apparent_compliance(
    tmp_path: Path,
) -> None:
    summary = _run(
        tmp_path,
        [
            {"time_s": 0, "time_min": 0, "dP": 0, "pw_Pa": 1000, "Vq_m3_rad": 0},
            {"time_s": 1, "time_min": 1, "dP": 10, "pw_Pa": 1010, "Vq_m3_rad": 20},
        ],
    )

    rows = list(
        csv.DictReader(
            (tmp_path / "out" / "apparent_compliance_series.csv").open(
                encoding="utf-8"
            )
        )
    )
    assert float(rows[1]["delta_Vq_m3_rad"]) == 20.0
    assert float(rows[1]["delta_dP_Pa"]) == 10.0
    assert float(rows[1]["C_eff_apparent_1_Pa"]) == 2.0
    assert float(rows[1]["C_geom_apparent_1_Pa"]) == 1.0
    assert summary["formula"]["status"] == "REDUCED_TRACE_NO_EXPLICIT_DV_GEOM_OR_DML"


def test_phase10_21a_classifies_near_constant(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            {"time_s": 0, "time_min": 0, "dP": 0, "pw_Pa": 1000, "Vq_m3_rad": 0},
            {"time_s": 1, "time_min": 1, "dP": 10, "pw_Pa": 1010, "Vq_m3_rad": 20},
            {"time_s": 2, "time_min": 2, "dP": 20, "pw_Pa": 1020, "Vq_m3_rad": 40},
            {"time_s": 3, "time_min": 3, "dP": 30, "pw_Pa": 1030, "Vq_m3_rad": 60},
            {"time_s": 4, "time_min": 4, "dP": 40, "pw_Pa": 1040, "Vq_m3_rad": 80},
        ],
    )

    assert summary["classification"] == "APPARENT_COMPLIANCE_NEAR_CONSTANT"
    assert summary["statistics"]["pre_opening"]["C_eff_apparent"][
        "coefficient_of_variation"
    ] == 0.0


def test_phase10_21a_classifies_pressure_dependent(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            {"time_s": 0, "time_min": 0, "dP": 0, "pw_Pa": 1000, "Vq_m3_rad": 0},
            {"time_s": 1, "time_min": 1, "dP": 10, "pw_Pa": 1010, "Vq_m3_rad": 10},
            {"time_s": 2, "time_min": 2, "dP": 20, "pw_Pa": 1020, "Vq_m3_rad": 30},
            {"time_s": 3, "time_min": 3, "dP": 30, "pw_Pa": 1030, "Vq_m3_rad": 60},
            {"time_s": 4, "time_min": 4, "dP": 40, "pw_Pa": 1040, "Vq_m3_rad": 100},
        ],
    )

    assert summary["classification"] == "APPARENT_COMPLIANCE_PRESSURE_DEPENDENT"


def test_phase10_21a_skips_zero_delta_dp(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            {"time_s": 0, "time_min": 0, "dP": 0, "pw_Pa": 1000, "Vq_m3_rad": 0},
            {"time_s": 1, "time_min": 1, "dP": 0, "pw_Pa": 1000, "Vq_m3_rad": 20},
            {"time_s": 2, "time_min": 2, "dP": 10, "pw_Pa": 1010, "Vq_m3_rad": 40},
        ],
    )

    rows = list(
        csv.DictReader(
            (tmp_path / "out" / "apparent_compliance_series.csv").open(
                encoding="utf-8"
            )
        )
    )
    assert rows[1]["formula_status"] == "SKIPPED_ZERO_DELTA_DP"
    assert rows[1]["C_eff_apparent_1_Pa"] == ""
    assert summary["statistics"]["pre_opening"]["n"] == 1


def test_phase10_21a_metadata_records_missing_fields(tmp_path: Path) -> None:
    _run(
        tmp_path,
        [
            {"time_s": 0, "time_min": 0, "dP": 0, "pw_Pa": 1000, "Vq_m3_rad": 0},
            {"time_s": 1, "time_min": 1, "dP": 10, "pw_Pa": 1010, "Vq_m3_rad": 20},
        ],
    )

    metadata = json.loads(
        (tmp_path / "out" / "legacy_apparent_compliance_trace_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["instrumentation_status"] == "NOT_MODIFIED_USING_EXISTING_AUDIT_TRACE"
    assert "dV_geom_m3_rad" in metadata["fields_missing"]
    assert "dMl_term_m3_rad" in metadata["fields_missing"]
