#!/usr/bin/env python3
"""Run or summarize a generic LOT/PKN sensitivity matrix."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(frozen=True)
class MatrixScenario:
    id: str
    case: str
    timeseries: str | None = None


@dataclass(frozen=True)
class MatrixSpec:
    matrix_id: str
    mode: str
    base_case: str | None
    scenarios: list[MatrixScenario]


@dataclass
class SummaryRow:
    scenario_id: str
    case: str
    timeseries_csv: str
    max_pressure_Pa: float | None
    fracture_initiation_time_s: float | None
    first_sink_positive_time_s: float | None
    sink_delay_s: float | None
    final_pressure_Pa: float | None


def load_matrix(path: Path) -> MatrixSpec:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    scenarios = data.get("scenarios") or []
    if not data.get("matrix_id"):
        raise ValueError("matrix_id is required")
    if not scenarios:
        raise ValueError("scenarios is required")
    parsed = []
    for item in scenarios:
        if not item.get("id") or not item.get("case"):
            raise ValueError("each scenario requires id and case")
        parsed.append(MatrixScenario(id=str(item["id"]), case=str(item["case"]), timeseries=item.get("timeseries")))
    return MatrixSpec(
        matrix_id=str(data["matrix_id"]),
        mode=str(data.get("mode", "lot-pkn")),
        base_case=data.get("base_case"),
        scenarios=parsed,
    )


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def first_present(row: dict[str, str], names: Iterable[str]) -> float | None:
    for name in names:
        value = as_float(row.get(name))
        if value is not None:
            return value
    return None


def truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "opened"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no rows")
    return rows


def summarize_timeseries(path: Path, scenario: MatrixScenario) -> SummaryRow:
    rows = read_csv(path)
    pressures = [
        first_present(row, ["wellbore_pressure_Pa", "pressure_Pa", "wall_pressure_Pa", "net_pressure_Pa"])
        for row in rows
    ]
    pressures = [p for p in pressures if p is not None]
    if not pressures:
        raise ValueError(f"{path} has no usable pressure column")

    opened = None
    for row in rows:
        if truthy(row.get("fracture_open")) or truthy(row.get("fracture_opened")) or truthy(row.get("fracture_initiated")) or truthy(row.get("opened")):
            opened = first_present(row, ["time_s", "elapsed_time_s"])
            break

    sink_time = None
    for row in rows:
        sink = first_present(
            row,
            [
                "fracture_sink_m3",
                "fracture_sink_increment_m3",
                "fracture_sink_applied_m3",
                "leakoff_volume_increment_m3",
                "fracture_volume_increment_m3",
            ],
        )
        if sink is not None and sink > 0:
            sink_time = first_present(row, ["time_s", "elapsed_time_s"])
            break

    return SummaryRow(
        scenario_id=scenario.id,
        case=scenario.case,
        timeseries_csv=str(path),
        max_pressure_Pa=max(pressures),
        fracture_initiation_time_s=opened,
        first_sink_positive_time_s=sink_time,
        sink_delay_s=(sink_time - opened) if sink_time is not None and opened is not None else None,
        final_pressure_Pa=pressures[-1],
    )


def default_lot_sim() -> str:
    candidate = Path("build/Debug/lot-sim.exe")
    return str(candidate) if candidate.exists() else "lot-sim"


def run_command(args: list[str]) -> None:
    subprocess.run(args, check=True)


def run_matrix(spec: MatrixSpec, output_dir: Path, lot_sim: str, dry_run: bool, skip_run: bool) -> list[dict]:
    actions = []
    for scenario in spec.scenarios:
        scenario_output = output_dir / "runs" / scenario.id
        validate_cmd = [lot_sim, "validate", "--case", scenario.case]
        run_cmd = [lot_sim, "run", "--case", scenario.case, "--mode", spec.mode, "--output", str(scenario_output)]
        actions.append({"scenario_id": scenario.id, "validate": validate_cmd, "run": run_cmd})
        if dry_run or skip_run:
            continue
        run_command(validate_cmd)
        run_command(run_cmd)
    return actions


def scenario_timeseries(output_dir: Path, scenario: MatrixScenario) -> Path:
    if scenario.timeseries:
        return Path(scenario.timeseries)
    return output_dir / "runs" / scenario.id / "timeseries.csv"


def write_summary(path: Path, rows: list[SummaryRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def execute(args: argparse.Namespace) -> dict:
    spec = load_matrix(args.matrix)
    output_dir = args.output_dir
    actions = run_matrix(spec, output_dir, args.lot_sim, args.dry_run, args.skip_run or args.only_summary)
    summary_rows: list[SummaryRow] = []
    if not args.dry_run:
        for scenario in spec.scenarios:
            summary_rows.append(summarize_timeseries(scenario_timeseries(output_dir, scenario), scenario))
    summary_csv = output_dir / "summary.csv"
    if summary_rows:
        write_summary(summary_csv, summary_rows)
    metadata = {
        "matrix_id": spec.matrix_id,
        "mode": spec.mode,
        "dry_run": args.dry_run,
        "skip_run": args.skip_run,
        "only_summary": args.only_summary,
        "legacy_csv": str(args.legacy_csv) if args.legacy_csv else None,
        "scenario_count": len(spec.scenarios),
        "actions": actions,
        "summary_csv": str(summary_csv) if summary_rows else None,
        "status": "GENERIC_LOT_PKN_SENSITIVITY_RUNNER_ADDED",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--legacy-csv", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--only-summary", action="store_true")
    parser.add_argument("--lot-sim", default=default_lot_sim())
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metadata = execute(args)
    print(f"MATRIX_ID={metadata['matrix_id']}")
    print(f"SCENARIO_COUNT={metadata['scenario_count']}")
    print(f"STATUS={metadata['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
