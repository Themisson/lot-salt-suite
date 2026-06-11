#!/usr/bin/env python3
"""Verify artifacts produced by tools/run_lot_pkn_study.py."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


CLASS_OK = "LOT_PKN_STUDY_RESULTS_OK"
CLASS_DRY = "LOT_PKN_STUDY_RESULTS_DRY_RUN_OK"
CLASS_PARTIAL = "LOT_PKN_STUDY_RESULTS_PARTIAL"
CLASS_FAILED = "LOT_PKN_STUDY_RESULTS_FAILED"
CLASS_INVALID = "LOT_PKN_STUDY_RESULTS_INVALID_MANIFEST"
CLASS_MISSING = "LOT_PKN_STUDY_RESULTS_MISSING_OUTPUTS"
CLASS_INCONCLUSIVE = "LOT_PKN_STUDY_RESULTS_INCONCLUSIVE"


def resolve_path(result_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return result_dir / path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_summary_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def required_manifest_fields() -> set[str]:
    return {
        "schema_version",
        "study_id",
        "study_status",
        "matrix_path",
        "outputs",
        "scenarios",
    }


def validate_manifest_shape(manifest: dict, errors: list[str]) -> None:
    missing = sorted(required_manifest_fields() - set(manifest))
    if missing:
        errors.append(f"manifest missing required fields: {missing}")
    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    if not isinstance(manifest.get("outputs"), dict):
        errors.append("manifest outputs must be an object")
    if not isinstance(manifest.get("scenarios"), list):
        errors.append("manifest scenarios must be a list")


def check_file(path: Path | None, label: str, errors: list[str]) -> bool:
    if path is None:
        errors.append(f"{label} is not declared")
        return False
    if not path.exists():
        errors.append(f"{label} is missing: {path}")
        return False
    return True


def validate_scenarios(manifest: dict, errors: list[str], warnings: list[str], strict: bool) -> str:
    scenarios = manifest.get("scenarios") or []
    if not scenarios:
        warnings.append("manifest has no scenario entries")
        return CLASS_PARTIAL
    failed = 0
    malformed = 0
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not scenario.get("id") or not scenario.get("status"):
            malformed += 1
            continue
        if str(scenario["status"]).lower() in {"failed", "error"}:
            failed += 1
    if malformed:
        errors.append("one or more scenarios are missing id/status")
    if failed:
        return CLASS_FAILED if strict or failed == len(scenarios) else CLASS_PARTIAL
    return CLASS_OK


def verify(args: argparse.Namespace) -> dict:
    result_dir: Path = args.result_dir
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = result_dir / args.manifest
    manifest: dict = {}

    if not result_dir.exists():
        errors.append(f"result-dir is missing: {result_dir}")
        classification = CLASS_MISSING
    elif not manifest_path.exists():
        errors.append(f"manifest is missing: {manifest_path}")
        classification = CLASS_INVALID
    else:
        try:
            manifest = read_json(manifest_path)
        except json.JSONDecodeError as exc:
            errors.append(f"manifest is not valid JSON: {exc}")
            manifest = {}
        validate_manifest_shape(manifest, errors)
        classification = CLASS_INVALID if errors else CLASS_INCONCLUSIVE

    if manifest and not errors:
        outputs = manifest.get("outputs") or {}
        study_status = str(manifest.get("study_status", "")).lower()
        dry_run = study_status == "dry_run"
        run_commands = resolve_path(result_dir, outputs.get("run_commands_txt"))
        check_file(run_commands, "run_commands_txt", errors)

        matrix_path = manifest.get("matrix_path")
        if matrix_path and not resolve_path(result_dir, str(matrix_path)).exists():
            warnings.append(f"matrix_path is not present in this checkout or result dir: {matrix_path}")

        if dry_run:
            if args.allow_dry_run:
                classification = CLASS_DRY
            else:
                errors.append("dry-run manifest requires --allow-dry-run")
                classification = CLASS_PARTIAL
        else:
            summary_path = resolve_path(result_dir, outputs.get("summary_csv"))
            metadata_path = resolve_path(result_dir, outputs.get("metadata_json"))
            summary_ok = check_file(summary_path, "summary_csv", errors)
            metadata_ok = check_file(metadata_path, "metadata_json", errors)
            if summary_ok and summary_path is not None:
                rows = read_summary_rows(summary_path)
                if not rows:
                    errors.append("summary_csv has no scenario rows")
            if metadata_ok and metadata_path is not None:
                try:
                    read_json(metadata_path)
                except json.JSONDecodeError as exc:
                    errors.append(f"metadata_json is not valid JSON: {exc}")
            if args.require_report:
                check_file(resolve_path(result_dir, outputs.get("report_json")), "report_json", errors)
                check_file(resolve_path(result_dir, outputs.get("report_md")), "report_md", errors)
            scenario_class = validate_scenarios(manifest, errors, warnings, args.strict)
            if errors:
                classification = CLASS_MISSING if any("missing" in err for err in errors) else CLASS_INVALID
            elif scenario_class in {CLASS_FAILED, CLASS_PARTIAL}:
                classification = scenario_class
            else:
                classification = CLASS_OK

    report = {
        "classification": classification,
        "result_dir": str(result_dir),
        "study_id": manifest.get("study_id") if manifest else None,
        "manifest_status": "present" if manifest else "missing_or_invalid",
        "outputs_status": "ok" if not errors else "issues",
        "scenario_status": classification,
        "warnings": warnings,
        "errors": errors,
    }
    return report


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# LOT/PKN study results verification",
        "",
        f"- classification: `{report['classification']}`",
        f"- result_dir: `{report['result_dir']}`",
        f"- study_id: `{report['study_id']}`",
        f"- manifest_status: `{report['manifest_status']}`",
        f"- outputs_status: `{report['outputs_status']}`",
        f"- scenario_status: `{report['scenario_status']}`",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {item}" for item in report["warnings"] or ["none"])
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {item}" for item in report["errors"] or ["none"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--manifest", default="study_manifest.json")
    parser.add_argument("--json", action="store_true", help="Print the verification report as JSON.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--allow-dry-run", action="store_true")
    parser.add_argument("--require-report", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify(args)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(args.output_md, report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"CLASSIFICATION={report['classification']}")
        print(f"STUDY_ID={report['study_id']}")
        print(f"ERRORS={len(report['errors'])}")
        print(f"WARNINGS={len(report['warnings'])}")
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
