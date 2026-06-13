import json
import subprocess
import sys
from pathlib import Path

from tools import validate_apb_lot_real_runner_integration as validator


SCRIPT = Path("tools/validate_apb_lot_real_runner_integration.py")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_help() -> None:
    assert run_script("--help").returncode == 0


def test_json_has_effective_data() -> None:
    payload = {
        "metadata": {},
        "configuration": {},
        "time_series": [{"time_s": 0}, {"time_s": 30}],
        "summary": {"max_pressure_Pa": 10.0, "max_delta_pressure_Pa": 1.0},
    }

    assert validator.json_has_effective_data(payload) is True


def test_json_without_timeseries_is_not_effective() -> None:
    payload = {
        "metadata": {},
        "configuration": {},
        "time_series": [],
        "summary": {"max_pressure_Pa": 10.0, "max_delta_pressure_Pa": 1.0},
    }

    assert validator.json_has_effective_data(payload) is False


def test_positive_leakoff_detection() -> None:
    payload = {"time_series": [{"dV_leakoff_m3": 0.0}, {"dV_leakoff_m3": 0.01}]}

    assert validator.has_positive_leakoff(payload) is True


def test_salt_displacement_detection() -> None:
    payload = {"time_series": [{"salt_displacement_m": 0.0}, {"salt_displacement_m": -0.001}]}

    assert validator.has_salt_displacement(payload) is True


def test_markdown_writer(tmp_path: Path) -> None:
    report = {
        "integration_status": validator.IMPLEMENTED,
        "modern_case_executed": True,
        "legacy_case_accepted": True,
        "invalid_mode_rejected": True,
        "json_output_generated": True,
        "json_has_effective_data": True,
        "output_name_rule_valid": True,
        "explicit_output_path_valid": True,
        "volume_balance_exercised": True,
        "pre_iterative_exercised": True,
        "legacy_modes_preserved": True,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
    }
    output = tmp_path / "report.md"

    validator.write_markdown(output, report)

    assert output.exists()
    assert "APB/LOT real runner integration" in output.read_text(encoding="utf-8")


def test_report_can_be_serialized() -> None:
    report = {
        "phase": validator.PHASE,
        "integration_status": validator.IMPLEMENTED,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
    }

    assert json.loads(json.dumps(report))["integration_status"] == validator.IMPLEMENTED
