#!/usr/bin/env python3
"""Compare PKN outputs with diagnostic pre-runner disabled and enabled.

Phase 11.11B proves that enabling the diagnostic pre-runner writes only the
isolated diagnostic JSON and does not change the physical PKN outputs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PHASE = "11.11B"
STATUS_OK = "PKN_OUTPUTS_UNCHANGED_WITH_DIAGNOSTICS"
STATUS_FAILED = "PKN_OUTPUTS_CHANGED_OR_DIAGNOSTIC_NOT_ISOLATED"
RECOMMENDED_NEXT_PHASE = "PHASE11_11C_DECIDE_RUNTIME_WIRING_INTEGRATION_READINESS"
DEFAULT_CASES = [
    Path("cases/validation/lot_pkn_minimal.yaml"),
    Path("cases/validation/lot_pkn_with_leakoff.yaml"),
]
PHYSICAL_OUTPUTS = ["result.json", "timeseries.csv"]
DIAGNOSTIC_OUTPUT = "diagnostic_fracture_gate.json"


@dataclass
class CaseComparison:
    case_id: str
    disabled_output_dir: str
    enabled_output_dir: str
    physical_outputs_identical: bool
    diagnostic_output_isolated: bool
    diagnostic_output_present_enabled: bool
    diagnostic_output_absent_disabled: bool
    changed_files: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def inject_diagnostic_block(case_text: str) -> str:
    if "fracture_gate_diagnostics:" in case_text:
        return case_text
    lines = case_text.splitlines()
    output: list[str] = []
    inserted = False
    for line in lines:
        output.append(line)
        if not inserted and line == "  fracture:":
            output.extend(
                [
                    "    fracture_gate_diagnostics:",
                    "      enabled: true",
                    "      mode: pre_runner",
                    "      dispatch_runtime_enabled: false",
                ]
            )
            inserted = True
    if not inserted:
        raise ValueError("case YAML does not contain expected '  fracture:' block")
    return "\n".join(output) + "\n"


def find_default_lot_sim() -> Path:
    candidates = [
        Path("build/Debug/lot-sim.exe"),
        Path("build/Release/lot-sim.exe"),
        Path("build/lot-sim.exe"),
        Path("lot-sim.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("lot-sim")


def run_lot_sim(lot_sim: Path, case_path: Path, output_dir: Path) -> None:
    cmd = [
        str(lot_sim),
        "run",
        "--mode",
        "lot-pkn",
        "--case",
        str(case_path),
        "--output",
        str(output_dir),
    ]
    subprocess.run(cmd, check=True)


def prepare_and_run_cases(
    cases: list[Path], lot_sim: Path, work_dir: Path
) -> list[CaseComparison]:
    comparisons: list[CaseComparison] = []
    for case_path in cases:
        case_id = case_path.stem
        case_dir = work_dir / case_id
        disabled_case = case_dir / "disabled" / case_path.name
        enabled_case = case_dir / "enabled" / case_path.name
        disabled_output = case_dir / "disabled_output"
        enabled_output = case_dir / "enabled_output"

        source = read_text(case_path)
        write_text(disabled_case, source)
        write_text(enabled_case, inject_diagnostic_block(source))

        run_lot_sim(lot_sim, disabled_case, disabled_output)
        run_lot_sim(lot_sim, enabled_case, enabled_output)
        comparisons.append(compare_output_pair(case_id, disabled_output, enabled_output))
    return comparisons


def compare_output_pair(case_id: str, disabled_dir: Path, enabled_dir: Path) -> CaseComparison:
    changed_files: list[str] = []
    for name in PHYSICAL_OUTPUTS:
        disabled_file = disabled_dir / name
        enabled_file = enabled_dir / name
        if not disabled_file.exists() or not enabled_file.exists():
            changed_files.append(f"{name}:missing")
            continue
        if disabled_file.read_bytes() != enabled_file.read_bytes():
            changed_files.append(name)

    diagnostic_enabled = (enabled_dir / DIAGNOSTIC_OUTPUT).exists()
    diagnostic_absent_disabled = not (disabled_dir / DIAGNOSTIC_OUTPUT).exists()
    return CaseComparison(
        case_id=case_id,
        disabled_output_dir=str(disabled_dir),
        enabled_output_dir=str(enabled_dir),
        physical_outputs_identical=not changed_files,
        diagnostic_output_isolated=diagnostic_enabled and diagnostic_absent_disabled,
        diagnostic_output_present_enabled=diagnostic_enabled,
        diagnostic_output_absent_disabled=diagnostic_absent_disabled,
        changed_files=changed_files,
    )


def comparisons_from_fixture(fixture_root: Path) -> list[CaseComparison]:
    comparisons: list[CaseComparison] = []
    for case_dir in sorted(path for path in fixture_root.iterdir() if path.is_dir()):
        disabled_dir = case_dir / "disabled"
        enabled_dir = case_dir / "enabled"
        if disabled_dir.exists() and enabled_dir.exists():
            comparisons.append(compare_output_pair(case_dir.name, disabled_dir, enabled_dir))
    if not comparisons:
        raise ValueError("fixture root does not contain case/disabled and case/enabled pairs")
    return comparisons


def build_report(comparisons: list[CaseComparison], source: str) -> dict[str, Any]:
    physical_outputs_identical = all(item.physical_outputs_identical for item in comparisons)
    diagnostic_output_isolated = all(item.diagnostic_output_isolated for item in comparisons)
    ok = physical_outputs_identical and diagnostic_output_isolated
    return {
        "phase": PHASE,
        "source": source,
        "comparison_status": STATUS_OK if ok else STATUS_FAILED,
        "physical_outputs_identical": physical_outputs_identical,
        "diagnostic_output_isolated": diagnostic_output_isolated,
        "pkn_behavior_changed": not physical_outputs_identical,
        "runtime_physical_dispatch_enabled": False,
        "buz29_execution_allowed": False,
        "compared_physical_outputs": PHYSICAL_OUTPUTS,
        "diagnostic_output": DIAGNOSTIC_OUTPUT,
        "cases": [item.__dict__ for item in comparisons],
        "required_statuses": [
            "PHASE11_11B_PKN_OUTPUTS_COMPARED_WITH_DIAGNOSTICS",
            STATUS_OK,
            "DIAGNOSTIC_OUTPUT_ISOLATED",
            "RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED",
            "BUZ29_EXECUTION_BLOCKED",
        ],
        "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        "caveats": [
            "Phase 11.11B compares result.json and timeseries.csv only.",
            "The diagnostic pre-runner remains opt-in and isolated.",
            "Physical dispatch remains disabled.",
            "BUZ29-PENNY is not executed.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Phase 11.11B PKN Diagnostic Regression",
        "",
        f"- phase: `{report['phase']}`",
        f"- comparison_status: `{report['comparison_status']}`",
        f"- physical_outputs_identical: `{report['physical_outputs_identical']}`",
        f"- diagnostic_output_isolated: `{report['diagnostic_output_isolated']}`",
        f"- pkn_behavior_changed: `{report['pkn_behavior_changed']}`",
        f"- runtime_physical_dispatch_enabled: `{report['runtime_physical_dispatch_enabled']}`",
        f"- buz29_execution_allowed: `{report['buz29_execution_allowed']}`",
        "",
        "## Cases",
    ]
    for item in report["cases"]:
        lines.extend(
            [
                "",
                f"### {item['case_id']}",
                f"- physical_outputs_identical: `{item['physical_outputs_identical']}`",
                f"- diagnostic_output_isolated: `{item['diagnostic_output_isolated']}`",
                f"- changed_files: `{', '.join(item['changed_files']) or 'none'}`",
            ]
        )
    lines.extend(["", "## Caveats"])
    lines.extend(f"- {item}" for item in report["caveats"])
    write_text(path, "\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Phase 11.11B PKN outputs with diagnostics disabled/enabled."
    )
    parser.add_argument("--lot-sim", type=Path, default=find_default_lot_sim())
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("results/comparison/phase11_11b/pkn_diagnostic_regression"),
    )
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--case", dest="cases", type=Path, action="append")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_root:
        comparisons = comparisons_from_fixture(args.fixture_root)
        report = build_report(comparisons, "FIXTURE_OUTPUT_PAIRS")
    else:
        cases = args.cases or DEFAULT_CASES
        if args.work_dir.exists():
            shutil.rmtree(args.work_dir)
        comparisons = prepare_and_run_cases(cases, args.lot_sim, args.work_dir)
        report = build_report(comparisons, "LOT_SIM_RUN_OUTPUTS")

    if args.output_json:
        write_text(args.output_json, json.dumps(report, indent=2) + "\n")
    if args.output_md:
        write_markdown(args.output_md, report)

    print(f"phase={report['phase']}")
    print(f"comparison_status={report['comparison_status']}")
    print(f"physical_outputs_identical={report['physical_outputs_identical']}")
    print(f"diagnostic_output_isolated={report['diagnostic_output_isolated']}")
    return 0 if report["comparison_status"] == STATUS_OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
