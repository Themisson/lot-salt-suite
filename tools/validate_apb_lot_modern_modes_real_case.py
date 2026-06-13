#!/usr/bin/env python3
"""Audit whether APB/LOT modern modes can run through a real runtime case."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


PHASE = "APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE"
BLOCKED_STATUS = "APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER"
AVAILABLE_STATUS = "APB_LOT_REAL_CASE_RUNNER_AVAILABLE_NEEDS_OUTPUT"
VALID_STATUS = "APB_LOT_MODERN_MODES_REAL_CASE_VALID"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _fixture_scalars(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in _read(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in {
            "name",
            "output_format",
            "output_path",
            "legacy_dat_output_enabled",
            "leakoff_coupling_mode",
            "salt_displacement_mode",
        }:
            values[key] = value.strip().strip('"')
    return values


def _finite_summary(payload: dict[str, Any]) -> bool:
    summary = payload.get("summary")
    if not isinstance(summary, dict) or not summary:
        return False
    numeric_values = [value for value in summary.values() if isinstance(value, (int, float))]
    return bool(numeric_values) and all(math.isfinite(float(value)) for value in numeric_values)


def _json_has_effective_data(path: Path) -> dict[str, bool]:
    if not path.exists():
        return {
            "modern_json_output_generated": False,
            "modern_json_parseable": False,
            "modern_json_has_effective_data": False,
            "time_series_non_empty": False,
            "summary_finite": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "modern_json_output_generated": True,
            "modern_json_parseable": False,
            "modern_json_has_effective_data": False,
            "time_series_non_empty": False,
            "summary_finite": False,
        }
    time_series = payload.get("time_series")
    time_series_non_empty = isinstance(time_series, list) and len(time_series) > 0
    summary_finite = _finite_summary(payload)
    sections_present = all(
        key in payload
        for key in ("metadata", "configuration", "time_series", "layers", "annulars", "summary", "caveats")
    )
    return {
        "modern_json_output_generated": True,
        "modern_json_parseable": True,
        "modern_json_has_effective_data": sections_present and time_series_non_empty and summary_finite,
        "time_series_non_empty": time_series_non_empty,
        "summary_finite": summary_finite,
    }


def audit_runtime(fixtures_dir: Path, modern_json: Path | None = None) -> dict[str, Any]:
    app_text = _read(Path("apps/lot-sim.cpp"))
    writer_text = _read(Path("src/io/ApbLotJsonOutputWriter.cpp"))
    case_parser_text = _read(Path("src/io/CaseParser.cpp"))
    pkn_only_runtime = "run suporta apenas --mode lot-pkn nesta fase" in app_text
    writer_integrated_with_runtime = (
        "write_apb_lot_output_json" in app_text
        or ("ApbLotRunner" in app_text and "run_apb_lot_case" in app_text)
    )
    parser_accepts_apb_lot = "parse_apb_lot_modern_modes" in case_parser_text
    writer_available = "write_apb_lot_output_json" in writer_text

    runner_available = (not pkn_only_runtime) and writer_integrated_with_runtime
    fixtures = sorted(fixtures_dir.glob("*.yaml")) if fixtures_dir.exists() else []
    fixture_modes = {item.name: _fixture_scalars(item) for item in fixtures}
    has_modern_fixture = any(
        values.get("output_format") == "json"
        and values.get("leakoff_coupling_mode") == "volume_balance"
        and values.get("salt_displacement_mode") == "pre_iterative"
        for values in fixture_modes.values()
    )
    has_legacy_fixture = any(
        values.get("output_format") == "legacy_dat"
        and values.get("leakoff_coupling_mode") == "legacy_nodal_force"
        and values.get("salt_displacement_mode") == "legacy_inside_newton"
        for values in fixture_modes.values()
    )

    json_status = _json_has_effective_data(modern_json) if modern_json else {
        "modern_json_output_generated": False,
        "modern_json_parseable": False,
        "modern_json_has_effective_data": False,
        "time_series_non_empty": False,
        "summary_finite": False,
    }
    if runner_available and json_status["modern_json_has_effective_data"]:
        validation_status = VALID_STATUS
    elif runner_available:
        validation_status = AVAILABLE_STATUS
    else:
        validation_status = BLOCKED_STATUS

    report: dict[str, Any] = {
        "phase": PHASE,
        "validation_status": validation_status,
        "real_case_runner_available": runner_available,
        "modern_case_executed": runner_available and json_status["modern_json_output_generated"],
        "legacy_case_executed": False,
        **json_status,
        "volume_balance_exercised": runner_available and json_status["modern_json_has_effective_data"],
        "pre_iterative_exercised": runner_available and json_status["modern_json_has_effective_data"],
        "blocked_by_missing_runtime_integration": not runner_available,
        "writer_available": writer_available,
        "parser_accepts_apb_lot": parser_accepts_apb_lot,
        "writer_integrated_with_runtime": writer_integrated_with_runtime,
        "volume_balance_integrated_with_solver": False,
        "pre_iterative_integrated_with_solver": False,
        "fixture_count": len(fixtures),
        "modern_fixture_available": has_modern_fixture,
        "legacy_fixture_available": has_legacy_fixture,
        "legacy_modes_preserved": has_legacy_fixture,
        "runtime_metrics_available": False,
        "pkn_behavior_changed": False,
        "buz29_penny_executed": False,
        "blocking_reasons": [],
        "recommended_next_phase": (
            "APB_LOT_DECIDE_MODERN_MODES_RUNTIME_READINESS"
            if validation_status == VALID_STATUS
            else (
                "APB_LOT_IMPLEMENT_REAL_CASE_RUNNER_INTEGRATION"
                if validation_status == BLOCKED_STATUS
                else "APB_LOT_RUN_REAL_CASE_OUTPUT_VALIDATION"
            )
        ),
    }
    if not runner_available:
        report["blocking_reasons"] = [
            "apps/lot-sim.cpp accepts only run --mode lot-pkn",
            "ApbLotJsonOutputWriter is not called by the runtime",
            "volume_balance and pre_iterative are parser/contracts, not exercised by a real APB solver",
        ]
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# APB/LOT modern modes real case validation",
        "",
        f"Status: `{report['validation_status']}`",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for key in (
        "real_case_runner_available",
        "modern_case_executed",
        "legacy_case_executed",
        "modern_json_output_generated",
        "modern_json_has_effective_data",
        "volume_balance_exercised",
        "pre_iterative_exercised",
        "writer_integrated_with_runtime",
        "pkn_behavior_changed",
        "buz29_penny_executed",
        "recommended_next_phase",
    ):
        lines.append(f"| `{key}` | `{report[key]}` |")
    if report["blocking_reasons"]:
        lines.extend(["", "## Blocking reasons", ""])
        lines.extend(f"- {reason}" for reason in report["blocking_reasons"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate or block APB/LOT modern modes with a real controlled runtime case."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures/comparison/phase_apb_lot_real_case"),
    )
    parser.add_argument("--modern-json", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    report = audit_runtime(args.fixtures_dir, args.modern_json)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)
    print(report["validation_status"])
    return 0 if report["validation_status"] in {VALID_STATUS, BLOCKED_STATUS, AVAILABLE_STATUS} else 1


if __name__ == "__main__":
    raise SystemExit(main())
