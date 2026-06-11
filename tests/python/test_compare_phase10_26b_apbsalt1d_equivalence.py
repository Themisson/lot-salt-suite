from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import compare_phase10_26b_apbsalt1d_equivalence as phase10_26b  # noqa: E402


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _legacy_rows() -> list[dict[str, object]]:
    return [
        {
            "time_s": 480.0,
            "pw_Pa": 6.60e7,
            "opened": "false",
            "sink_positive": "false",
        },
        {
            "time_s": 510.0,
            "pw_Pa": 6.67e7,
            "opened": "true",
            "sink_positive": "false",
        },
        {
            "time_s": 540.0,
            "pw_Pa": 6.65e7,
            "opened": "true",
            "sink_positive": "true",
        },
    ]


def _modern_rows(
    *,
    opening_s: float,
    sink_s: float,
    status: str = "APBSALT1D_CONFIG_CONSUMED",
) -> list[dict[str, object]]:
    return [
        {
            "time_s": 480.0,
            "wellbore_pressure_Pa": 6.60e7,
            "fracture_started_this_step": "false",
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
            "sigma_theta_mapping_status": status,
        },
        {
            "time_s": opening_s,
            "wellbore_pressure_Pa": 6.68e7,
            "fracture_started_this_step": "true",
            "fracture_sink_applied_m3": 0.0,
            "leakoff_sink_applied_m3": 0.0,
            "sigma_theta_mapping_status": status,
        },
        {
            "time_s": sink_s,
            "wellbore_pressure_Pa": 6.65e7,
            "fracture_started_this_step": "false",
            "fracture_sink_applied_m3": 1.0,
            "leakoff_sink_applied_m3": 0.0,
            "sigma_theta_mapping_status": status,
        },
    ]


def _run(tmp_path: Path, modern_rows: list[dict[str, object]]) -> dict[str, object]:
    legacy = tmp_path / "legacy.csv"
    modern = tmp_path / "modern.csv"
    out = tmp_path / "out"
    _write_csv(legacy, _legacy_rows())
    _write_csv(modern, modern_rows)
    return phase10_26b.run_comparison(
        phase10_26b.build_parser().parse_args(
            ["--legacy-csv", str(legacy), "--modern-csv", str(modern), "--output-dir", str(out)]
        )
    )


def test_help() -> None:
    help_text = phase10_26b.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-csv" in help_text


def test_classification_metadata_only(tmp_path: Path) -> None:
    metadata = _run(
        tmp_path,
        _modern_rows(
            opening_s=660.0,
            sink_s=690.0,
            status="APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED",
        ),
    )

    assert metadata["classification"] == "APBSALT1D_EQUIVALENCE_METADATA_ONLY"
    assert (
        metadata["metrics"]["apbsalt1d_geometry_status"]
        == "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED"
    )


def test_classification_effective(tmp_path: Path) -> None:
    metadata = _run(tmp_path, _modern_rows(opening_s=510.0, sink_s=540.0))

    assert metadata["classification"] == "APBSALT1D_EQUIVALENCE_EFFECTIVE"
    assert metadata["metrics"]["opening_time_error_s"] == 0.0


def test_classification_no_change(tmp_path: Path) -> None:
    metadata = _run(tmp_path, _modern_rows(opening_s=660.0, sink_s=690.0))

    assert metadata["classification"] == "APBSALT1D_EQUIVALENCE_NO_CHANGE"
    assert metadata["metrics"]["opening_time_error_s"] == 150.0


def test_missing_required_fields(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.csv"
    modern = tmp_path / "modern.csv"
    out = tmp_path / "out"
    _write_csv(legacy, [{"time_s": 510.0, "opened": "true"}])
    _write_csv(modern, _modern_rows(opening_s=510.0, sink_s=540.0))

    with pytest.raises(ValueError, match="pw_Pa"):
        phase10_26b.run_comparison(
            phase10_26b.build_parser().parse_args(
                [
                    "--legacy-csv",
                    str(legacy),
                    "--modern-csv",
                    str(modern),
                    "--output-dir",
                    str(out),
                ]
            )
        )
