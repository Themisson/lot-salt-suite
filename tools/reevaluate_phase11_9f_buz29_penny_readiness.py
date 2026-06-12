#!/usr/bin/env python3
"""Reevaluate BUZ29 PennyShaped readiness after pressure/opening evidence."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.audit_phase11_9e_buz29_pressure_opening_evidence import audit_sources


PHASE = "11.9F"
CASE_ID = "BUZ29-VISCO-first-well"
TRACK = "PENNY_SHAPED"

AXISYMMETRIC_CAVEAT = "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED"

READINESS_DIAGNOSTIC_SAFE = "BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE"
GATE_DIAGNOSTIC_SAFE = "BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A"
NEXT_PHASE_11_10A = "PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE"


@dataclass(frozen=True)
class ReadinessInputs:
    previous_readiness: str = "BUZ29_PENNY_CANDIDATE_PARTIAL"
    pressure_history_status: str = "PRESSURE_HISTORY_FOUND_CONSUMABLE"
    opening_time_status: str = "OPENING_TIME_FOUND_CONSUMABLE"
    pressure_opening_evidence_classification: str = (
        "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE"
    )
    pressure_history_consumable: bool = True
    opening_time_consumable: bool = True
    adapter_ready_status: str = "ADAPTER_READY_PARTIAL_DIAGNOSTIC_SAFE"
    severe_semantic_ambiguity: bool = False
    penny_math_blocks_diagnostic: bool = False
    source_output: str = "legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat"
    legacy_time_points: int | None = 131
    legacy_time_min: float | None = 0.0
    legacy_time_max: float | None = 13.0
    legacy_opening_time_min: float | None = 10.4
    evidence_items: list[dict[str, Any]] = field(default_factory=list)


def inputs_from_phase11_9e() -> ReadinessInputs:
    evidence = audit_sources()
    summary = evidence.get("legacy_dat_summary", {})
    return ReadinessInputs(
        pressure_history_status=evidence["pressure_history_status"],
        opening_time_status=evidence["opening_time_status"],
        pressure_opening_evidence_classification=evidence["classification"],
        pressure_history_consumable=bool(evidence["pressure_history_consumable"]),
        opening_time_consumable=bool(evidence["opening_time_consumable"]),
        source_output=str(summary.get("path") or ""),
        legacy_time_points=summary.get("n_time_points"),
        legacy_time_min=summary.get("time_min"),
        legacy_time_max=summary.get("time_max"),
        legacy_opening_time_min=summary.get("opening_time_min"),
        evidence_items=list(evidence.get("evidence_items", [])),
    )


def reevaluate_readiness(inputs: ReadinessInputs) -> dict[str, Any]:
    pressure_and_opening_consumable = (
        inputs.pressure_history_consumable
        and inputs.opening_time_consumable
        and inputs.pressure_history_status == "PRESSURE_HISTORY_FOUND_CONSUMABLE"
        and inputs.opening_time_status == "OPENING_TIME_FOUND_CONSUMABLE"
        and inputs.pressure_opening_evidence_classification
        == "BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE"
    )

    blocking_gaps: list[str] = []
    required_caveats = [
        AXISYMMETRIC_CAVEAT,
        "BUZ29_DIAGNOSTIC_ONLY_NO_PHYSICAL_VALIDATION",
        "BUZ29_PENNY_YAML_NOT_CREATED_IN_11_9F",
        "BUZ29_SIMULATION_NOT_EXECUTED_IN_11_9F",
        "LEGACY_EQUIVALENCE_NOT_DECLARED",
        "FRACTURE_VOLUME_PROXY_NOT_TOTAL_2PI_VOLUME",
    ]
    nonblocking_gaps = [
        "sigmaTheta BUZ29 is not exported directly in the legacy .dat output.",
        "pw, margin and opened are not exported directly in the legacy .dat output.",
        "The 11.10A route must remain preparation/diagnostic only.",
        "PennyShaped fracture volume/proxy needs a future mathematical audit before strong physical interpretation.",
    ]

    if not inputs.pressure_history_consumable:
        blocking_gaps.append("pressure_history")
    if not inputs.opening_time_consumable:
        blocking_gaps.append("opening_time")

    if inputs.severe_semantic_ambiguity:
        updated_readiness = "BUZ29_PENNY_CANDIDATE_INCONCLUSIVE"
        can_start = False
        gate = "BUZ29_PENNY_INCONCLUSIVE_DO_NOT_START_11_10A"
        recommended_next_phase = "PHASE11_9G_RESOLVE_BUZ29_PRESSURE_OPENING_SEMANTICS"
        blocking_gaps.append("pressure_opening_semantics")
    elif inputs.penny_math_blocks_diagnostic:
        updated_readiness = "BUZ29_PENNY_CANDIDATE_PARTIAL"
        can_start = False
        gate = "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
        recommended_next_phase = "PHASE11_8E_AUDIT_PENNY_SHAPED_MODEL_MATH"
        blocking_gaps.append("penny_shaped_math_interpretation")
    elif pressure_and_opening_consumable and inputs.adapter_ready_status in {
        "ADAPTER_READY_SUFFICIENT",
        "ADAPTER_READY_PARTIAL_DIAGNOSTIC_SAFE",
    }:
        updated_readiness = READINESS_DIAGNOSTIC_SAFE
        can_start = True
        gate = GATE_DIAGNOSTIC_SAFE
        recommended_next_phase = NEXT_PHASE_11_10A
    elif pressure_and_opening_consumable:
        updated_readiness = "BUZ29_PENNY_CANDIDATE_PARTIAL"
        can_start = False
        gate = "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
        recommended_next_phase = "PHASE11_9G_COMPLETE_BUZ29_ADAPTER_READY_INPUTS"
        blocking_gaps.append("adapter_ready_inputs")
    elif blocking_gaps:
        updated_readiness = "BUZ29_PENNY_CANDIDATE_PARTIAL"
        can_start = False
        gate = "BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A"
        recommended_next_phase = "PHASE11_9G_COMPLETE_BUZ29_ADAPTER_READY_INPUTS"
    else:
        updated_readiness = "BUZ29_PENNY_CANDIDATE_BLOCKED"
        can_start = False
        gate = "BUZ29_PENNY_BLOCKED_DO_NOT_START_11_10A"
        recommended_next_phase = "PHASE11_9G_RESOLVE_BUZ29_READINESS_BLOCKER"

    return {
        "phase": PHASE,
        "case": CASE_ID,
        "track": TRACK,
        "previous_readiness": inputs.previous_readiness,
        "pressure_history_status": inputs.pressure_history_status,
        "opening_time_status": inputs.opening_time_status,
        "pressure_opening_evidence_classification": (
            inputs.pressure_opening_evidence_classification
        ),
        "axisymmetric_interpretation": AXISYMMETRIC_CAVEAT,
        "adapter_ready_status": inputs.adapter_ready_status,
        "updated_readiness": updated_readiness,
        "can_start_11_10A": can_start,
        "gate": gate,
        "blocking_gaps": blocking_gaps,
        "nonblocking_gaps": nonblocking_gaps,
        "required_caveats": required_caveats,
        "recommended_next_phase": recommended_next_phase,
        "source_output": inputs.source_output,
        "legacy_time_points": inputs.legacy_time_points,
        "legacy_time_min": inputs.legacy_time_min,
        "legacy_time_max": inputs.legacy_time_max,
        "legacy_opening_time_min": inputs.legacy_opening_time_min,
        "legacy_opening_time_s": (
            inputs.legacy_opening_time_min * 60.0
            if inputs.legacy_opening_time_min is not None
            else None
        ),
        "evidence_items": inputs.evidence_items,
        "buz29_candidate_yaml_created": False,
        "study_id_created": False,
        "buz29_simulation_executed": False,
        "physical_validation": False,
        "legacy_equivalence": False,
        "lot_pkn_changed": False,
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Fase 11.9F — readiness BUZ29-PENNY após evidência de pressão e abertura",
        "",
        "## Resumo executivo",
        "",
        "A 11.9F não executa BUZ29-PENNY, não cria YAML candidato e não valida BUZ29. Ela apenas reavalia o readiness após a evidência consumível de pressão e abertura encontrada na 11.9E.",
        "",
        f"- previous_readiness: `{result['previous_readiness']}`",
        f"- updated_readiness: `{result['updated_readiness']}`",
        f"- gate: `{result['gate']}`",
        f"- can_start_11_10A: `{str(result['can_start_11_10A']).lower()}`",
        f"- recommended_next_phase: `{result['recommended_next_phase']}`",
        "",
        "## Evidência 11.9E considerada",
        "",
        f"- `pressure_history_status`: `{result['pressure_history_status']}`.",
        f"- `opening_time_status`: `{result['opening_time_status']}`.",
        f"- `classification`: `{result['pressure_opening_evidence_classification']}`.",
        f"- fonte: `{result['source_output']}`.",
        f"- faixa temporal: `{result['legacy_time_points']}` pontos, `{result['legacy_time_min']}` a `{result['legacy_time_max']}` min.",
        f"- momento da quebra: `{result['legacy_opening_time_min']}` min (`{result['legacy_opening_time_s']}` s).",
        "",
        "## Caveat axissimétrico 1 rad",
        "",
        "O modelo PennyShaped usado no projeto deve ser interpretado no contexto da formulação axissimétrica de 1 rad. Portanto, qualquer volume/proxy de fratura não deve ser automaticamente tratado como volume circular completo em 2π sem auditoria matemática específica.",
        "",
        f"Classificação: `{result['axisymmetric_interpretation']}`.",
        "",
        "## Campos ainda ausentes ou não diretos",
        "",
    ]
    lines.extend(f"- {item}" for item in result["nonblocking_gaps"])
    lines.extend(
        [
            "",
            "## Decisão",
            "",
            f"O readiness atualizado é `{result['updated_readiness']}`. O gate para a próxima fase é `{result['gate']}`.",
            "",
            "Essa abertura de gate autoriza apenas a preparação da rota diagnóstica 11.10A. Ela não autoriza validação física, equivalência com o legado, criação de rota runtime oficial ou interpretação de volume total em 2π.",
            "",
            "## Gaps bloqueantes",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in result["blocking_gaps"] or ["none"])
    lines.extend(["", "## Caveats obrigatórios", ""])
    lines.extend(f"- `{item}`" for item in result["required_caveats"])
    lines.extend(
        [
            "",
            "## Próxima fase recomendada",
            "",
            f"```text\n{result['recommended_next_phase']}\n```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reevaluate BUZ29 PennyShaped readiness after Phase 11.9E pressure/opening evidence."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = reevaluate_readiness(inputs_from_phase11_9e())
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(result, args.output_md)

    print(f"PHASE={result['phase']}")
    print(f"UPDATED_READINESS={result['updated_readiness']}")
    print(f"CAN_START_11_10A={str(result['can_start_11_10A']).lower()}")
    print(f"GATE={result['gate']}")
    print(f"AXISYMMETRIC_INTERPRETATION={result['axisymmetric_interpretation']}")
    print(f"RECOMMENDED_NEXT_PHASE={result['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
