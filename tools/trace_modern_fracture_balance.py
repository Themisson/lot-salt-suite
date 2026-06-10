from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _float(row: dict[str, str], field: str, default: float = 0.0) -> float:
    value = row.get(field)
    if value is None or value == "":
        return default
    parsed = float(value)
    return parsed if math.isfinite(parsed) else default


def build_trace(modern_csv: Path, modern_result_json: Path,
                threshold_json: Path) -> list[dict[str, Any]]:
    rows = _read_csv(modern_csv)
    result = _read_json(modern_result_json)
    threshold = _read_json(threshold_json)
    summary = result.get("summary", {})
    initial_pressure = float(summary.get("initial_pressure_Pa", 0.0))
    compressibility = float(summary.get("fluid_compressibility_per_Pa", 0.0))
    annular_volume = float(summary.get("initial_annular_volume_m3", 0.0))
    threshold_pa = float(threshold.get("modern_static_threshold_Pa", 0.0))

    pressure_before = initial_pressure
    previous_fracture = 0.0
    previous_leakoff = 0.0
    opened = False
    traced: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        injected_increment = _float(row, "balance_injected_volume_increment_m3")
        fracture_current = _float(row, "fracture_volume_m3")
        leakoff_current = _float(row, "leakoff_volume_m3")
        fracture_increment = _float(row, "balance_fracture_volume_increment_m3")
        leakoff_increment = _float(row, "balance_leakoff_volume_increment_m3")
        if compressibility > 0.0 and annular_volume > 0.0:
            trial_delta = injected_increment / (compressibility * annular_volume)
        else:
            trial_delta = 0.0
        trial_pressure = max(0.0, pressure_before + trial_delta)
        opened_before = opened
        if not opened and threshold_pa > 0.0:
            opened = trial_pressure - initial_pressure >= threshold_pa
        pressure_after = _float(row, "wellbore_pressure_Pa", pressure_before)
        traced.append(
            {
                "step": index,
                "time_s": _float(row, "time_s"),
                "active_phase": "injection" if injected_increment > 0.0 else "shutin",
                "injection_rate": injected_increment,
                "wellbore_pressure_before_Pa": pressure_before,
                "initial_pressure_Pa": initial_pressure,
                "accumulated_dP_before_Pa": pressure_before - initial_pressure,
                "dV_inj_m3": injected_increment,
                "breakdown_threshold_Pa": threshold_pa,
                "criterion_pressure_Pa": trial_pressure,
                "fracture_initiated_before": opened_before,
                "fracture_initiated_after": opened,
                "fracture_volume_m3": fracture_current,
                "fracture_volume_previous_m3": previous_fracture,
                "fracture_volume_increment_m3": fracture_increment,
                "leakoff_volume_m3": leakoff_current,
                "leakoff_volume_previous_m3": previous_leakoff,
                "leakoff_volume_increment_m3": leakoff_increment,
                "effective_volume_increment_m3": _float(
                    row, "balance_effective_volume_increment_m3"
                ),
                "dP_step_Pa": _float(row, "balance_delta_pressure_Pa"),
                "wellbore_pressure_after_Pa": pressure_after,
                "annular_volume_m3": annular_volume,
                "compressibility_1_Pa": compressibility,
            }
        )
        previous_fracture = fracture_current
        previous_leakoff = leakoff_current
        pressure_before = pressure_after
    return traced


def write_trace(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("modern trace has no rows")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = build_trace(
        Path(args.modern_csv),
        Path(args.modern_result_json),
        Path(args.threshold_json),
    )
    write_trace(Path(args.output_csv), rows)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a Phase 10.18F modern fracture-balance trace from lot-sim CSV."
    )
    parser.add_argument("--modern-csv", required=True)
    parser.add_argument("--modern-result-json", required=True)
    parser.add_argument("--threshold-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser


def main() -> int:
    rows = run(build_parser().parse_args())
    print(json.dumps({"phase": "10.18F", "rows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
