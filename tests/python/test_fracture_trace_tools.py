from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from tools import analyze_legacy_fracture_trace
from tools import compare_fracture_traces
from tools import trace_modern_fracture_balance


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_fracture_trace_tool_help_exposes_expected_flags() -> None:
    analyze_help = analyze_legacy_fracture_trace.build_parser().format_help()
    modern_help = trace_modern_fracture_balance.build_parser().format_help()
    compare_help = compare_fracture_traces.build_parser().format_help()

    assert "--legacy-trace" in analyze_help
    assert "--modern-csv" in modern_help
    assert "--modern-result-json" in modern_help
    assert "--threshold-json" in modern_help
    assert "--modern-trace" in compare_help
    assert "--output-dir" in compare_help


def test_analyze_legacy_trace_classifies_next_step_sink(tmp_path: Path) -> None:
    legacy_trace = tmp_path / "legacy_trace.csv"
    _write_csv(
        legacy_trace,
        [
            {
                "step": 0,
                "time_min": 0.0,
                "time_s": 0.0,
                "pw_Pa": 10.0,
                "sigmaTheta_Pa": 20.0,
                "margin_Pa": -10.0,
                "opened": 0,
                "opened_before_step": 0,
                "opened_after_step": 0,
                "fracture_volume_m3": 0.0,
                "fracture_volume_increment_m3": 0.0,
                "leakoff_volume_m3": 0.0,
                "leakoff_volume_increment_m3": 0.0,
                "dV_effective_m3": 0.0,
                "dP_step_Pa": 0.0,
                "layer": 1,
                "annular_index": 1,
            },
            {
                "step": 1,
                "time_min": 0.5,
                "time_s": 30.0,
                "pw_Pa": 25.0,
                "sigmaTheta_Pa": 20.0,
                "margin_Pa": 5.0,
                "opened": 1,
                "opened_before_step": 0,
                "opened_after_step": 1,
                "fracture_volume_m3": 0.0,
                "fracture_volume_increment_m3": 0.0,
                "leakoff_volume_m3": 0.0,
                "leakoff_volume_increment_m3": 0.0,
                "dV_effective_m3": 0.0,
                "dP_step_Pa": 1.0,
                "layer": 1,
                "annular_index": 1,
            },
            {
                "step": 2,
                "time_min": 1.0,
                "time_s": 60.0,
                "pw_Pa": 26.0,
                "sigmaTheta_Pa": 20.0,
                "margin_Pa": 6.0,
                "opened": 1,
                "opened_before_step": 1,
                "opened_after_step": 1,
                "fracture_volume_m3": 0.2,
                "fracture_volume_increment_m3": 0.2,
                "leakoff_volume_m3": 0.2,
                "leakoff_volume_increment_m3": 0.2,
                "dV_effective_m3": -0.2,
                "dP_step_Pa": 1.0,
                "layer": 1,
                "annular_index": 1,
            },
        ],
    )

    summary = analyze_legacy_fracture_trace.analyze_trace(legacy_trace)

    assert summary["legacy_sink_classification"] == "LEGACY_SINK_NEXT_STEP"
    assert summary["first_open"]["time_s"] == 30.0
    assert summary["first_positive_sink_after_open"]["time_s"] == 60.0
    assert summary["sink_enters_next_step"] is True


def test_trace_modern_fracture_balance_writes_opening_trace(tmp_path: Path) -> None:
    modern_csv = tmp_path / "modern.csv"
    result_json = tmp_path / "result.json"
    threshold_json = tmp_path / "threshold.json"
    output_csv = tmp_path / "modern_trace.csv"

    _write_csv(
        modern_csv,
        [
            {
                "time_s": 0.0,
                "balance_injected_volume_increment_m3": 0.0,
                "fracture_volume_m3": 0.0,
                "leakoff_volume_m3": 0.0,
                "balance_fracture_volume_increment_m3": 0.0,
                "balance_leakoff_volume_increment_m3": 0.0,
                "balance_effective_volume_increment_m3": 0.0,
                "balance_delta_pressure_Pa": 0.0,
                "wellbore_pressure_Pa": 100.0,
            },
            {
                "time_s": 30.0,
                "balance_injected_volume_increment_m3": 2.0,
                "fracture_volume_m3": 0.5,
                "leakoff_volume_m3": 0.25,
                "balance_fracture_volume_increment_m3": 0.5,
                "balance_leakoff_volume_increment_m3": 0.25,
                "balance_effective_volume_increment_m3": 1.25,
                "balance_delta_pressure_Pa": 12.5,
                "wellbore_pressure_Pa": 112.5,
            },
        ],
    )
    result_json.write_text(
        json.dumps(
            {
                "summary": {
                    "initial_pressure_Pa": 100.0,
                    "fluid_compressibility_per_Pa": 0.1,
                    "initial_annular_volume_m3": 10.0,
                }
            }
        ),
        encoding="utf-8",
    )
    threshold_json.write_text(
        json.dumps({"modern_static_threshold_Pa": 1.0}), encoding="utf-8"
    )

    rows = trace_modern_fracture_balance.run(
        argparse.Namespace(
            modern_csv=modern_csv,
            modern_result_json=result_json,
            threshold_json=threshold_json,
            output_csv=output_csv,
        )
    )

    assert output_csv.exists()
    assert rows[0]["fracture_initiated_after"] is False
    assert rows[1]["fracture_initiated_after"] is True
    assert rows[1]["fracture_volume_increment_m3"] == 0.5
    assert _read_csv(output_csv)[1]["fracture_initiated_after"] == "True"


def test_compare_traces_blocks_correction_when_static_threshold_opens_early(
    tmp_path: Path,
) -> None:
    legacy_trace = tmp_path / "legacy.csv"
    modern_trace = tmp_path / "modern.csv"
    output_dir = tmp_path / "comparison"

    _write_csv(
        legacy_trace,
        [
            {
                "time_s": 510.0,
                "opened": 1,
                "pw_Pa": 66769490.0,
                "sigmaTheta_Pa": 66666624.0,
                "margin_Pa": 102866.0,
                "fracture_volume_increment_m3": 0.0,
            },
            {
                "time_s": 540.0,
                "opened": 1,
                "pw_Pa": 67123526.0,
                "sigmaTheta_Pa": 66344403.0,
                "margin_Pa": 779123.0,
                "fracture_volume_increment_m3": 9.0e-5,
            },
        ],
    )
    _write_csv(
        modern_trace,
        [
            {
                "time_s": 30.0,
                "fracture_initiated_after": "True",
                "criterion_pressure_Pa": 82129237.0,
                "breakdown_threshold_Pa": 8131435.0,
                "fracture_volume_increment_m3": 0.0397,
                "wellbore_pressure_after_Pa": 26732215.0,
                "fracture_volume_m3": 0.0397,
            },
            {
                "time_s": 510.0,
                "fracture_initiated_after": "True",
                "criterion_pressure_Pa": 82129237.0,
                "breakdown_threshold_Pa": 8131435.0,
                "fracture_volume_increment_m3": 0.01,
                "wellbore_pressure_after_Pa": 26732215.0,
                "fracture_volume_m3": 0.675,
            },
        ],
    )

    metadata = compare_fracture_traces.run(
        argparse.Namespace(
            legacy_trace=legacy_trace,
            modern_trace=modern_trace,
            output_dir=output_dir,
        )
    )

    assert metadata["root_cause_classification"] == "OTHER"
    assert metadata["correction_allowed"] is False
    assert "criterion mismatch" in metadata["root_cause_detail"]
    assert (output_dir / "trace_comparison.csv").exists()
    assert (output_dir / "trace_comparison_metadata.json").exists()
