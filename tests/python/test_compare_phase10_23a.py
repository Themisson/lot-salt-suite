from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools import compare_phase10_23a


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_compare_phase10_23a_help_exposes_required_arguments() -> None:
    help_text = compare_phase10_23a.build_parser().format_help()

    assert "--legacy-csv" in help_text
    assert "--modern-same-step-csv" in help_text
    assert "--modern-next-step-csv" in help_text
    assert "--output-dir" in help_text


def test_compare_phase10_23a_classifies_next_step_sink_timing(
    tmp_path: Path,
) -> None:
    legacy_csv = tmp_path / "legacy.csv"
    same_csv = tmp_path / "same.csv"
    next_csv = tmp_path / "next.csv"
    output_dir = tmp_path / "out"

    _write_csv(
        legacy_csv,
        [
            {"time_s": 0.0, "pw_Pa": 1000.0, "dP": 0.0},
            {"time_s": 510.0, "pw_Pa": 2000.0, "dP": 1000.0},
            {"time_s": 540.0, "pw_Pa": 2500.0, "dP": 1500.0},
        ],
    )
    _write_csv(
        same_csv,
        [
            {
                "time_s": 510.0,
                "wellbore_pressure_Pa": 2000.0,
                "fracture_started_this_step": 1,
                "fracture_initiated": 1,
                "fracture_sink_applied_m3": 0.01,
                "leakoff_sink_applied_m3": 0.0,
            },
            {
                "time_s": 540.0,
                "wellbore_pressure_Pa": 2400.0,
                "fracture_started_this_step": 0,
                "fracture_initiated": 1,
                "fracture_sink_applied_m3": 0.02,
                "leakoff_sink_applied_m3": 0.0,
            },
        ],
    )
    _write_csv(
        next_csv,
        [
            {
                "time_s": 510.0,
                "wellbore_pressure_Pa": 2200.0,
                "fracture_started_this_step": 1,
                "fracture_initiated": 1,
                "fracture_sink_applied_m3": 0.0,
                "leakoff_sink_applied_m3": 0.0,
            },
            {
                "time_s": 540.0,
                "wellbore_pressure_Pa": 2450.0,
                "fracture_started_this_step": 0,
                "fracture_initiated": 1,
                "fracture_sink_applied_m3": 0.02,
                "leakoff_sink_applied_m3": 0.0,
            },
        ],
    )

    metadata = compare_phase10_23a.run_comparison(
        argparse.Namespace(
            legacy_csv=legacy_csv,
            modern_same_step_csv=same_csv,
            modern_next_step_csv=next_csv,
            output_dir=output_dir,
        )
    )

    assert metadata["phase"] == "10.23A"
    assert metadata["classification"] == "NEXT_STEP_SINK_EFFECTIVE"
    assert metadata["physical_validation"] is False
    assert metadata["runtime_default_changed"] is False
    assert metadata["metrics"]["legacy"]["sink_delay_s"] == 30.0
    assert metadata["metrics"]["same_step"]["sink_delay_s"] == 0.0
    assert metadata["metrics"]["next_step"]["sink_delay_s"] == 30.0
    assert "Diagnostic only" in " ".join(metadata["caveats"])
    assert (output_dir / "phase10_23a_summary.csv").exists()
    saved = json.loads((output_dir / "phase10_23a_metadata.json").read_text())
    assert saved["classification"] == "NEXT_STEP_SINK_EFFECTIVE"
