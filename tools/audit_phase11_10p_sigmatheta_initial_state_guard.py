#!/usr/bin/env python3
"""Audit Phase 11.10P sigma-theta initial-state guard artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "include/lot/SigmaThetaInitialStateGuard.hpp",
    "src/lot/SigmaThetaInitialStateGuard.cpp",
    "tests/cpp/test_sigma_theta_initial_state_guard.cpp",
]


def build_audit(repo_root: Path) -> dict[str, Any]:
    source_files = []
    for rel_path in REQUIRED_FILES:
        path = repo_root / rel_path
        source_files.append(
            {
                "path": rel_path,
                "exists": path.exists(),
            }
        )

    implemented = all(item["exists"] for item in source_files)
    return {
        "phase": "11.10P",
        "implementation_status": (
            "SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED"
            if implemented
            else "SIGMATHETA_INITIAL_STATE_GUARD_INCOMPLETE"
        ),
        "preferred_source": "ELASTIC_INITIAL_WELLBORE_STATE",
        "dispatch_allowed_next": False,
        "runtime_execution_allowed_next": False,
        "buz29_execution_allowed_next": False,
        "parser_schema_changed": False,
        "runtime_dispatch_changed": False,
        "lot_pkn_behavior_changed": False,
        "source_files": source_files,
        "required_statuses": [
            "PHASE11_10P_SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED",
            "SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED",
            "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA",
            "FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA",
            "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
            "RUNTIME_DISPATCH_NOT_CHANGED",
            "PARSER_SCHEMA_NOT_CHANGED",
            "LOT_PKN_BEHAVIOR_NOT_CHANGED",
        ],
        "blocking_reasons_supported": [
            "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA",
            "FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA",
            "FRACTURE_GATE_BLOCKED_UNKNOWN_SOURCE",
            "FRACTURE_GATE_BLOCKED_WRONG_STATE_TIME",
            "FRACTURE_GATE_BLOCKED_UNKNOWN_REFERENCE_FRAME",
            "FRACTURE_GATE_BLOCKED_UNKNOWN_SIGN_CONVENTION",
            "FRACTURE_GATE_BLOCKED_UNKNOWN_PRESSURE_SEMANTICS",
            "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH",
        ],
        "recommended_next_phase": (
            "PHASE11_10Q_SPECIFY_FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD"
        ),
        "caveats": [
            "The guard is implemented as an isolated C++ helper.",
            "The guard is not integrated into parser, schema, CLI or runtime dispatch.",
            "BUZ29-PENNY is not executed.",
            "No physical validation or legacy equivalence is claimed.",
        ],
    }


def write_markdown(audit: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Phase 11.10P Sigma-Theta Initial-State Guard Audit",
        "",
        f"- phase: `{audit['phase']}`",
        f"- implementation_status: `{audit['implementation_status']}`",
        f"- preferred_source: `{audit['preferred_source']}`",
        f"- dispatch_allowed_next: `{str(audit['dispatch_allowed_next']).lower()}`",
        f"- runtime_execution_allowed_next: `{str(audit['runtime_execution_allowed_next']).lower()}`",
        f"- buz29_execution_allowed_next: `{str(audit['buz29_execution_allowed_next']).lower()}`",
        "",
        "## Source Files",
        "",
    ]
    for item in audit["source_files"]:
        lines.append(f"- `{item['path']}`: `{str(item['exists']).lower()}`")
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            *[f"- {caveat}" for caveat in audit["caveats"]],
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Phase 11.10P sigma-theta initial-state guard artifacts."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root. Defaults to the current working directory.",
    )
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--output-md", help="Optional Markdown output path.")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    audit = build_audit(repo_root)

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.output_md:
        write_markdown(audit, Path(args.output_md))

    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
