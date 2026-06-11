#!/usr/bin/env python3
"""Audit BUZ29-VISCO-first-well readiness for a modern-refined LOT/PKN route."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PHASE = "11.6A"
FIRST_WELL_NAME = "BUZ29-VISCO-first-well.cpp"


@dataclass(frozen=True)
class Candidate:
    path: str
    kind: str
    model_hint: str
    status: str
    reason: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="replace")


def active_line(line: str) -> str:
    return line.split("//", 1)[0].strip()


def active_contains(line: str, token: str) -> bool:
    return token.lower() in active_line(line).lower()


def detect_active_model(text: str) -> str:
    active_models: list[str] = []
    for line in text.splitlines():
        active = active_line(line).lower()
        for model in ("pkn", "penny-shaped", "circular", "elliptical"):
            if f'"{model}"' in active:
                active_models.append(model)
    if "pkn" in active_models:
        return "PKN"
    if "penny-shaped" in active_models:
        return "PENNY_SHAPED"
    if "circular" in active_models:
        return "KGD_CIRCULAR"
    if "elliptical" in active_models:
        return "KGD_ELLIPTICAL"
    if re.search(r"\bPKN\b", text, flags=re.IGNORECASE):
        return "PKN_COMMENT_OR_OUTPUT_ONLY"
    return "UNKNOWN"


def extract_first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_line(pattern: str, text: str) -> str | None:
    for line in text.splitlines():
        if re.search(pattern, line, flags=re.IGNORECASE) and active_line(line):
            return line.strip()
    return None


def extract_parameters(text: str) -> dict[str, dict[str, str | None]]:
    flat = text.replace("\n", " ")
    return {
        "active_fracture_model": {
            "value": detect_active_model(text),
            "unit": None,
            "status": "EXTRACTED",
            "source": extract_line(r"setLeakoffProps", text),
        },
        "commented_pkn_evidence": {
            "value": "present" if re.search(r"//.*setLeakoffProps.*pkn", text, flags=re.IGNORECASE) else "absent",
            "unit": None,
            "status": "EXTRACTED",
            "source": extract_first(r"(//.*setLeakoffProps[^\n]*pkn[^\n]*)", text),
        },
        "fluid": {
            "value": extract_first(r"setPFluid\(([^;]+)\);", text),
            "unit": "ppg, 1/degC, 1/Pa",
            "status": "EXTRACTED" if "setPFluid" in text else "NOT_FOUND",
            "source": extract_line(r"setPFluid", text),
        },
        "simulation": {
            "value": extract_first(r"APB1da\s+simulation\(([^;]+)\);", text),
            "unit": "legacy constructor tuple",
            "status": "EXTRACTED" if "APB1da simulation" in text else "NOT_FOUND",
            "source": extract_line(r"APB1da\s+simulation", text),
        },
        "layers": {
            "value": extract_first(r"MatrixXd\s+mdepths\(([^;]+)\);", text),
            "unit": "legacy matrix declaration",
            "status": "EXTRACTED" if "MatrixXd mdepths" in text else "NOT_FOUND",
            "source": extract_line(r"MatrixXd\s+mdepths", text),
        },
        "depth_interval": {
            "value": extract_first(r"new\s+Temperature\(([^;]+)\);", text),
            "unit": "m and legacy temperature vectors",
            "status": "EXTRACTED" if "new Temperature" in text else "NOT_FOUND",
            "source": extract_line(r"new Temperature", text),
        },
        "output": {
            "value": extract_first(r'filePath\s*=\s*"([^"]+)"', text),
            "unit": None,
            "status": "EXTRACTED" if "filePath" in text else "NOT_FOUND",
            "source": extract_line(r"filePath\s*=", text),
        },
        "rock_creep_rate_units": {
            "value": "contains * 60 or / 60 conversions" if re.search(r"e[-+]?\d+\s*[*\/]\s*60", text, flags=re.IGNORECASE) else "not detected",
            "unit": "legacy minutes convention",
            "status": "EXTRACTED",
            "source": "Rock entries include minute/hour conversion comments and factors.",
        },
        "raw_mdepths": {
            "value": extract_first(r"mdepths\s*<<(.*?);", flat),
            "unit": "m",
            "status": "EXTRACTED" if "mdepths <<" in text else "NOT_FOUND",
            "source": "MatrixXd mdepths block",
        },
    }


def candidate_model_from_text(path: Path) -> tuple[str, str]:
    text = read_text(path)
    model = detect_active_model(text)
    if model == "PKN":
        return model, "Contains active PKN fracture model."
    if model in {"PENNY_SHAPED", "KGD_CIRCULAR", "KGD_ELLIPTICAL"}:
        return model, "Contains active non-PKN fracture model."
    if "pkn" in path.name.lower():
        return "PKN_OUTPUT_OR_NAME_ONLY", "PKN appears in the artifact name but not as an audited active source."
    return model, "No active LOT fracture model was detected by the read-only scan."


def find_candidates(root: Path) -> list[Candidate]:
    if not root.exists():
        return []
    candidates: list[Candidate] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        lower_name = path.name.lower()
        if not any(token in lower_name for token in ("buz29", "29d")):
            continue
        relative = path.as_posix()
        if path.suffix.lower() in {".cpp", ".h", ".hpp"}:
            model, reason = candidate_model_from_text(path)
            status = "SOURCE_AUDITED"
            if path.name == FIRST_WELL_NAME:
                status = "PRIMARY_FIRST_WELL_SOURCE"
            candidates.append(Candidate(relative, "source", model, status, reason))
        elif path.suffix.lower() in {".dat", ".csv", ".json"}:
            model = "PKN_OUTPUT_ONLY" if "pkn" in lower_name else "OUTPUT_ONLY"
            candidates.append(Candidate(relative, "output", model, "OUTPUT_ONLY", "Output artifact; insufficient for modern YAML by itself."))
        else:
            candidates.append(Candidate(relative, "artifact", "REFERENCE_ONLY", "REFERENCE_ONLY", "Non-source reference artifact."))
    return candidates


def locate_first_well(root: Path) -> Path | None:
    direct = root / FIRST_WELL_NAME
    if direct.exists():
        return direct
    matches = sorted(root.rglob(FIRST_WELL_NAME)) if root.exists() else []
    return matches[0] if matches else None


def classify(first_well: Path | None, parameters: dict[str, dict[str, str | None]]) -> dict[str, object]:
    if first_well is None:
        return {
            "source_status": "BUZ29_VISCO_FIRST_WELL_SOURCE_NOT_FOUND",
            "primary_classification": "BUZ29_VISCO_FIRST_WELL_BLOCKED_SOURCE_NOT_FOUND",
            "future_yaml_readiness": "BUZ29_VISCO_FIRST_WELL_NOT_READY",
            "recommended_next_phase": "PHASE11_6B_NON_PKN_ROADMAP",
            "missing_fields": ["primary_source"],
        }
    active_model = parameters["active_fracture_model"]["value"]
    missing_fields = [
        key
        for key in ("fluid", "simulation", "layers", "depth_interval", "output")
        if parameters.get(key, {}).get("status") != "EXTRACTED"
    ]
    if active_model != "PKN":
        return {
            "source_status": "BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND",
            "primary_classification": "BUZ29_VISCO_FIRST_WELL_NOT_PKN",
            "future_yaml_readiness": "BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY",
            "recommended_next_phase": "PHASE11_6B_NON_PKN_ROADMAP",
            "missing_fields": missing_fields,
        }
    if missing_fields:
        return {
            "source_status": "BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND",
            "primary_classification": "BUZ29_VISCO_FIRST_WELL_MISSING_CRITICAL_FIELDS",
            "future_yaml_readiness": "BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY",
            "recommended_next_phase": "PHASE11_6B_NON_PKN_ROADMAP",
            "missing_fields": missing_fields,
        }
    return {
        "source_status": "BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND",
        "primary_classification": "BUZ29_VISCO_FIRST_WELL_PKN_READY_FOR_FUTURE_YAML",
        "future_yaml_readiness": "BUZ29_VISCO_FIRST_WELL_READY_FOR_FUTURE_MODERN_YAML",
        "recommended_next_phase": "PHASE11_6B_NON_PKN_ROADMAP",
        "missing_fields": [],
    }


def audit(root: Path) -> dict[str, object]:
    first_well = locate_first_well(root)
    parameters = extract_parameters(read_text(first_well)) if first_well else {}
    classification = classify(first_well, parameters)
    candidates = find_candidates(root)
    return {
        "phase": PHASE,
        "case": "BUZ29-VISCO-first-well",
        "source": "READ_ONLY_LEGACY_SCAN",
        "primary_source": first_well.as_posix() if first_well else None,
        "parameters": parameters,
        "candidates": [asdict(candidate) for candidate in candidates],
        "required_models": [
            "PENNY_SHAPED_OR_NON_PKN_RUNTIME",
            "KGD_CIRCULAR_IF_OTHER_BUZ29_VARIANTS_ARE_SELECTED",
            "ZAMORA_OR_COMPOSITIONAL_FLUID_IF_ZAMORA_VARIANTS_ARE_SELECTED",
        ],
        "modern_pkn_ready": classification["primary_classification"] == "BUZ29_VISCO_FIRST_WELL_PKN_READY_FOR_FUTURE_YAML",
        "caveats": [
            "Read-only audit; no legance files were modified.",
            "The active first-well source uses penny-shaped LOT, while the PKN line is commented.",
            "PKN output artifacts do not establish source-level PKN readiness.",
            "No modern YAML is created and no physical equivalence is claimed.",
        ],
        **classification,
    }


def write_markdown(path: Path, summary: dict[str, object]) -> None:
    lines = [
        "# Phase 11.6A BUZ29 VISCO first-well audit",
        "",
        "## Summary",
        "",
        f"- `source_status`: `{summary['source_status']}`",
        f"- `primary_classification`: `{summary['primary_classification']}`",
        f"- `future_yaml_readiness`: `{summary['future_yaml_readiness']}`",
        f"- `recommended_next_phase`: `{summary['recommended_next_phase']}`",
        f"- `modern_pkn_ready`: `{str(summary['modern_pkn_ready']).lower()}`",
        "",
        "## Primary Source",
        "",
        f"`{summary['primary_source']}`",
        "",
        "## Parameters",
        "",
        "| Field | Value | Unit | Status | Source |",
        "|---|---|---|---|---|",
    ]
    for key, info in dict(summary.get("parameters", {})).items():
        value = str(info.get("value") or "").replace("|", "\\|")
        source = str(info.get("source") or "").replace("|", "\\|")
        lines.append(f"| {key} | `{value}` | {info.get('unit') or ''} | {info.get('status')} | `{source}` |")
    lines.extend(["", "## Candidates", "", "| Path | Kind | Model | Status |", "|---|---|---|---|"])
    for candidate in list(summary.get("candidates", [])):
        lines.append(f"| `{candidate['path']}` | {candidate['kind']} | {candidate['model_hint']} | {candidate['status']} |")
    lines.extend(["", "## Caveats", ""])
    for caveat in list(summary.get("caveats", [])):
        lines.append(f"- {caveat}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, default=Path("legance/LOT_Tese"))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = audit(args.legacy_root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, summary)
    print(f"PHASE={summary['phase']}")
    print(f"SOURCE_STATUS={summary['source_status']}")
    print(f"PRIMARY_CLASSIFICATION={summary['primary_classification']}")
    print(f"NEXT_PHASE={summary['recommended_next_phase']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
