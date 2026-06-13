import json
import subprocess
import sys
from pathlib import Path

from tools import validate_apb_lot_real_runner_numerical_semantics as validator


SCRIPT = Path("tools/validate_apb_lot_real_runner_numerical_semantics.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def valid_payload() -> dict:
    return {
        "metadata": {"case_id": "apb_lot"},
        "configuration": {
            "leakoff_coupling_mode": "volume_balance",
            "salt_displacement_mode": "pre_iterative",
        },
        "time_series": [
            {
                "time_s": 0.0,
                "pressure_Pa": 30_000_000.0,
                "delta_pressure_Pa": 0.0,
                "dV_m3": 0.0,
                "dV_leakoff_m3": 0.0,
                "salt_displacement_m": 0.0,
            },
            {
                "time_s": 30.0,
                "pressure_Pa": 30_001_650.0,
                "delta_pressure_Pa": 1_650.0,
                "dV_m3": 0.0165,
                "dV_leakoff_m3": 0.0015,
                "salt_displacement_m": -0.0001,
            },
        ],
        "summary": {
            "max_pressure_Pa": 30_001_650.0,
            "max_delta_pressure_Pa": 1_650.0,
            "total_leakoff_volume_m3": 0.0015,
            "final_time": 30.0,
        },
        "caveats": ["CONTROLLED_PRE_ITERATIVE_SALT_DISPLACEMENT"],
    }


def test_help() -> None:
    assert run_script("--help").returncode == 0


def test_validates_numerical_semantics() -> None:
    status = validator.validate_payload(valid_payload())

    assert status["time_series_non_empty"] is True
    assert status["finite_values"] is True
    assert status["time_monotonic"] is True
    assert status["summary_consistent"] is True
    assert status["volume_balance_semantics_valid"] is True
    assert status["pre_iterative_semantics_valid"] is True


def test_rejects_nonfinite_values() -> None:
    payload = valid_payload()
    payload["time_series"][1]["pressure_Pa"] = float("nan")

    assert validator.validate_payload(payload)["finite_values"] is False


def test_rejects_decreasing_time() -> None:
    payload = valid_payload()
    payload["time_series"][1]["time_s"] = -1.0

    assert validator.validate_payload(payload)["time_monotonic"] is False


def test_rejects_inconsistent_summary() -> None:
    payload = valid_payload()
    payload["summary"]["max_pressure_Pa"] = 1.0

    assert validator.validate_payload(payload)["summary_consistent"] is False


def test_markdown_writer(tmp_path: Path) -> None:
    report = {
        "validation_status": validator.VALID,
        "modern_case_executed": True,
        "legacy_case_executed": True,
        "json_output_parseable": True,
        "time_series_non_empty": True,
        "finite_values": True,
        "time_monotonic": True,
        "summary_consistent": True,
        "volume_balance_semantics_valid": True,
        "pre_iterative_semantics_valid": True,
        "legacy_modes_preserved": True,
        "controlled_runner": True,
        "physical_validation_claimed": False,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
        "recommended_next_phase": "NEXT",
    }
    output = tmp_path / "report.md"

    validator.write_markdown(output, report)

    assert output.exists()
    assert "numerical semantics" in output.read_text(encoding="utf-8")


def test_report_can_be_serialized() -> None:
    report = {
        "phase": validator.PHASE,
        "validation_status": validator.VALID,
        "modern_case_executed": True,
        "json_output_parseable": True,
    }

    assert json.loads(json.dumps(report))["validation_status"] == validator.VALID
