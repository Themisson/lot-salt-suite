#!/usr/bin/env python3
"""Audit BUZ-29D legacy material for a future modern-refined case."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


CRITICAL_FIELDS = [
    "fracture_model",
    "simulation",
    "fluid",
    "depths",
    "layers",
    "output",
]


@dataclass(frozen=True)
class Candidate:
    path: str
    kind: str
    model: str
    status: str
    output_hint: str | None = None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="replace")


def is_active_line(line: str, token: str) -> bool:
    stripped = line.strip()
    return token in stripped and not stripped.startswith("//")


def detect_model(text: str) -> str:
    active_models = []
    for line in text.splitlines():
        for model in ["pkn", "penny-shaped", "circular", "elliptical"]:
            if is_active_line(line.lower(), f'"{model}"'):
                active_models.append(model)
    if "pkn" in active_models:
        return "PKN"
    if "penny-shaped" in active_models:
        return "PENNY_SHAPED"
    if "circular" in active_models:
        return "KGD_CIRCULAR"
    if "elliptical" in active_models:
        return "KGD_ELLIPTICAL"
    if re.search(r"\bPKN\b", text, re.IGNORECASE):
        return "PKN_OUTPUT_OR_COMMENT_ONLY"
    return "UNKNOWN"


def extract_first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_parameters(text: str) -> dict[str, dict[str, str | None]]:
    return {
        "fracture_model": {"value": detect_model(text), "unit": None, "status": "EXTRACTED"},
        "simulation": {
            "value": extract_first(r"APB1da\s+simulation\(([^;]+)\);", text),
            "unit": "legacy constructor tuple",
            "status": "EXTRACTED" if "APB1da simulation" in text else "NOT_FOUND",
        },
        "fluid": {
            "value": extract_first(r"setPFluid\(([^;]+)\);", text),
            "unit": "ppg, 1/degC, 1/Pa",
            "status": "EXTRACTED" if "setPFluid" in text else "NOT_FOUND",
        },
        "depths": {
            "value": extract_first(r"mdepths\s*<<\s*(.*?);", text.replace("\n", " ")),
            "unit": "m",
            "status": "EXTRACTED" if "mdepths" in text else "NOT_FOUND",
        },
        "layers": {
            "value": extract_first(r"Layers\*\s+layers\s*=\s*new\s+Layers\(([^;]+)\);", text.replace("\n", " ")),
            "unit": "legacy constructor tuple",
            "status": "EXTRACTED" if "new Layers" in text else "NOT_FOUND",
        },
        "output": {
            "value": extract_first(r'(?:filePath\s*=\s*|setSaveName\()"?([^";)]+)', text),
            "unit": None,
            "status": "EXTRACTED" if "setSaveName" in text or "filePath" in text else "NOT_FOUND",
        },
    }


def find_candidates(root: Path) -> list[Candidate]:
    if not root.exists():
        return []
    candidates: list[Candidate] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name.lower()
        if not any(token in name for token in ["buz29", "29d"]):
            continue
        relative = path.as_posix()
        if path.suffix.lower() in {".cpp", ".h", ".hpp"}:
            text = read_text(path)
            model = detect_model(text)
            status = "SOURCE_AUDITED"
            output_hint = extract_parameters(text)["output"]["value"]
            candidates.append(Candidate(relative, "source", model, status, output_hint))
        elif path.suffix.lower() in {".dat", ".csv", ".json"}:
            model = "PKN_OUTPUT_ONLY" if "pkn" in name else "OUTPUT_ONLY"
            candidates.append(Candidate(relative, "output", model, "OUTPUT_ONLY", None))
        else:
            candidates.append(Candidate(relative, "artifact", "UNKNOWN", "REFERENCE_ONLY", None))
    return candidates


def choose_primary_source(candidates: list[Candidate]) -> Candidate | None:
    sources = [candidate for candidate in candidates if candidate.kind == "source"]
    for candidate in sources:
        if candidate.model == "PKN":
            return candidate
    for candidate in sources:
        if candidate.model in {"PENNY_SHAPED", "KGD_CIRCULAR", "KGD_ELLIPTICAL"}:
            return candidate
    return sources[0] if sources else None


def classify(candidates: list[Candidate], parameters: dict[str, dict[str, str | None]]) -> tuple[str, str, list[str], str]:
    if not candidates:
        return "BUZ29D_SOURCE_NOT_FOUND", "NO_SOURCE", CRITICAL_FIELDS, "SEARCH_LEGACY_OR_EXTERNAL_NOTES"
    primary_model = parameters.get("fracture_model", {}).get("value")
    missing = [key for key in CRITICAL_FIELDS if parameters.get(key, {}).get("status") != "EXTRACTED"]
    if primary_model != "PKN":
        return "BUZ29D_MODERN_YAML_NOT_READY", "BUZ29D_NOT_PKN", missing, "AUDIT_PKN_OUTPUT_PROVENANCE_OR_ADD_NON_PKN_RUNTIME"
    if missing:
        return "BUZ29D_MODERN_YAML_NOT_READY", "BUZ29D_MISSING_CRITICAL_FIELDS", missing, "EXTRACT_MISSING_FIELDS_BEFORE_YAML"
    return "BUZ29D_READY_FOR_FUTURE_MODERN_REFINED_YAML", "BUZ29D_MODERN_REFINED_READY", missing, "CREATE_MODERN_REFINED_YAML_IN_FUTURE_PHASE"


def audit(root: Path) -> dict:
    candidates = find_candidates(root)
    primary = choose_primary_source(candidates)
    parameters = {}
    if primary and primary.kind == "source":
        parameters = extract_parameters(read_text(Path(primary.path)))
    source_status, model_status, missing_fields, next_step = classify(candidates, parameters)
    return {
        "phase": "10.29C",
        "buz29d_source_status": source_status,
        "model_status": model_status,
        "critical_fields_status": "COMPLETE" if not missing_fields else "INCOMPLETE",
        "missing_fields": missing_fields,
        "future_yaml_readiness": source_status,
        "recommended_next_step": next_step,
        "primary_source": primary.path if primary else None,
        "candidates": [asdict(candidate) for candidate in candidates],
        "parameters": parameters,
        "caveats": [
            "Read-only audit; no legacy files were modified.",
            "Output-only PKN artifacts do not define a modern YAML without source provenance.",
            "No physical validation or numeric equivalence is claimed.",
        ],
    }


def write_markdown(path: Path, summary: dict) -> None:
    lines = [
        "# Phase 10.29C BUZ-29D audit",
        "",
        "## Summary",
        "",
        f"- `buz29d_source_status`: `{summary['buz29d_source_status']}`",
        f"- `model_status`: `{summary['model_status']}`",
        f"- `future_yaml_readiness`: `{summary['future_yaml_readiness']}`",
        f"- `recommended_next_step`: `{summary['recommended_next_step']}`",
        "",
        "## Candidates",
        "",
        "| Path | Kind | Model | Status |",
        "|---|---|---|---|",
    ]
    for candidate in summary["candidates"]:
        lines.append(f"| `{candidate['path']}` | {candidate['kind']} | {candidate['model']} | {candidate['status']} |")
    lines.extend(["", "## Parameters", "", "| Field | Value | Unit | Status |", "|---|---|---|---|"])
    for key, info in summary["parameters"].items():
        value = str(info.get("value") or "").replace("|", "\\|")
        lines.append(f"| {key} | `{value}` | {info.get('unit') or ''} | {info.get('status')} |")
    lines.extend(["", "## Caveats", ""])
    for caveat in summary["caveats"]:
        lines.append(f"- {caveat}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = audit(args.legacy_root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, summary)
    print(f"BUZ29D_SOURCE_STATUS={summary['buz29d_source_status']}")
    print(f"MODEL_STATUS={summary['model_status']}")
    print(f"FUTURE_YAML_READINESS={summary['future_yaml_readiness']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
