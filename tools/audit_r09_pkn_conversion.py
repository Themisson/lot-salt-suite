#!/usr/bin/env python3
"""Analytical R09 flow-conversion comparison.

This script is intentionally independent from legacy source files. It only
quantifies the expressions documented in the R09 audit.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "docs" / "audits" / "R09_pkn_conversion_table.csv"
Q_VALUES = (0.1, 0.3, 0.5, 1.0)


def alternatives(q_value: float) -> list[tuple[str, float, float, str]]:
    """Return label, converted value, ratio to /pi/2, and observation."""
    reference = q_value * 9.53924 / math.pi / 2.0
    rows = [
        (
            "Q * 9.53924 / (M_PI * 22)",
            q_value * 9.53924 / (math.pi * 22.0),
            "idQ == 4 suspect branch; same as /M_PI/22",
        ),
        (
            "Q * 9.53924 / M_PI / 22",
            q_value * 9.53924 / math.pi / 22.0,
            "C++ left-associative form used by Conv_bbmin_m3h",
        ),
        (
            "Q * 9.53924 / (M_PI * 2)",
            q_value * 9.53924 / (math.pi * 2.0),
            "canonical parenthesized form of /M_PI/2",
        ),
        (
            "Q * 9.53924 / M_PI / 2",
            reference,
            "pattern used by neighboring conversion functions",
        ),
        (
            "Q * 9.53924 / (2 * M_PI)",
            q_value * 9.53924 / (2.0 * math.pi),
            "identical to /M_PI/2",
        ),
    ]
    return [(label, value, value / reference, obs) for label, value, obs in rows]


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for q_value in Q_VALUES:
        for label, value, ratio, observation in alternatives(q_value):
            rows.append(
                {
                    "Q_original": f"{q_value:.6g}",
                    "alternative": label,
                    "converted_value": f"{value:.12g}",
                    "ratio_to_M_PI_2": f"{ratio:.12g}",
                    "observation": observation,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def print_table(rows: list[dict[str, str]]) -> None:
    headers = ["Q_original", "alternative", "converted_value", "ratio_to_M_PI_2"]
    widths = {key: max(len(key), *(len(row[key]) for row in rows)) for key in headers}
    print(" | ".join(key.ljust(widths[key]) for key in headers))
    print("-+-".join("-" * widths[key] for key in headers))
    for row in rows:
        print(" | ".join(row[key].ljust(widths[key]) for key in headers))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare R09 PKN conversion factors")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="CSV output path. Defaults to docs/audits/R09_pkn_conversion_table.csv",
    )
    parser.add_argument("--no-csv", action="store_true", help="Do not write CSV")
    args = parser.parse_args()

    rows = build_rows()
    print_table(rows)
    if not args.no_csv:
        write_csv(args.csv, rows)
        print(f"\nCSV written: {args.csv}")


if __name__ == "__main__":
    main()
