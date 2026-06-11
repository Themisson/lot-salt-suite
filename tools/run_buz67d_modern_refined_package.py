#!/usr/bin/env python3
"""Run the reproducible BUZ-67D modern-refined validation package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import run_lot_pkn_sensitivity_matrix as matrix_runner


DEFAULT_MATRIX = Path("cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml")
DEFAULT_OUTPUT_DIR = Path("results/comparison/buz67d_modern_refined_package")
DEFAULT_LEGACY_OPENING_TIME_S = 510.0
DEFAULT_LEGACY_MAX_PRESSURE_PA = 69035836.1743195
MINIMAL_VALIDATION_CASES = [
    Path("cases/validation/lot_pkn_minimal.yaml"),
    Path("cases/validation/lot_pkn_with_leakoff.yaml"),
    Path("cases/lot_tese_migrated/buz67d_pkn.yaml"),
]


def command_text(command: list[str]) -> str:
    return " ".join(command)


def existing_lot_sim(path: str | None) -> str | None:
    if path:
        return path if Path(path).exists() else None
    candidate = Path("build/Debug/lot-sim.exe")
    if candidate.exists():
        return str(candidate)
    found = shutil.which("lot-sim")
    return found


def validate_inputs(matrix: Path, lot_sim: str | None, dry_run: bool, only_report: bool) -> matrix_runner.MatrixSpec:
    spec = matrix_runner.load_matrix(matrix)
    if not dry_run and not only_report and lot_sim is None:
        raise FileNotFoundError("lot-sim executable not found; pass --lot-sim or build Debug first")
    return spec


def build_commands(args: argparse.Namespace, spec: matrix_runner.MatrixSpec, lot_sim: str | None) -> dict[str, list[list[str]]]:
    lot_sim_arg = lot_sim or args.lot_sim or "lot-sim"
    validation_commands = [[lot_sim_arg, "validate", "--case", str(case)] for case in MINIMAL_VALIDATION_CASES]
    matrix_validation_commands = [[lot_sim_arg, "validate", "--case", scenario.case] for scenario in spec.scenarios]
    matrix_command = [
        sys.executable,
        "tools/run_lot_pkn_sensitivity_matrix.py",
        "--matrix",
        str(args.matrix),
        "--output-dir",
        str(args.output_dir),
        "--lot-sim",
        lot_sim_arg,
    ]
    if args.skip_run:
        matrix_command.append("--skip-run")
    if args.only_report:
        matrix_command.append("--only-summary")

    summary = args.existing_summary or args.output_dir / "summary.csv"
    metadata = args.existing_metadata or args.output_dir / "metadata.json"
    report_command = [
        sys.executable,
        "tools/report_lot_pkn_sensitivity_matrix.py",
        "--summary",
        str(summary),
        "--metadata",
        str(metadata),
        "--output-json",
        str(args.output_dir / "sensitivity_report.json"),
        "--output-md",
        str(args.output_dir / "sensitivity_report.md"),
        "--legacy-opening-time-s",
        str(DEFAULT_LEGACY_OPENING_TIME_S),
        "--legacy-max-pressure-Pa",
        str(DEFAULT_LEGACY_MAX_PRESSURE_PA),
    ]
    return {
        "minimal_validations": validation_commands,
        "matrix_validations": matrix_validation_commands,
        "matrix_run": [matrix_command],
        "report": [report_command],
    }


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def write_run_commands(path: Path, commands: dict[str, list[list[str]]]) -> None:
    lines: list[str] = []
    for section, section_commands in commands.items():
        lines.append(f"[{section}]")
        for command in section_commands:
            lines.append(command_text(command))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_if_exists(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return True


def write_metadata(path: Path, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execute(args: argparse.Namespace) -> dict:
    lot_sim = existing_lot_sim(args.lot_sim)
    spec = validate_inputs(args.matrix, lot_sim, args.dry_run, args.only_report)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    commands = build_commands(args, spec, lot_sim)
    write_run_commands(args.output_dir / "run_commands.txt", commands)

    status = "BUZ67D_MODERN_REFINED_PACKAGE_DRY_RUN" if args.dry_run else "BUZ67D_MODERN_REFINED_PACKAGE_RUN_OK"
    if not args.dry_run:
        if not args.skip_build_check:
            for command in commands["minimal_validations"]:
                run_command(command)
        if not args.only_report:
            for command in commands["matrix_validations"]:
                run_command(command)
        if not args.only_report:
            run_command(commands["matrix_run"][0])
        run_command(commands["report"][0])
        copy_if_exists(args.output_dir / "summary.csv", args.output_dir / "sensitivity_summary.csv")
        copy_if_exists(args.output_dir / "metadata.json", args.output_dir / "sensitivity_metadata.json")

    metadata = {
        "status": status,
        "phase": "10.31A",
        "matrix": str(args.matrix),
        "matrix_id": spec.matrix_id,
        "mode": spec.mode,
        "scenario_count": len(spec.scenarios),
        "output_dir": str(args.output_dir),
        "lot_sim": lot_sim or args.lot_sim or "lot-sim",
        "dry_run": args.dry_run,
        "skip_run": args.skip_run,
        "only_report": args.only_report,
        "commands": commands,
        "expected_outputs": {
            "package_metadata_json": str(args.output_dir / "package_metadata.json"),
            "run_commands_txt": str(args.output_dir / "run_commands.txt"),
            "sensitivity_summary_csv": str(args.output_dir / "sensitivity_summary.csv"),
            "sensitivity_metadata_json": str(args.output_dir / "sensitivity_metadata.json"),
            "sensitivity_report_json": str(args.output_dir / "sensitivity_report.json"),
            "sensitivity_report_md": str(args.output_dir / "sensitivity_report.md"),
        },
        "caveats": [
            "results/ outputs are local and must not be versioned.",
            "The matrix is diagnostic; best factors are not automatic calibration.",
            "This package does not change C++ runtime behavior.",
        ],
    }
    write_metadata(args.output_dir / "package_metadata.json", metadata)
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--lot-sim")
    parser.add_argument("--skip-build-check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--only-report", action="store_true")
    parser.add_argument("--existing-summary", type=Path)
    parser.add_argument("--existing-metadata", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metadata = execute(args)
    print(f"PHASE={metadata['phase']}")
    print(f"STATUS={metadata['status']}")
    print(f"MATRIX_ID={metadata['matrix_id']}")
    print(f"SCENARIO_COUNT={metadata['scenario_count']}")
    print(f"OUTPUT_DIR={metadata['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
