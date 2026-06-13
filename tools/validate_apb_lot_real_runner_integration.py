#!/usr/bin/env python3
"""Validate the controlled APB/LOT real runner integration."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


PHASE = "APB_LOT_IMPLEMENT_REAL_CASE_RUNNER_INTEGRATION"
IMPLEMENTED = "APB_LOT_REAL_CASE_RUNNER_IMPLEMENTED"
PARTIAL = "APB_LOT_REAL_CASE_RUNNER_PARTIAL"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run controlled APB/LOT fixtures through lot-sim --mode apb-lot."
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
        default=Path("results/comparison/phase_apb_lot_real_runner/tool_runs"),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def detect_lot_sim(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    candidates = [
        Path("build/Debug/lot-sim.exe"),
        Path("build/Release/lot-sim.exe"),
        Path("build/lot-sim.exe"),
        Path("build/lot-sim"),
    ]
    for candidate in candidates:
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_has_effective_data(payload: dict[str, Any]) -> bool:
    time_series = payload.get("time_series")
    summary = payload.get("summary")
    return (
        isinstance(payload.get("metadata"), dict)
        and isinstance(payload.get("configuration"), dict)
        and isinstance(time_series, list)
        and len(time_series) >= 2
        and isinstance(summary, dict)
        and summary.get("max_pressure_Pa") is not None
        and summary.get("max_delta_pressure_Pa") is not None
    )


def has_positive_leakoff(payload: dict[str, Any]) -> bool:
    return any(float(row.get("dV_leakoff_m3", 0.0)) > 0.0 for row in payload["time_series"])


def has_salt_displacement(payload: dict[str, Any]) -> bool:
    return any(abs(float(row.get("salt_displacement_m", 0.0))) > 0.0 for row in payload["time_series"])


def run_integration(fixtures_dir: Path, lot_sim: Path, work_dir: Path) -> dict[str, Any]:
    modern_case = fixtures_dir / "apb_lot_modern_controlled.yaml"
    explicit_case = fixtures_dir / "apb_lot_modern_explicit_output.yaml"
    legacy_case = fixtures_dir / "apb_lot_legacy_controlled.yaml"
    invalid_case = fixtures_dir / "apb_lot_invalid_mode.yaml"
    modern_output_dir = work_dir / "modern"
    explicit_output_dir = work_dir / "explicit"
    legacy_output_dir = work_dir / "legacy"

    for directory in (modern_output_dir, explicit_output_dir, legacy_output_dir):
        directory.mkdir(parents=True, exist_ok=True)

    commands: dict[str, list[str]] = {
        "modern_run": [
            str(lot_sim),
            "run",
            "--case",
            str(modern_case),
            "--mode",
            "apb-lot",
            "--output",
            str(modern_output_dir),
        ],
        "explicit_run": [
            str(lot_sim),
            "run",
            "--case",
            str(explicit_case),
            "--mode",
            "apb-lot",
            "--output",
            str(explicit_output_dir),
        ],
        "legacy_run": [
            str(lot_sim),
            "run",
            "--case",
            str(legacy_case),
            "--mode",
            "apb-lot",
            "--output",
            str(legacy_output_dir),
        ],
        "invalid_validate": [
            str(lot_sim),
            "validate",
            "--case",
            str(invalid_case),
        ],
    }
    completed = {name: run_command(command) for name, command in commands.items()}

    modern_json = modern_output_dir / "apb_lot_modern_controlled_out.json"
    explicit_json = explicit_output_dir / "custom/apb_lot_modern_explicit_out.json"
    modern_payload = read_json(modern_json) if modern_json.exists() else {}
    explicit_payload = read_json(explicit_json) if explicit_json.exists() else {}

    modern_ok = completed["modern_run"].returncode == 0 and json_has_effective_data(modern_payload)
    explicit_ok = completed["explicit_run"].returncode == 0 and json_has_effective_data(explicit_payload)
    legacy_ok = completed["legacy_run"].returncode == 0
    invalid_rejected = completed["invalid_validate"].returncode != 0
    volume_balance = modern_ok and modern_payload["configuration"].get("leakoff_coupling_mode") == "volume_balance" and has_positive_leakoff(modern_payload)
    pre_iterative = modern_ok and modern_payload["configuration"].get("salt_displacement_mode") == "pre_iterative" and has_salt_displacement(modern_payload)

    all_ok = all((modern_ok, explicit_ok, legacy_ok, invalid_rejected, volume_balance, pre_iterative))
    return {
        "phase": PHASE,
        "integration_status": IMPLEMENTED if all_ok else PARTIAL,
        "cli_mode_added": "apb-lot",
        "modern_case_executed": modern_ok,
        "legacy_case_accepted": legacy_ok,
        "invalid_mode_rejected": invalid_rejected,
        "json_output_generated": modern_json.exists(),
        "json_output_parseable": bool(modern_payload),
        "json_has_effective_data": modern_ok,
        "time_series_non_empty": bool(modern_payload.get("time_series")),
        "output_name_rule_valid": modern_json.name == "apb_lot_modern_controlled_out.json",
        "explicit_output_path_valid": explicit_ok and explicit_json.exists(),
        "volume_balance_exercised": volume_balance,
        "pre_iterative_exercised": pre_iterative,
        "legacy_modes_preserved": legacy_ok,
        "not_physically_validated": True,
        "not_legacy_equivalent": True,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
        "modern_json": str(modern_json),
        "explicit_json": str(explicit_json),
        "commands": {
            name: {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            for name, proc in completed.items()
        },
        "recommended_next_phase": "APB_LOT_VALIDATE_REAL_RUNNER_NUMERICAL_SEMANTICS",
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# APB/LOT real runner integration",
        "",
        f"Status: `{report['integration_status']}`",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for key in (
        "modern_case_executed",
        "legacy_case_accepted",
        "invalid_mode_rejected",
        "json_output_generated",
        "json_has_effective_data",
        "output_name_rule_valid",
        "explicit_output_path_valid",
        "volume_balance_exercised",
        "pre_iterative_exercised",
        "legacy_modes_preserved",
        "pkn_behavior_changed",
        "buz29_penny_executed",
    ):
        lines.append(f"| `{key}` | `{report[key]}` |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    report = run_integration(args.fixtures_dir, detect_lot_sim(args.lot_sim), args.work_dir)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)
    print(report["integration_status"])
    return 0 if report["integration_status"] == IMPLEMENTED else 1


if __name__ == "__main__":
    raise SystemExit(main())
