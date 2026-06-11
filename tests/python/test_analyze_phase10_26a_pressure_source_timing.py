from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools import analyze_phase10_26a_pressure_source_timing as timing


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _legacy_rows() -> list[dict[str, object]]:
    return [
        {
            "record_type": "opening",
            "time_s": 510,
            "dt_s": 30,
            "pw_Pa": 66769500,
            "sigmaTheta_Pa": 66666600,
            "margin_Pa": 102900,
            "opened": 1,
            "sink_positive": 0,
        },
        {
            "record_type": "opening",
            "time_s": 540,
            "dt_s": 30,
            "pw_Pa": 67400000,
            "sigmaTheta_Pa": 66344400,
            "margin_Pa": 1000000,
            "opened": 1,
            "sink_positive": 1,
        },
        {
            "record_type": "opening",
            "time_s": 660,
            "dt_s": 30,
            "pw_Pa": 68300000,
            "sigmaTheta_Pa": 65445500,
            "margin_Pa": 2800000,
            "opened": 1,
            "sink_positive": 1,
        },
    ]


def _modern_rows(*, pressures: list[float], include_trial: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, pressure in enumerate(pressures):
        time_s = index * 30
        row: dict[str, object] = {
            "time_s": time_s,
            "wellbore_pressure_Pa": pressure,
            "fracture_started_this_step": int(time_s == 660),
            "fracture_initiated": int(time_s >= 660),
            "sink_active_this_step": 0,
            "sink_deferred_this_step": int(time_s == 660),
        }
        if include_trial:
            row["wellbore_pressure_trial_Pa"] = pressure
        rows.append(row)
    return rows


def _run(tmp_path: Path, modern_rows: list[dict[str, object]]) -> dict[str, object]:
    legacy = tmp_path / "legacy.csv"
    modern = tmp_path / "modern.csv"
    _write_csv(legacy, _legacy_rows())
    _write_csv(modern, modern_rows)
    return timing.analyze(
        argparse.Namespace(
            legacy_trace=legacy,
            modern_csv=modern,
            output_csv=tmp_path / "analysis.csv",
            output_json=tmp_path / "summary.json",
            output_dir=tmp_path,
        )
    )


def test_phase10_26a_help_exposes_required_arguments() -> None:
    help_text = timing.build_parser().format_help()

    assert "--legacy-trace" in help_text
    assert "--modern-csv" in help_text
    assert "--output-csv" in help_text
    assert "--output-json" in help_text


def test_candidate_can_match_legacy_opening(tmp_path: Path) -> None:
    rows = _modern_rows(
        pressures=[0.0] * 17 + [66700000.0, 68000000.0],
        include_trial=True,
    )
    result = _run(tmp_path, rows)

    assert result["classification_counts"]["MATCHES_LEGACY_OPENING"] > 0


def test_candidate_classifies_late_opening(tmp_path: Path) -> None:
    rows = _modern_rows(
        pressures=[0.0] * 24 + [66700000.0],
        include_trial=True,
    )
    result = _run(tmp_path, rows)

    assert result["classification_counts"]["OPENING_TOO_LATE"] > 0


def test_candidate_classifies_early_opening(tmp_path: Path) -> None:
    rows = _modern_rows(
        pressures=[0, 10, 20, 66700000, 68000000],
        include_trial=True,
    )
    result = _run(tmp_path, rows)

    assert result["best_candidate"]["classification"] == "OPENING_TOO_EARLY"


def test_missing_pressure_field_sets_modern_trace_export_gate(tmp_path: Path) -> None:
    rows = _modern_rows(
        pressures=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        include_trial=False,
    )
    result = _run(tmp_path, rows)

    assert result["cause"] == "MISSING_PRESSURE_TRACE_FIELDS"
    assert result["gate"] == "MODERN_TRACE_EXPORT_REQUIRED"


def test_missing_sigma_field_blocks_without_legacy_sigma(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.csv"
    modern = tmp_path / "modern.csv"
    _write_csv(
        legacy,
        [
            {
                "record_type": "opening",
                "time_s": 510,
                "pw_Pa": 1,
                "sigmaTheta_Pa": "",
                "margin_Pa": "",
                "opened": 1,
                "sink_positive": 0,
            }
        ],
    )
    _write_csv(modern, _modern_rows(pressures=[1, 2, 3], include_trial=True))

    result = timing.analyze(
        argparse.Namespace(
            legacy_trace=legacy,
            modern_csv=modern,
            output_csv=tmp_path / "analysis.csv",
            output_json=tmp_path / "summary.json",
            output_dir=tmp_path,
        )
    )

    assert result["gate"] in {
        "MODERN_TRACE_EXPORT_REQUIRED",
        "NO_FIX_UNTIL_RUNTIME_TRACE_COMPLETE",
    }
    assert result["sigmaTheta_points_from_legacy_trace"] == 0
