#!/usr/bin/env python3
"""Audit readiness for fracture/leakoff maxima in LOT/PKN sensitivity summaries."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


PHASE = "11.5D"
REQUIRED_COLUMNS = [
    "fracture_volume_m3",
    "leakoff_volume_m3",
    "fracture_length_m",
    "fracture_width_m",
    "net_pressure_Pa",
]


def read_header(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def audit(timeseries_csv: Path | None = None) -> dict:
    header: list[str] = []
    missing: list[str] = []
    if timeseries_csv:
        header = read_header(timeseries_csv)
        missing = [column for column in REQUIRED_COLUMNS if column not in header]
    return {
        "phase": PHASE,
        "status": "SUMMARY_MAXIMA_PYTHON_ONLY_SAFE" if not missing else "SUMMARY_MAXIMA_BLOCKED_MISSING_FIELDS",
        "runner_update": "MAXIMA_ADDED_TO_SUMMARY_WHEN_COLUMNS_EXIST" if not missing else "BLOCKED",
        "requires_cpp_change": False,
        "required_columns": REQUIRED_COLUMNS,
        "observed_columns": header,
        "missing_columns": missing,
        "summary_columns": [
            "max_fracture_volume_m3",
            "max_leakoff_volume_m3",
            "max_fracture_length_m",
            "max_fracture_width_m",
            "max_net_pressure_Pa",
        ],
        "caveats": [
            "This is summary aggregation only; it does not change LOT/PKN physics.",
            "Blank summary cells are allowed when legacy or old synthetic CSVs lack optional columns.",
            "Maxima are diagnostic post-processing fields, not calibration targets.",
        ],
    }


def write_markdown(path: Path, summary: dict) -> None:
    lines = [
        "# Phase 11.5D summary maxima audit",
        "",
        f"- `status`: `{summary['status']}`",
        f"- `runner_update`: `{summary['runner_update']}`",
        f"- `requires_cpp_change`: `{str(summary['requires_cpp_change']).lower()}`",
        "",
        "## Required columns",
        "",
    ]
    for column in summary["required_columns"]:
        marker = "present" if column in summary["observed_columns"] else "missing"
        lines.append(f"- `{column}`: `{marker}`")
    lines.extend(["", "## Summary columns", ""])
    for column in summary["summary_columns"]:
        lines.append(f"- `{column}`")
    lines.extend(["", "## Caveats", ""])
    for caveat in summary["caveats"]:
        lines.append(f"- {caveat}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeseries-csv", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = audit(args.timeseries_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, summary)
    print(f"PHASE={summary['phase']}")
    print(f"STATUS={summary['status']}")
    print(f"RUNNER_UPDATE={summary['runner_update']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
