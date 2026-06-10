from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

from tools.compare_phase10_18e import build_parser as build_compare_parser
from tools.compare_phase10_18e import run_comparison
from tools.extract_phase10_18e_breakdown_threshold import build_parser as build_extract_parser
from tools.extract_phase10_18e_breakdown_threshold import extract_threshold, run


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_extract_phase10_18e_help() -> None:
    help_text = build_extract_parser().format_help()
    assert "--legacy-csv" in help_text
    assert "--output-json" in help_text


def test_compare_phase10_18e_help() -> None:
    help_text = build_compare_parser().format_help()
    assert "--legacy-csv" in help_text
    assert "--threshold-json" in help_text


def test_extracts_explicit_breakdown_marker_from_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "legacy.csv"
        _write_csv(
            path,
            [
                {
                    "time_min": 0.0,
                    "time_s": 0.0,
                    "pw_Pa": 10.0,
                    "dP": 0.0,
                    "opened": "false",
                    "layer": 1,
                    "annular_index": 1,
                },
                {
                    "time_min": 1.0,
                    "time_s": 60.0,
                    "pw_Pa": 15.0,
                    "dP": 5.0,
                    "opened": "true",
                    "layer": 1,
                    "annular_index": 1,
                },
            ],
        )

        result = extract_threshold(path)

        assert result["threshold_status"] == "EXTRACTED_FROM_LEGACY_MARKER"
        assert result["breakdown_time_s"] == 60.0
        assert result["breakdown_pressure_Pa"] == 15.0
        assert result["modern_static_threshold_Pa"] == 5.0


def test_extract_blocks_without_pressure_or_marker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "legacy.csv"
        _write_csv(path, [{"time_s": 0.0, "opened": "true"}])

        result = extract_threshold(path)

        assert result["threshold_status"] == "BLOCKED"
        assert "pw_Pa" in " ".join(result["caveats"])


def test_extract_writes_json_and_csv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        legacy = root / "legacy.csv"
        output_json = root / "threshold.json"
        output_csv = root / "threshold.csv"
        _write_csv(
            legacy,
            [
                {
                    "time_min": 0.0,
                    "time_s": 0.0,
                    "pw_Pa": 10.0,
                    "dP": 0.0,
                    "opened": "false",
                    "layer": 1,
                    "annular_index": 1,
                },
                {
                    "time_min": 1.0,
                    "time_s": 60.0,
                    "pw_Pa": 15.0,
                    "dP": 5.0,
                    "opened": "true",
                    "layer": 1,
                    "annular_index": 1,
                },
            ],
        )

        result = run(
            argparse.Namespace(
                legacy_csv=str(legacy),
                output_json=str(output_json),
                output_csv=str(output_csv),
            )
        )

        assert result["breakdown_pressure_Pa"] == 15.0
        assert json.loads(output_json.read_text(encoding="utf-8"))[
            "modern_static_threshold_Pa"
        ] == 5.0
        assert output_csv.exists()


def test_compare_phase10_18e_writes_summary_and_metadata() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        legacy = root / "legacy.csv"
        modern = root / "modern.csv"
        threshold = root / "threshold.json"
        output_dir = root / "out"
        _write_csv(
            legacy,
            [
                {
                    "time_s": 0.0,
                    "time_min": 0.0,
                    "pw_Pa": 10.0,
                    "injected_volume_m3": 0.0,
                },
                {
                    "time_s": 60.0,
                    "time_min": 1.0,
                    "pw_Pa": 20.0,
                    "injected_volume_m3": 1.0,
                },
            ],
        )
        _write_csv(
            modern,
            [
                {
                    "time_s": 0.0,
                    "injected_volume_m3": 0.0,
                    "wellbore_pressure_Pa": 10.0,
                    "fracture_volume_m3": 0.0,
                    "leakoff_volume_m3": 0.0,
                    "balance_fracture_volume_increment_m3": 0.0,
                    "balance_leakoff_volume_increment_m3": 0.0,
                    "balance_effective_volume_increment_m3": 0.0,
                    "balance_injected_volume_increment_m3": 0.0,
                },
                {
                    "time_s": 60.0,
                    "injected_volume_m3": 1.0,
                    "wellbore_pressure_Pa": 20.0,
                    "fracture_volume_m3": 0.5,
                    "leakoff_volume_m3": 0.1,
                    "balance_fracture_volume_increment_m3": 0.5,
                    "balance_leakoff_volume_increment_m3": 0.1,
                    "balance_effective_volume_increment_m3": 0.4,
                    "balance_injected_volume_increment_m3": 1.0,
                },
            ],
        )
        threshold.write_text(
            json.dumps(
                {
                    "breakdown_time_s": 60.0,
                    "breakdown_pressure_Pa": 20.0,
                    "modern_static_threshold_Pa": 5.0,
                }
            ),
            encoding="utf-8",
        )

        metadata = run_comparison(
            argparse.Namespace(
                legacy_csv=str(legacy),
                modern_csv=str(modern),
                threshold_json=str(threshold),
                output_dir=str(output_dir),
                modern_10_18b_csv=None,
                modern_10_18c_csv=None,
            )
        )

        assert metadata["phase"] == "10.18E"
        assert metadata["physical_validation"] is False
        assert metadata["modern_10_18e"]["first_sink_event"]["time_s"] == 60.0
        assert (output_dir / "phase10_18e_summary.csv").exists()
        assert (output_dir / "phase10_18e_metadata.json").exists()


def test_legacy_static_breakdown_case_exists_and_is_marked() -> None:
    path = Path("cases/validation/buz67d_pkn_legacy_static_breakdown.yaml")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "legacy_audit_static_threshold" in text
    assert "8131435.236221395" in text
