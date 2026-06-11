from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "analyze_phase10_25a_sigma_theta_refined.py"

sys.path.insert(0, str(ROOT / "tools"))
from analyze_phase10_25a_sigma_theta_refined import (  # noqa: E402
    analyze,
    read_trace,
    read_yaml_sigma_theta_series,
)


FIELDS = [
    "step",
    "time_min",
    "time_s",
    "dt_min",
    "dt_s",
    "idAnnular",
    "idLayer",
    "depth_influence_m",
    "thickness_m",
    "pi_Pa",
    "dP_Pa",
    "pw_Pa",
    "sigmaTheta_raw_Pa",
    "sigmaTheta_compression_positive_Pa",
    "margin_Pa",
    "opened",
    "opened_before_step",
    "opened_after_step",
    "fracture_started_this_step",
    "sink_positive",
    "sink_started_this_step",
    "dV_leakoff_m3_rad",
    "dV_leakoff_increment_m3_rad",
    "Qinj_m3_rad_min",
]


def _write_trace(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _row(
    step: int,
    time_s: float,
    sigma: float,
    pw: float,
    *,
    layer: int = 7,
    opened_before: int = 0,
    leakoff: float = 0.0,
) -> dict[str, object]:
    opened = int(pw > sigma)
    return {
        "step": step,
        "time_min": time_s / 60.0,
        "time_s": time_s,
        "dt_min": 0.5,
        "dt_s": 30.0,
        "idAnnular": 1,
        "idLayer": layer,
        "depth_influence_m": 4356.4,
        "thickness_m": 0.8,
        "pi_Pa": 5.9e7,
        "dP_Pa": pw - 5.9e7,
        "pw_Pa": pw,
        "sigmaTheta_raw_Pa": -sigma,
        "sigmaTheta_compression_positive_Pa": sigma,
        "margin_Pa": pw - sigma,
        "opened": opened,
        "opened_before_step": opened_before,
        "opened_after_step": opened,
        "fracture_started_this_step": int(opened and not opened_before),
        "sink_positive": int(leakoff > 0.0),
        "sink_started_this_step": int(leakoff > 0.0),
        "dV_leakoff_m3_rad": leakoff,
        "dV_leakoff_increment_m3_rad": leakoff,
        "Qinj_m3_rad_min": 0.0126518,
    }


def _write_yaml(path: Path, values: list[tuple[float, float]]) -> None:
    entries = "\n".join(
        f"""          - time:
              value: {time_s}
              unit: s
            sigma_theta_compression_positive:
              value: {sigma}
              unit: Pa
            layer_id: legacy_layer_7
            influence_depth:
              value: 4356.4
              unit: m"""
        for time_s, sigma in values
    )
    path.write_text(
        f"""lot:
  fracture:
    initiation:
      sigma_theta_series:
        values:
{entries}
""",
        encoding="utf-8",
    )


def _fixture(tmp_path: Path, *, yaml_values: list[tuple[float, float]]) -> tuple[Path, Path]:
    trace = tmp_path / "trace.csv"
    yaml_path = tmp_path / "case.yaml"
    _write_trace(
        trace,
        [
            _row(1, 480.0, 6.70e7, 6.60e7),
            _row(2, 510.0, 6.66e7, 6.68e7),
            _row(3, 540.0, 6.63e7, 6.74e7, opened_before=1, leakoff=0.1),
            _row(4, 660.0, 6.54e7, 6.83e7, opened_before=1, leakoff=0.2),
        ],
    )
    _write_yaml(yaml_path, yaml_values)
    return trace, yaml_path


def test_help_command() -> None:
    completed = subprocess.run([sys.executable, str(SCRIPT), "--help"], check=True)
    assert completed.returncode == 0


def test_detects_opening_sink_and_refined_gate(tmp_path: Path) -> None:
    trace, yaml_path = _fixture(
        tmp_path,
        yaml_values=[(480.0, 6.66e7), (510.0, 6.66e7), (540.0, 6.66e7)],
    )

    series, summary = analyze(read_trace(trace), read_yaml_sigma_theta_series(yaml_path))

    assert len(series) == 4
    assert summary["legacy_first_opened_time_s"] == 510.0
    assert summary["legacy_first_sink_positive_time_s"] == 540.0
    assert summary["sink_delay_s"] == 30.0
    assert summary["gate"] == "SIGMA_THETA_REFINED_PROVIDER_UPDATE_ALLOWED"
    assert "SIGMA_THETA_REFINED_SERIES_COMPLETE" in summary["classifications"]


def test_classifies_yaml_series_as_too_sparse_and_different(tmp_path: Path) -> None:
    trace, yaml_path = _fixture(
        tmp_path,
        yaml_values=[(480.0, 6.66e7), (510.0, 6.66e7), (540.0, 6.66e7)],
    )

    _, summary = analyze(read_trace(trace), read_yaml_sigma_theta_series(yaml_path))

    assert "SIGMA_THETA_YAML_SERIES_TOO_SPARSE" in summary["classifications"]
    assert "SIGMA_THETA_SOURCE_MISMATCH_EXPLAINS_OPENING_SHIFT" in summary["classifications"]
    assert summary["max_abs_difference_between_yaml_and_refined"] > 1.0e5


def test_classifies_yaml_series_as_matching_refined_when_dense(tmp_path: Path) -> None:
    values = [(480.0, 6.70e7), (510.0, 6.66e7), (540.0, 6.63e7), (660.0, 6.54e7)]
    trace, yaml_path = _fixture(tmp_path, yaml_values=values)

    _, summary = analyze(read_trace(trace), read_yaml_sigma_theta_series(yaml_path))

    assert "SIGMA_THETA_YAML_SERIES_MATCHES_REFINED" in summary["classifications"]
    assert summary["max_abs_difference_between_yaml_and_refined"] == 0.0


def test_missing_trace_fields_are_rejected(tmp_path: Path) -> None:
    trace, _ = _fixture(tmp_path, yaml_values=[(480.0, 6.7e7), (510.0, 6.66e7)])
    rows = list(csv.DictReader(trace.read_text(encoding="utf-8").splitlines()))
    fields = [field for field in FIELDS if field != "sigmaTheta_compression_positive_Pa"]
    bad = tmp_path / "bad.csv"
    with bad.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="sigmaTheta_compression_positive_Pa"):
        read_trace(bad)


def test_cli_writes_outputs_and_plots(tmp_path: Path) -> None:
    trace, yaml_path = _fixture(
        tmp_path,
        yaml_values=[(480.0, 6.66e7), (510.0, 6.66e7), (540.0, 6.66e7)],
    )
    output_csv = tmp_path / "series.csv"
    output_json = tmp_path / "summary.json"
    output_dir = tmp_path / "out"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--trace",
            str(trace),
            "--existing-yaml",
            str(yaml_path),
            "--output-csv",
            str(output_csv),
            "--output-json",
            str(output_json),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
    )

    assert output_csv.exists()
    assert output_json.exists()
    assert (output_dir / "legacy_sigma_theta_refined_trace_metadata.json").exists()
    assert (output_dir / "sigma_theta_refined_vs_time.png").exists()
