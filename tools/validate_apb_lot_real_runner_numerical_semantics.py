#!/usr/bin/env python3
"""Validate numerical semantics of the controlled APB/LOT real runner."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any


PHASE = "APB_LOT_VALIDATE_REAL_RUNNER_NUMERICAL_SEMANTICS"
VALID = "APB_LOT_REAL_RUNNER_NUMERICAL_SEMANTICS_VALID"
PARTIAL = "APB_LOT_REAL_RUNNER_NUMERICAL_SEMANTICS_PARTIAL"
FAILED = "APB_LOT_REAL_RUNNER_NUMERICAL_SEMANTICS_FAILED"
INCONCLUSIVE = "APB_LOT_REAL_RUNNER_NUMERICAL_SEMANTICS_INCONCLUSIVE"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate APB/LOT controlled runner numerical semantics."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase_apb_lot_real_runner"),
    )
    parser.add_argument("--lot-sim", type=Path)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("results/comparison/phase_apb_lot_numerical_semantics/runs"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def detect_lot_sim(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    for candidate in (
        Path("build/Debug/lot-sim.exe"),
        Path("build/Release/lot-sim.exe"),
        Path("build/lot-sim.exe"),
        Path("build/lot-sim"),
    ):
        if candidate.exists():
            return candidate
    return Path("lot-sim")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def series_numbers_are_finite(time_series: list[dict[str, Any]]) -> bool:
    numeric_fields = (
        "time_s",
        "pressure_Pa",
        "delta_pressure_Pa",
        "dV_m3",
        "dV_leakoff_m3",
        "salt_displacement_m",
    )
    for row in time_series:
        for field in numeric_fields:
            if field in row and not finite_number(row[field]):
                return False
    return True


def times_are_monotonic(time_series: list[dict[str, Any]]) -> bool:
    times = [float(row["time_s"]) for row in time_series if "time_s" in row]
    return len(times) == len(time_series) and all(
        earlier <= later for earlier, later in zip(times, times[1:])
    )


def max_field(time_series: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in time_series if field in row]
    return max(values) if values else None


def last_time(time_series: list[dict[str, Any]]) -> float | None:
    if not time_series or "time_s" not in time_series[-1]:
        return None
    return float(time_series[-1]["time_s"])


def close(a: float | None, b: float | None, tol: float = 1.0e-9) -> bool:
    if a is None or b is None:
        return False
    scale = max(1.0, abs(a), abs(b))
    return abs(a - b) <= tol * scale


def validate_summary(payload: dict[str, Any]) -> bool:
    time_series = payload.get("time_series")
    summary = payload.get("summary")
    if not isinstance(time_series, list) or not isinstance(summary, dict):
        return False
    final_value = summary.get("final_time", summary.get("final_time_s"))
    return (
        close(float(final_value), last_time(time_series))
        and close(summary.get("max_pressure_Pa"), max_field(time_series, "pressure_Pa"))
        and close(
            summary.get("max_delta_pressure_Pa"),
            max_field(time_series, "delta_pressure_Pa"),
        )
        and close(
            summary.get("total_leakoff_volume_m3"),
            max_field(time_series, "dV_leakoff_m3"),
        )
    )


def validate_volume_balance(payload: dict[str, Any]) -> bool:
    config = payload.get("configuration", {})
    time_series = payload.get("time_series", [])
    if config.get("leakoff_coupling_mode") != "volume_balance":
        return False
    leakoff_values = [float(row.get("dV_leakoff_m3", 0.0)) for row in time_series]
    total_values = [float(row.get("dV_m3", 0.0)) for row in time_series]
    return (
        any(value >= 0.0 for value in leakoff_values)
        and any(value > 0.0 for value in leakoff_values)
        and max(total_values) >= max(leakoff_values)
        and close(
            payload["summary"].get("total_leakoff_volume_m3"),
            max(leakoff_values),
        )
    )


def validate_pre_iterative(payload: dict[str, Any]) -> bool:
    config = payload.get("configuration", {})
    time_series = payload.get("time_series", [])
    caveats = payload.get("caveats", [])
    return (
        config.get("salt_displacement_mode") == "pre_iterative"
        and any(finite_number(row.get("salt_displacement_m")) for row in time_series)
        and any(abs(float(row.get("salt_displacement_m", 0.0))) > 0.0 for row in time_series)
        and "CONTROLLED_PRE_ITERATIVE_SALT_DISPLACEMENT" in caveats
    )


def validate_payload(payload: dict[str, Any]) -> dict[str, bool]:
    time_series = payload.get("time_series")
    minimal_schema = all(
        key in payload
        for key in ("metadata", "configuration", "time_series", "summary", "caveats")
    )
    time_series_non_empty = isinstance(time_series, list) and len(time_series) >= 2
    finite_values = time_series_non_empty and series_numbers_are_finite(time_series)
    time_monotonic = time_series_non_empty and times_are_monotonic(time_series)
    summary_consistent = validate_summary(payload)
    volume_balance = validate_volume_balance(payload)
    pre_iterative = validate_pre_iterative(payload)
    return {
        "json_minimum_schema": minimal_schema,
        "time_series_non_empty": time_series_non_empty,
        "finite_values": finite_values,
        "time_monotonic": time_monotonic,
        "summary_consistent": summary_consistent,
        "volume_balance_semantics_valid": volume_balance,
        "pre_iterative_semantics_valid": pre_iterative,
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validation(fixtures_dir: Path, lot_sim: Path, work_dir: Path) -> dict[str, Any]:
    modern_case = fixtures_dir / "apb_lot_modern_controlled.yaml"
    legacy_case = fixtures_dir / "apb_lot_legacy_controlled.yaml"
    modern_output_dir = work_dir / "modern"
    legacy_output_dir = work_dir / "legacy"
    modern_output_dir.mkdir(parents=True, exist_ok=True)
    legacy_output_dir.mkdir(parents=True, exist_ok=True)

    modern_run = run_command(
        [
            str(lot_sim),
            "run",
            "--case",
            str(modern_case),
            "--mode",
            "apb-lot",
            "--output",
            str(modern_output_dir),
        ]
    )
    legacy_run = run_command(
        [
            str(lot_sim),
            "run",
            "--case",
            str(legacy_case),
            "--mode",
            "apb-lot",
            "--output",
            str(legacy_output_dir),
        ]
    )
    modern_json = modern_output_dir / "apb_lot_modern_controlled_out.json"
    payload: dict[str, Any] = {}
    json_output_parseable = False
    if modern_json.exists():
      try:
          payload = read_json(modern_json)
          json_output_parseable = True
      except json.JSONDecodeError:
          payload = {}

    invariant_status = validate_payload(payload) if json_output_parseable else {
        "json_minimum_schema": False,
        "time_series_non_empty": False,
        "finite_values": False,
        "time_monotonic": False,
        "summary_consistent": False,
        "volume_balance_semantics_valid": False,
        "pre_iterative_semantics_valid": False,
    }
    legacy_ok = legacy_run.returncode == 0
    modern_ok = modern_run.returncode == 0
    all_valid = (
        modern_ok
        and legacy_ok
        and json_output_parseable
        and all(invariant_status.values())
    )
    partial = modern_ok or legacy_ok or json_output_parseable
    status = VALID if all_valid else PARTIAL if partial else FAILED
    return {
        "phase": PHASE,
        "validation_status": status,
        "modern_case_executed": modern_ok,
        "legacy_case_executed": legacy_ok,
        "json_output_parseable": json_output_parseable,
        **invariant_status,
        "legacy_modes_preserved": legacy_ok,
        "controlled_runner": True,
        "physical_validation_claimed": False,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
        "modern_json": str(modern_json),
        "commands": {
            "modern_run": {
                "returncode": modern_run.returncode,
                "stdout": modern_run.stdout,
                "stderr": modern_run.stderr,
            },
            "legacy_run": {
                "returncode": legacy_run.returncode,
                "stdout": legacy_run.stdout,
                "stderr": legacy_run.stderr,
            },
        },
        "recommended_next_phase": "APB_LOT_COMPARE_REAL_RUNNER_MODERN_VS_LEGACY_SEMANTICS",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# APB/LOT real runner numerical semantics",
        "",
        f"Status: `{report['validation_status']}`",
        "",
        "This validation checks controlled runtime semantics. It does not claim full APB/LOT physical validation.",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    keys = (
        "modern_case_executed",
        "legacy_case_executed",
        "json_output_parseable",
        "time_series_non_empty",
        "finite_values",
        "time_monotonic",
        "summary_consistent",
        "volume_balance_semantics_valid",
        "pre_iterative_semantics_valid",
        "legacy_modes_preserved",
        "controlled_runner",
        "physical_validation_claimed",
        "pkn_behavior_changed",
        "buz29_penny_executed",
        "recommended_next_phase",
    )
    for key in keys:
        lines.append(f"| `{key}` | `{report[key]}` |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    report = run_validation(args.fixtures_dir, detect_lot_sim(args.lot_sim), args.work_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)
    print(report["validation_status"])
    return 0 if report["validation_status"] == VALID else 1


if __name__ == "__main__":
    raise SystemExit(main())
