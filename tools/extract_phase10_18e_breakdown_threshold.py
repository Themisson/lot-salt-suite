from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any


PHASE = "10.18E"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _finite_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _truthy_marker(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "opened", "open"}


def _find_marker_row(rows: list[dict[str, str]]) -> tuple[dict[str, str], str] | None:
    marker_fields = [
        "fracture_started",
        "opened",
        "legacy_algebra_opened",
        "breakdown",
    ]
    for field in marker_fields:
        if field not in rows[0]:
            continue
        for row in rows:
            if _truthy_marker(row.get(field)):
                return row, f"explicit_marker:{field}"
    return None


def _event_time_from_rows(rows: list[dict[str, str]]) -> tuple[float, str] | None:
    for field in ("momento_da_quebra_raw", "breakdown_time_min", "breakdown_time"):
        if field not in rows[0]:
            continue
        values = [_finite_float(row.get(field)) for row in rows]
        values = [value for value in values if value is not None]
        if values:
            return values[0], f"csv_event_field:{field}:minutes"
    for field in ("breakdown_time_s", "fracture_start_time_s"):
        if field not in rows[0]:
            continue
        values = [_finite_float(row.get(field)) for row in rows]
        values = [value for value in values if value is not None]
        if values:
            return values[0] / 60.0, f"csv_event_field:{field}:seconds"
    return None


def _event_time_from_native_output(legacy_csv: Path) -> tuple[float, str] | None:
    native = legacy_csv.with_name("legacy_native_output.dat")
    if not native.exists():
        return None
    text = native.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"Momento\s+da\s+quebra:\s*([-+0-9.eE]+)", text)
    if not match:
        return None
    value = float(match.group(1))
    if not math.isfinite(value):
        return None
    return value, f"native_output:{native.name}:Momento da quebra:minutes"


def _aggregate_row_at_time(
    rows: list[dict[str, str]], time_min: float
) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if (value := _finite_float(row.get("time_min"))) is not None
        and abs(value - time_min) <= 1.0e-9
    ]
    if not matches:
        matches = [
            row
            for row in rows
            if (value := _finite_float(row.get("time_s"))) is not None
            and abs(value / 60.0 - time_min) <= 1.0e-9
        ]
    if not matches:
        return None
    return max(matches, key=lambda row: _finite_float(row.get("pw_Pa")) or -math.inf)


def _group_max_pressure_by_time(rows: list[dict[str, str]]) -> list[dict[str, float]]:
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        time_s = _finite_float(row.get("time_s"))
        if time_s is not None:
            grouped.setdefault(time_s, []).append(row)

    points: list[dict[str, float]] = []
    for time_s in sorted(grouped):
        selected = max(
            grouped[time_s],
            key=lambda row: _finite_float(row.get("pw_Pa")) or -math.inf,
        )
        pressure = _finite_float(selected.get("pw_Pa"))
        volume = _finite_float(selected.get("injected_volume_m3"))
        if pressure is None or volume is None:
            continue
        points.append(
            {
                "time_s": time_s,
                "time_min": time_s / 60.0,
                "pressure_Pa": pressure,
                "injected_volume_m3": volume,
            }
        )
    return points


def _infer_curve_breakdown(rows: list[dict[str, str]]) -> tuple[dict[str, str], str] | None:
    points = _group_max_pressure_by_time(rows)
    if len(points) < 4:
        return None

    slopes: list[tuple[int, float]] = []
    for idx in range(1, len(points)):
        dv = points[idx]["injected_volume_m3"] - points[idx - 1]["injected_volume_m3"]
        dp = points[idx]["pressure_Pa"] - points[idx - 1]["pressure_Pa"]
        if dv > 0.0:
            slopes.append((idx, dp / dv))
    if len(slopes) < 3:
        return None

    best_idx = slopes[1][0]
    best_drop = 0.0
    for prev, current in zip(slopes, slopes[1:]):
        if prev[1] <= 0.0:
            continue
        drop = (prev[1] - current[1]) / prev[1]
        if drop > best_drop:
            best_drop = drop
            best_idx = current[0]

    if best_drop <= 0.0:
        return None
    selected_point = points[best_idx]
    row = _aggregate_row_at_time(rows, selected_point["time_min"])
    if row is None:
        return None
    return row, f"curve_slope_drop:max_relative_drop:{best_drop:.6g}"


def _make_result(
    legacy_csv: Path,
    rows: list[dict[str, str]],
    selected: dict[str, str] | None,
    status: str,
    method: str,
    caveats: list[str],
) -> dict[str, Any]:
    if selected is None:
        return {
            "phase": PHASE,
            "threshold_status": "BLOCKED",
            "method": method,
            "source_csv": str(legacy_csv),
            "columns": list(rows[0].keys()) if rows else [],
            "caveats": caveats,
        }

    pressure = _finite_float(selected.get("pw_Pa"))
    time_s = _finite_float(selected.get("time_s"))
    time_min = _finite_float(selected.get("time_min"))
    if pressure is None or time_s is None:
        return {
            "phase": PHASE,
            "threshold_status": "BLOCKED",
            "method": method,
            "source_csv": str(legacy_csv),
            "columns": list(rows[0].keys()) if rows else [],
            "caveats": caveats + ["selected row lacks finite pw_Pa or time_s"],
        }

    delta_pressure = _finite_float(selected.get("dP"))
    if delta_pressure is None:
        initial_at_same_layer = next(
            (
                _finite_float(row.get("pw_Pa"))
                for row in rows
                if row.get("layer") == selected.get("layer")
                and row.get("annular_index") == selected.get("annular_index")
                and (_finite_float(row.get("time_s")) or 0.0) == 0.0
            ),
            None,
        )
        if initial_at_same_layer is not None:
            delta_pressure = pressure - initial_at_same_layer
    if delta_pressure is None or delta_pressure < 0.0:
        delta_pressure = 0.0
        caveats.append("breakdown delta pressure unavailable; modern static threshold set to 0")

    return {
        "phase": PHASE,
        "threshold_status": status,
        "breakdown_time_s": time_s,
        "breakdown_time_min": time_min if time_min is not None else time_s / 60.0,
        "breakdown_pressure_Pa": pressure,
        "breakdown_pressure_MPa": pressure / 1.0e6,
        "breakdown_delta_pressure_Pa": delta_pressure,
        "breakdown_delta_pressure_MPa": delta_pressure / 1.0e6,
        "modern_static_threshold_Pa": delta_pressure,
        "modern_static_threshold_MPa": delta_pressure / 1.0e6,
        "selected_layer": selected.get("layer", ""),
        "selected_annular_index": selected.get("annular_index", ""),
        "selected_injected_volume_m3": _finite_float(selected.get("injected_volume_m3")),
        "method": method,
        "source_csv": str(legacy_csv),
        "columns": list(rows[0].keys()) if rows else [],
        "caveats": caveats,
    }


def extract_threshold(legacy_csv: Path) -> dict[str, Any]:
    rows = _read_csv(legacy_csv)
    if not rows:
        return {
            "phase": PHASE,
            "threshold_status": "BLOCKED",
            "method": "empty_csv",
            "source_csv": str(legacy_csv),
            "caveats": ["legacy CSV has no rows"],
        }
    if "pw_Pa" not in rows[0]:
        return _make_result(
            legacy_csv,
            rows,
            None,
            "BLOCKED",
            "missing_pw_Pa",
            ["legacy CSV does not expose pw_Pa"],
        )

    marker = _find_marker_row(rows)
    if marker is not None:
        return _make_result(
            legacy_csv,
            rows,
            marker[0],
            "EXTRACTED_FROM_LEGACY_MARKER",
            marker[1],
            [
                "diagnostic only; not final sigma-theta runtime criterion",
                "modern PknModel threshold uses delta above initial pressure",
            ],
        )

    event_time = _event_time_from_rows(rows) or _event_time_from_native_output(legacy_csv)
    if event_time is not None:
        row = _aggregate_row_at_time(rows, event_time[0])
        return _make_result(
            legacy_csv,
            rows,
            row,
            "EXTRACTED_FROM_LEGACY_MARKER",
            event_time[1],
            [
                "breakdown event came from legacy audit event time, not sigma-theta runtime",
                "selected row is the maximum pw_Pa row at the event time",
                "modern PknModel threshold uses legacy dP/delta pressure, while absolute pw_Pa is recorded separately",
            ],
        )

    inferred = _infer_curve_breakdown(rows)
    if inferred is not None:
        return _make_result(
            legacy_csv,
            rows,
            inferred[0],
            "CALIBRATED_FROM_LEGACY_CURVE",
            inferred[1],
            [
                "breakdown was inferred from curve slope, not an explicit legacy marker",
                "diagnostic only; not final sigma-theta runtime criterion",
                "modern PknModel threshold uses delta above initial pressure",
            ],
        )

    return _make_result(
        legacy_csv,
        rows,
        None,
        "BLOCKED",
        "no_marker_or_curve_inference",
        ["could not identify a traceable breakdown threshold"],
    )


def _write_one_row_csv(path: Path, data: dict[str, Any]) -> None:
    fields = [
        "phase",
        "threshold_status",
        "breakdown_time_s",
        "breakdown_time_min",
        "breakdown_pressure_Pa",
        "breakdown_pressure_MPa",
        "breakdown_delta_pressure_Pa",
        "breakdown_delta_pressure_MPa",
        "modern_static_threshold_Pa",
        "modern_static_threshold_MPa",
        "selected_layer",
        "selected_annular_index",
        "selected_injected_volume_m3",
        "method",
        "source_csv",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({field: data.get(field, "") for field in fields})


def run(args: argparse.Namespace) -> dict[str, Any]:
    legacy_csv = Path(args.legacy_csv)
    result = extract_threshold(legacy_csv)
    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_one_row_csv(output_csv, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Phase 10.18E static breakdown threshold from legacy audit CSV."
    )
    parser.add_argument("--legacy-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser


def main() -> int:
    parser = build_parser()
    result = run(parser.parse_args())
    print(json.dumps(result, indent=2))
    return 0 if result.get("threshold_status") != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
