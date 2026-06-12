#!/usr/bin/env python3
"""Audit BUZ29 pressure and opening evidence for the PennyShaped track."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PHASE = "11.9E"
CASE_ID = "BUZ29-VISCO-first-well"
TRACK = "PENNY_SHAPED"


@dataclass(frozen=True)
class LegacyDatSummary:
    path: str
    exists: bool
    has_time: bool = False
    n_time_points: int = 0
    time_min: float | None = None
    time_max: float | None = None
    has_dp: bool = False
    dp_blocks: int = 0
    has_dv_leakoff: bool = False
    dv_leakoff_blocks: int = 0
    first_positive_dv_leakoff_time_min: float | None = None
    opening_time_min: float | None = None
    elapsed_runtime_s: float | None = None


def default_sources() -> dict[str, Path]:
    return {
        "buz29_source": Path("legance/LOT_Tese/BUZ29-VISCO-first-well.cpp"),
        "legacy_penny_dat": Path("legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat"),
        "pressure_visualizer": Path("legance/LOT_Tese/PressureDataVisualizer29D-RAA.py"),
        "doc_57": Path("docs/57_buz29_visco_first_well_audit.md"),
        "doc_58": Path("docs/58_non_pkn_model_roadmap.md"),
        "doc_68": Path("docs/68_buz29_penny_candidate_readiness.md"),
        "doc_70": Path("docs/70_buz29_penny_evidence_audit.md"),
        "doc_71": Path("docs/71_buz29_penny_readiness_update.md"),
        "tool_11_9c": Path("tools/audit_phase11_9c_buz29_penny_evidence.py"),
        "tool_11_9d": Path("tools/update_phase11_9d_buz29_penny_readiness.py"),
    }


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _numbers(line: str) -> list[float]:
    values: list[float] = []
    for token in line.strip().split():
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def summarize_legacy_dat(path: Path) -> LegacyDatSummary:
    if not path.exists():
        return LegacyDatSummary(path=str(path), exists=False)

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    times: list[float] = []
    dp_blocks = 0
    dv_blocks = 0
    first_positive_dv_index: int | None = None
    opening_time: float | None = None
    elapsed_runtime: float | None = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        lower = line.lower()
        if lower == "time" and i + 1 < len(lines):
            times = _numbers(lines[i + 1])
            i += 2
            continue

        if line == "dP":
            dp_blocks += 1
            i += 1
            continue

        if line == "dV_leakoff":
            dv_blocks += 1
            rows = 0
            if i + 1 < len(lines):
                maybe_rows = _numbers(lines[i + 1])
                if maybe_rows:
                    rows = int(maybe_rows[0])
            for row_index in range(rows):
                value_line_index = i + 2 + row_index
                if value_line_index >= len(lines):
                    break
                for idx, value in enumerate(_numbers(lines[value_line_index])):
                    if value > 0.0 and first_positive_dv_index is None:
                        first_positive_dv_index = idx
            i += max(2 + rows, 1)
            continue

        if lower.startswith("elapsed time"):
            match = re.search(r"([-+]?\d+(?:\.\d+)?)", line)
            if match:
                elapsed_runtime = float(match.group(1))

        if "momento da quebra" in lower:
            match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*$", line)
            if match:
                opening_time = float(match.group(1))

        i += 1

    first_positive_time = None
    if first_positive_dv_index is not None and first_positive_dv_index < len(times):
        first_positive_time = times[first_positive_dv_index]

    return LegacyDatSummary(
        path=str(path),
        exists=True,
        has_time=bool(times),
        n_time_points=len(times),
        time_min=min(times) if times else None,
        time_max=max(times) if times else None,
        has_dp=dp_blocks > 0,
        dp_blocks=dp_blocks,
        has_dv_leakoff=dv_blocks > 0,
        dv_leakoff_blocks=dv_blocks,
        first_positive_dv_leakoff_time_min=first_positive_time,
        opening_time_min=opening_time,
        elapsed_runtime_s=elapsed_runtime,
    )


def _source_item(name: str, path: Path, note: str) -> dict[str, Any]:
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "note": note,
    }


def _evidence_item(
    kind: str,
    status: str,
    source: str,
    consumable: bool,
    note: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "status": status,
        "source": source,
        "consumable": consumable,
        "note": note,
        "fields": fields or {},
    }


def audit_sources(
    sources: dict[str, Path] | None = None,
    *,
    requires_legacy_instrumentation: bool = False,
) -> dict[str, Any]:
    sources = sources or default_sources()
    dat = summarize_legacy_dat(sources["legacy_penny_dat"])
    source_text = _read(sources["buz29_source"])
    visualizer_text = _read(sources["pressure_visualizer"])

    sources_checked = [
        _source_item("BUZ29 source", sources["buz29_source"], "Primary legacy case source, read-only."),
        _source_item("BUZ29 PennyShaped .dat", sources["legacy_penny_dat"], "Legacy output containing Time, dP, dV_leakoff and tail metadata."),
        _source_item("BUZ29 pressure visualizer", sources["pressure_visualizer"], "Legacy script documents pressure plotting and dP-to-psi conversion."),
        _source_item("11.6A audit", sources["doc_57"], "Previous BUZ29 first-well audit."),
        _source_item("11.6B roadmap", sources["doc_58"], "Non-PKN model roadmap."),
        _source_item("11.9B readiness", sources["doc_68"], "Previous BUZ29 PennyShaped readiness."),
        _source_item("11.9C evidence audit", sources["doc_70"], "Previous evidence audit."),
        _source_item("11.9D readiness update", sources["doc_71"], "Current readiness gate before 11.9E."),
        _source_item("11.9C tool", sources["tool_11_9c"], "Previous evidence audit tool."),
        _source_item("11.9D tool", sources["tool_11_9d"], "Previous readiness update tool."),
    ]

    initial_pressure_match = re.search(r'initPressure\s*=\s*"([^"]+)"', source_text)
    initial_pressure_psi = float(initial_pressure_match.group(1)) if initial_pressure_match else None
    pressure_conversion_known = "0.000145038" in visualizer_text

    if requires_legacy_instrumentation:
        pressure_status = "PRESSURE_HISTORY_INCONCLUSIVE"
        opening_status = "OPENING_TIME_INCONCLUSIVE"
    elif dat.exists and dat.has_time and dat.has_dp and pressure_conversion_known:
        pressure_status = "PRESSURE_HISTORY_FOUND_CONSUMABLE"
    elif dat.exists and dat.has_dp:
        pressure_status = "PRESSURE_HISTORY_PARTIAL"
    elif dat.exists:
        pressure_status = "PRESSURE_HISTORY_FOUND_NOT_CONSUMABLE"
    else:
        pressure_status = "PRESSURE_HISTORY_MISSING"

    if requires_legacy_instrumentation:
        opening_status = "OPENING_TIME_INCONCLUSIVE"
    elif dat.exists and dat.opening_time_min is not None:
        opening_status = "OPENING_TIME_FOUND_CONSUMABLE"
    elif dat.exists and dat.has_dv_leakoff and dat.first_positive_dv_leakoff_time_min is not None:
        opening_status = "OPENING_TIME_PARTIAL"
    elif dat.exists:
        opening_status = "OPENING_TIME_FOUND_NOT_CONSUMABLE"
    else:
        opening_status = "OPENING_TIME_MISSING"

    pressure_consumable = pressure_status == "PRESSURE_HISTORY_FOUND_CONSUMABLE"
    opening_consumable = opening_status == "OPENING_TIME_FOUND_CONSUMABLE"

    evidence_items = [
        _evidence_item(
            "pressure_history",
            pressure_status,
            dat.path,
            pressure_consumable,
            "The .dat file provides Time and dP blocks; the visualizer applies dP*0.000145038 plus the BUZ29 source initPressure=70 psi.",
            {
                "n_time_points": dat.n_time_points,
                "time_unit": "min",
                "time_min": dat.time_min,
                "time_max": dat.time_max,
                "dp_blocks": dat.dp_blocks,
                "initial_pressure_psi": initial_pressure_psi,
                "pressure_conversion": "dP_Pa * 0.000145038 -> psi",
            },
        ),
        _evidence_item(
            "opening_time",
            opening_status,
            dat.path,
            opening_consumable,
            "The .dat tail records 'Momento da quebra' from APB1da::checkPwAndSaveTime; this is a traceable opening/break time in the same minute scale as Time.",
            {
                "opening_time_min": dat.opening_time_min,
                "opening_time_s": dat.opening_time_min * 60.0 if dat.opening_time_min is not None else None,
                "first_positive_dv_leakoff_time_min": dat.first_positive_dv_leakoff_time_min,
                "elapsed_runtime_s": dat.elapsed_runtime_s,
            },
        ),
        _evidence_item(
            "legacy_dv_leakoff",
            "DV_LEAKOFF_SERIES_FOUND" if dat.has_dv_leakoff else "DV_LEAKOFF_SERIES_MISSING",
            dat.path,
            False,
            "dV_leakoff helps corroborate post-opening behavior, but it is not by itself the direct opening criterion.",
            {
                "dv_leakoff_blocks": dat.dv_leakoff_blocks,
                "first_positive_dv_leakoff_time_min": dat.first_positive_dv_leakoff_time_min,
            },
        ),
    ]

    blocking_gaps: list[str] = []
    if not pressure_consumable:
        blocking_gaps.append("pressure_history")
    if not opening_consumable:
        blocking_gaps.append("opening_time")
    if requires_legacy_instrumentation:
        blocking_gaps.append("requires_controlled_legacy_instrumentation")

    if requires_legacy_instrumentation:
        classification = "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_BLOCKED"
        can_reopen = False
        next_phase = "PHASE12_0_CONTROLLED_LEGACY_TRACE_INSTRUMENTATION_PLAN"
    elif pressure_consumable and opening_consumable:
        classification = "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE"
        can_reopen = True
        next_phase = "PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING"
    elif pressure_consumable or opening_consumable:
        classification = "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_PARTIAL"
        can_reopen = False
        next_phase = "PHASE11_9F_DOCUMENT_REMAINING_BUZ29_EVIDENCE_GAPS"
    elif pressure_status == "PRESSURE_HISTORY_MISSING" and opening_status == "OPENING_TIME_MISSING":
        classification = "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_MISSING"
        can_reopen = False
        next_phase = "PHASE12_0_BUZ29_EXTERNAL_DATA_OR_CONTROLLED_LEGACY_INSTRUMENTATION_PLAN"
    else:
        classification = "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_INCONCLUSIVE"
        can_reopen = False
        next_phase = "PHASE11_9F_DOCUMENT_REMAINING_BUZ29_EVIDENCE_GAPS"

    return {
        "phase": PHASE,
        "case": CASE_ID,
        "track": TRACK,
        "pressure_history_status": pressure_status,
        "opening_time_status": opening_status,
        "pressure_history_consumable": pressure_consumable,
        "opening_time_consumable": opening_consumable,
        "sources_checked": sources_checked,
        "evidence_items": evidence_items,
        "legacy_dat_summary": dat.__dict__,
        "blocking_gaps": blocking_gaps,
        "classification": classification,
        "can_reopen_11_10A_gate": can_reopen,
        "recommended_next_phase": next_phase,
        "buz29_candidate_yaml_created": False,
        "buz29_simulation_executed": False,
        "physical_validation": False,
        "caveats": [
            "Phase 11.9E does not execute BUZ29-PENNY, does not create a candidate YAML and does not validate BUZ29 physically.",
            "The pressure history is evidence for a future readiness re-evaluation, not an approved runtime input by itself.",
            "The opening time comes from an existing legacy output tail and must be consumed by a future readiness phase before 11.10A can start.",
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Fase 11.9E — evidência BUZ29 de pressão e abertura",
        "",
        "## Resumo executivo",
        "",
        "A 11.9E não executa BUZ29-PENNY, não cria YAML candidato e não valida BUZ29. Ela apenas audita se existem histórico de pressão e evidência de abertura consumíveis para reavaliar o gate.",
        "",
        f"- classification: `{result['classification']}`",
        f"- pressure_history_status: `{result['pressure_history_status']}`",
        f"- opening_time_status: `{result['opening_time_status']}`",
        f"- can_reopen_11_10A_gate: `{str(result['can_reopen_11_10A_gate']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Fontes analisadas",
        "",
        "| Fonte | Existe? | Observação |",
        "|---|---:|---|",
    ]
    for item in result["sources_checked"]:
        lines.append(f"| `{item['path']}` | `{str(item['exists']).lower()}` | {item['note']} |")

    lines.extend(
        [
            "",
            "## Evidências",
            "",
            "| Tipo | Status | Consumível? | Fonte | Observação |",
            "|---|---|---:|---|---|",
        ]
    )
    for item in result["evidence_items"]:
        note = str(item["note"]).replace("|", "/")
        lines.append(
            f"| `{item['kind']}` | `{item['status']}` | `{str(item['consumable']).lower()}` | `{item['source']}` | {note} |"
        )

    summary = result["legacy_dat_summary"]
    lines.extend(
        [
            "",
            "## Campos consumíveis",
            "",
            f"- `pressure_history`: `{str(result['pressure_history_consumable']).lower()}`.",
            f"- `opening_time`: `{str(result['opening_time_consumable']).lower()}`.",
            f"- `time_min/time_max`: `{summary['time_min']}` / `{summary['time_max']}` min.",
            f"- `opening_time_min`: `{summary['opening_time_min']}`.",
            f"- `first_positive_dV_leakoff_time_min`: `{summary['first_positive_dv_leakoff_time_min']}`.",
            "",
            "## Gaps bloqueantes",
            "",
        ]
    )
    lines.extend(f"- `{gap}`" for gap in result["blocking_gaps"] or ["none"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit BUZ29 pressure and opening evidence for the PennyShaped diagnostic track."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = audit_sources()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"PRESSURE_HISTORY_STATUS={result['pressure_history_status']}")
    print(f"OPENING_TIME_STATUS={result['opening_time_status']}")
    print(f"CLASSIFICATION={result['classification']}")
    print(f"CAN_REOPEN_11_10A_GATE={str(result['can_reopen_11_10A_gate']).lower()}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
