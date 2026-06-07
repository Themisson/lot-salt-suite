from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PSI_TO_PA = 6894.757293168

POINT_FIELDS = [
    "source_file",
    "source_kind",
    "record_type",
    "annular",
    "time_raw",
    "time_unit_inferred",
    "time_s",
    "layer",
    "md",
    "dT",
    "dP",
    "dV",
    "u",
    "compressibilidade",
    "C_Exp",
    "Vq",
    "dV_leakoff",
    "V_outflow",
    "pressure_start_psi",
    "pressure_final_psi",
    "pressure_diff_psi",
    "pressure_apb_psi",
    "pressure_start_Pa",
    "pressure_final_Pa",
    "pressure_diff_Pa",
    "pressure_apb_Pa",
    "volume_start",
    "volume_final",
    "volume_diff",
    "vented_bbl",
    "leakage_bbl",
    "leakage_mass",
    "salt_displacement",
    "momento_da_quebra_raw",
]

SUMMARY_FIELDS = [
    "source_file",
    "source_kind",
    "n_records",
    "has_time",
    "has_layer",
    "has_dP",
    "has_dV_leakoff",
    "has_pressure_json",
    "has_pressure_Pa",
    "has_sigmaTheta",
    "has_pw",
    "has_margin",
    "has_opened",
    "comparison_readiness",
    "notes",
]

FIELD_GROUPS = {
    "directly_comparable": [
        "Time",
        "Layer",
        "dP",
        "dV",
        "dV_leakoff",
        "V_outflow",
    ],
    "requires_transformation": [
        "Time -> time_s",
        "Layer -> layer_id/depth mapping",
        "pressure psi -> Pa",
        "dV_leakoff -> metric only, not opened",
    ],
    "missing_without_instrumentation": [
        "pw",
        "sigmaTheta",
        "margin",
        "opened",
        "hoop_state",
        "j2",
        "von_mises",
    ],
}

CAVEATS = [
    "LOT_Tese does not export pw directly",
    "LOT_Tese does not export sigmaTheta directly",
    "LOT_Tese does not export margin/opened directly",
    "time units may require manual normalization",
    "LOT_APB_v5 pressures are converted from psi to Pa",
]

LOT_TESE_FIELDS = {
    "dT": "dT",
    "dP": "dP",
    "dV": "dV",
    "u": "u",
    "Compressibilidade": "compressibilidade",
    "C_Exp": "C_Exp",
    "Vq": "Vq",
    "dV_leakoff": "dV_leakoff",
    "V_outflow": "V_outflow",
}


@dataclass
class ExtractionResult:
    source_file: str
    source_kind: str
    points: list[dict[str, Any]]
    notes: list[str]


def _blank_record(source_file: Path, source_kind: str, record_type: str) -> dict[str, Any]:
    row = {field: "" for field in POINT_FIELDS}
    row["source_file"] = str(source_file)
    row["source_kind"] = source_kind
    row["record_type"] = record_type
    return row


def _parse_float(token: str) -> float | None:
    try:
        value = float(token)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def _parse_float_line(line: str) -> list[float]:
    values: list[float] = []
    for token in line.replace(",", " ").split():
        parsed = _parse_float(token)
        if parsed is not None:
            values.append(parsed)
    return values


def _next_non_empty(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index


def _read_matrix(lines: list[str], start: int, n_rows: int) -> tuple[list[list[float]], int]:
    rows: list[list[float]] = []
    index = start
    while index < len(lines) and len(rows) < n_rows:
        values = _parse_float_line(lines[index])
        if values:
            rows.append(values)
        index += 1
    return rows, index


def parse_lot_tese_dat(path: Path) -> ExtractionResult:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    times: list[float] = []
    points: list[dict[str, Any]] = []
    notes = [
        "LOT_Tese .dat output; time unit is not inferred automatically",
        "Layer is 1-based in the legacy output",
        "pw/sigmaTheta/margin/opened are not exported directly",
    ]
    current_layer = ""
    momento_da_quebra = ""

    index = 0
    while index < len(lines):
        label = lines[index].strip()

        if label == "Time":
            next_index = _next_non_empty(lines, index + 1)
            if next_index < len(lines):
                times = _parse_float_line(lines[next_index])
            index = next_index + 1
            continue

        if label == "Layer":
            next_index = _next_non_empty(lines, index + 1)
            current_layer = lines[next_index].strip() if next_index < len(lines) else ""
            index = next_index + 1
            continue

        if label.startswith("Momento da quebra"):
            if ":" in label:
                momento_da_quebra = label.split(":", 1)[1].strip()
            else:
                next_index = _next_non_empty(lines, index + 1)
                if next_index < len(lines):
                    momento_da_quebra = lines[next_index].strip()
                    index = next_index
            index += 1
            continue

        if label in LOT_TESE_FIELDS:
            rows_index = _next_non_empty(lines, index + 1)
            n_rows = 0
            if rows_index < len(lines):
                parsed_rows = _parse_float(lines[rows_index].strip())
                n_rows = int(parsed_rows) if parsed_rows is not None else 0
            matrix, index = _read_matrix(lines, rows_index + 1, n_rows)
            column_name = LOT_TESE_FIELDS[label]
            for annular_index, values in enumerate(matrix, start=1):
                max_count = max(len(values), len(times))
                for time_index in range(max_count):
                    row = _blank_record(path, "LOT_Tese_DAT", label)
                    row["annular"] = annular_index
                    row["layer"] = current_layer if label != "V_outflow" else ""
                    row["time_unit_inferred"] = "unknown"
                    if time_index < len(times):
                        row["time_raw"] = times[time_index]
                    if time_index < len(values):
                        row[column_name] = values[time_index]
                    points.append(row)
            continue

        index += 1

    if momento_da_quebra:
        for row in points:
            row["momento_da_quebra_raw"] = momento_da_quebra
        if not points:
            row = _blank_record(path, "LOT_Tese_DAT", "Momento da quebra")
            row["momento_da_quebra_raw"] = momento_da_quebra
            points.append(row)

    return ExtractionResult(str(path), "LOT_Tese_DAT", points, notes)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _value_at(value: Any, index: int) -> Any:
    if isinstance(value, list):
        if not value:
            return ""
        if index < len(value):
            return value[index]
        return ""
    if value is None:
        return ""
    return value


def _pressure_value(pressure: dict[str, Any], key: str, index: int) -> Any:
    return _value_at(pressure.get(key), index)


def _pressure_pa(value: Any) -> Any:
    if value == "":
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    return numeric * PSI_TO_PA


def _salt_displacement_at(value: Any, index: int) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        selected = value[index] if index < len(value) else value
    else:
        selected = value
    return json.dumps(selected, separators=(",", ":"), ensure_ascii=False)


def parse_lot_apb_v5_json(path: Path) -> ExtractionResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    points: list[dict[str, Any]] = []
    notes = [
        "LOT_APB_v5 JSON output; pressure fields are interpreted as psi and converted to Pa",
        "pw/sigmaTheta/margin/opened are not exported directly",
    ]

    containers = data if isinstance(data, list) else [data]
    for container_index, container in enumerate(containers):
        if not isinstance(container, dict):
            continue
        annuli = container.get("annuli", {})
        if isinstance(annuli, list):
            annulus_items = [(str(i), item) for i, item in enumerate(annuli)]
        elif isinstance(annuli, dict):
            annulus_items = sorted(annuli.items(), key=lambda item: str(item[0]))
        else:
            annulus_items = []

        for annular_id, annulus in annulus_items:
            if not isinstance(annulus, dict):
                continue
            md = _as_list(annulus.get("md"))
            results = annulus.get("results_by_time")
            if results is None:
                results = annulus.get("results")
            if results is None and ("pressure" in annulus or "volume" in annulus):
                results = [
                    {
                        "time": container.get("time", container.get("duration", "")),
                        "pressure": annulus.get("pressure", {}),
                        "volume": annulus.get("volume", {}),
                        "vented_bbl": annulus.get("vented_bbl", ""),
                        "leakage_bbl": annulus.get("leakage_bbl", ""),
                        "leakage_mass": annulus.get("leakage_mass", ""),
                        "salt_displacement": annulus.get("salt_displacement", ""),
                    }
                ]
            for result in _as_list(results):
                if not isinstance(result, dict):
                    continue
                points.extend(
                    _parse_lot_apb_v5_result(
                        path,
                        annular_id,
                        md,
                        result,
                        container_index,
                    )
                )

    return ExtractionResult(str(path), "LOT_APB_v5_JSON", points, notes)


def _parse_lot_apb_v5_result(
    path: Path,
    annular_id: str,
    md: list[Any],
    result: dict[str, Any],
    container_index: int,
) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    pressure = result.get("pressure", {})
    if not isinstance(pressure, dict):
        pressure = {}
    volume = result.get("volume", {})
    if not isinstance(volume, dict):
        volume = {}

    max_count = max(
        1,
        len(md),
        len(_as_list(pressure.get("start"))),
        len(_as_list(pressure.get("final"))),
        len(_as_list(pressure.get("diff"))),
    )
    for i in range(max_count):
        row = _blank_record(path, "LOT_APB_v5_JSON", "results_by_time")
        row["annular"] = annular_id
        row["time_raw"] = result.get("time", "")
        row["time_s"] = result.get("time", "")
        row["time_unit_inferred"] = "as_exported"
        row["md"] = _value_at(md, i)
        pressure_start = _pressure_value(pressure, "start", i)
        pressure_final = _pressure_value(pressure, "final", i)
        pressure_diff = _pressure_value(pressure, "diff", i)
        pressure_apb = _pressure_value(pressure, "APB", i)
        row["pressure_start_psi"] = pressure_start
        row["pressure_final_psi"] = pressure_final
        row["pressure_diff_psi"] = pressure_diff
        row["pressure_apb_psi"] = pressure_apb
        row["pressure_start_Pa"] = _pressure_pa(pressure_start)
        row["pressure_final_Pa"] = _pressure_pa(pressure_final)
        row["pressure_diff_Pa"] = _pressure_pa(pressure_diff)
        row["pressure_apb_Pa"] = _pressure_pa(pressure_apb)
        row["volume_start"] = _value_at(volume.get("start"), i)
        row["volume_final"] = _value_at(volume.get("final"), i)
        row["volume_diff"] = _value_at(volume.get("diff"), i)
        row["vented_bbl"] = result.get("vented_bbl", "")
        row["leakage_bbl"] = result.get("leakage_bbl", "")
        row["leakage_mass"] = result.get("leakage_mass", "")
        row["salt_displacement"] = _salt_displacement_at(result.get("salt_displacement"), i)
        if row["time_raw"] == "":
            row["time_raw"] = container_index
            row["time_s"] = container_index
        points.append(row)
    return points


def discover_inputs(inputs: Iterable[Path]) -> list[Path]:
    discovered: list[Path] = []
    for input_path in inputs:
        if input_path.is_dir():
            discovered.extend(sorted(input_path.rglob("*.dat")))
            discovered.extend(sorted(input_path.rglob("*.json")))
        elif input_path.is_file():
            discovered.append(input_path)
        else:
            raise FileNotFoundError(f"input does not exist: {input_path}")
    return sorted(dict.fromkeys(discovered))


def extract_file(path: Path) -> ExtractionResult:
    suffix = path.suffix.lower()
    if suffix == ".dat":
        return parse_lot_tese_dat(path)
    if suffix == ".json":
        return parse_lot_apb_v5_json(path)
    return ExtractionResult(str(path), "unsupported", [], [f"unsupported suffix: {suffix}"])


def _has_value(points: list[dict[str, Any]], field: str) -> bool:
    return any(row.get(field) not in ("", None) for row in points)


def build_summary(result: ExtractionResult) -> dict[str, Any]:
    points = result.points
    has_pressure_json = any(row.get("source_kind") == "LOT_APB_v5_JSON" for row in points)
    has_pressure_pa = any(
        row.get(field) not in ("", None)
        for row in points
        for field in ("pressure_start_Pa", "pressure_final_Pa", "pressure_diff_Pa", "pressure_apb_Pa")
    )
    if has_pressure_pa:
        readiness = "pressure_only"
    elif _has_value(points, "dP") or _has_value(points, "dV_leakoff"):
        readiness = "limited_indirect"
    else:
        readiness = "not_supported"

    return {
        "source_file": result.source_file,
        "source_kind": result.source_kind,
        "n_records": len(points),
        "has_time": _has_value(points, "time_raw"),
        "has_layer": _has_value(points, "layer"),
        "has_dP": _has_value(points, "dP"),
        "has_dV_leakoff": _has_value(points, "dV_leakoff"),
        "has_pressure_json": has_pressure_json,
        "has_pressure_Pa": has_pressure_pa,
        "has_sigmaTheta": False,
        "has_pw": False,
        "has_margin": False,
        "has_opened": False,
        "comparison_readiness": readiness,
        "notes": " | ".join(result.notes),
    }


def write_outputs(results: list[ExtractionResult], inputs: list[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_points = [point for result in results for point in result.points]
    summaries = [build_summary(result) for result in results]

    with (output_dir / "legacy_points.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=POINT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_points)

    with (output_dir / "legacy_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)

    metadata = {
        "generated_by": "lot-salt-suite",
        "phase": "10.12B",
        "inputs": [str(path) for path in inputs],
        "outputs": {
            "legacy_points_csv": "legacy_points.csv",
            "legacy_summary_csv": "legacy_summary.csv",
        },
        "field_groups": FIELD_GROUPS,
        "caveats": CAVEATS,
    }
    (output_dir / "legacy_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run(inputs: Iterable[Path], output_dir: Path) -> tuple[list[Path], list[ExtractionResult]]:
    discovered = discover_inputs(inputs)
    results = [extract_file(path) for path in discovered]
    write_outputs(results, discovered, output_dir)
    return discovered, results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract read-only LOT_Tese/LOT_APB_v5 legacy outputs for future comparison."
    )
    parser.add_argument("--input", nargs="+", required=True, help="Legacy output file(s) or directory.")
    parser.add_argument("--output-dir", required=True, help="Directory for normalized CSV/JSON outputs.")
    args = parser.parse_args()

    inputs = [Path(item) for item in args.input]
    output_dir = Path(args.output_dir)
    discovered, results = run(inputs, output_dir)
    n_records = sum(len(result.points) for result in results)
    print(f"processed_inputs={len(discovered)}")
    print(f"legacy_records={n_records}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
