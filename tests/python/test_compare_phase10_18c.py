from __future__ import annotations

import argparse
import csv
import json
import math
import tempfile
from pathlib import Path

from tools.compare_phase10_18c import run_comparison


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_phase10_18c_compares_uncoupled_and_fracture_coupled_balance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        legacy_csv = root / "legacy.csv"
        modern_csv = root / "modern.csv"
        modern_json = root / "result.json"
        output_dir = root / "out"

        _write_csv(
            legacy_csv,
            [
                {"time_s": 0, "injected_volume_m3": 0.0, "pw_Pa": 10.0},
                {"time_s": 1, "injected_volume_m3": 1.0, "pw_Pa": 90.0},
            ],
        )
        _write_csv(
            modern_csv,
            [
                {
                    "time_s": 0,
                    "injected_volume_m3": 0.0,
                    "initial_pressure_Pa": 10.0,
                    "wellbore_pressure_Pa": 10.0,
                    "balance_injected_volume_increment_m3": 0.0,
                    "balance_fracture_volume_increment_m3": 0.0,
                    "balance_leakoff_volume_increment_m3": 0.0,
                    "balance_effective_volume_increment_m3": 0.0,
                },
                {
                    "time_s": 1,
                    "injected_volume_m3": 1.0,
                    "initial_pressure_Pa": 10.0,
                    "wellbore_pressure_Pa": 60.0,
                    "balance_injected_volume_increment_m3": 1.0,
                    "balance_fracture_volume_increment_m3": 0.4,
                    "balance_leakoff_volume_increment_m3": 0.1,
                    "balance_effective_volume_increment_m3": 0.5,
                },
            ],
        )
        modern_json.write_text(
            json.dumps(
                {
                    "summary": {
                        "fluid_compressibility_per_Pa": 0.1,
                        "initial_annular_volume_m3": 0.1,
                    }
                }
            ),
            encoding="utf-8",
        )

        metadata = run_comparison(
            argparse.Namespace(
                legacy_csv=str(legacy_csv),
                modern_coupled_csv=str(modern_csv),
                modern_result_json=str(modern_json),
                output_dir=str(output_dir),
            )
        )

        assert metadata["phase"] == "10.18C"
        assert (
            metadata["gate"]
            == "FRACTURE_VOLUME_BALANCE_IMPLEMENTATION_ALLOWED_PRESSURE_THRESHOLD_APPROXIMATION"
        )
        assert metadata["physical_validation"] is False
        assert math.isclose(
            metadata["modern_uncoupled_reconstruction"]["max_pressure_Pa"], 110.0
        )
        assert metadata["modern_coupled_10_18c"]["max_pressure_Pa"] == 60.0
        assert metadata["modern_coupled_10_18c"]["total_fracture_sink_increment_m3"] == 0.4
        assert metadata["modern_coupled_10_18c"]["total_leakoff_sink_increment_m3"] == 0.1
        assert "sigma-theta" in " ".join(metadata["caveats"])
        assert (output_dir / "phase10_18c_summary.csv").exists()
        assert (output_dir / "phase10_18c_metadata.json").exists()
