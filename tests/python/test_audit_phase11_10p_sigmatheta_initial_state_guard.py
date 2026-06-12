import json
from pathlib import Path

from tools.audit_phase11_10p_sigmatheta_initial_state_guard import (
    build_audit,
    build_parser,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[2]

def test_audit_phase11_10p_help() -> None:
    help_text = build_parser().format_help()

    assert "sigma-theta initial-state guard" in help_text


def test_audit_phase11_10p_reports_implemented_status() -> None:
    audit = build_audit(REPO_ROOT)

    assert audit["implementation_status"] == "SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED"


def test_audit_phase11_10p_reports_preferred_source() -> None:
    audit = build_audit(REPO_ROOT)

    assert audit["preferred_source"] == "ELASTIC_INITIAL_WELLBORE_STATE"


def test_audit_phase11_10p_keeps_dispatch_blocked() -> None:
    audit = build_audit(REPO_ROOT)

    assert audit["dispatch_allowed_next"] is False
    assert audit["runtime_execution_allowed_next"] is False
    assert audit["buz29_execution_allowed_next"] is False


def test_audit_phase11_10p_reports_no_parser_schema_change() -> None:
    audit = build_audit(REPO_ROOT)

    assert audit["parser_schema_changed"] is False


def test_audit_phase11_10p_reports_no_runtime_dispatch_change() -> None:
    audit = build_audit(REPO_ROOT)

    assert audit["runtime_dispatch_changed"] is False


def test_audit_phase11_10p_reports_no_lot_pkn_behavior_change() -> None:
    audit = build_audit(REPO_ROOT)

    assert audit["lot_pkn_behavior_changed"] is False


def test_audit_phase11_10p_output_json(tmp_path: Path) -> None:
    output_json = tmp_path / "audit.json"

    assert main(["--repo-root", str(REPO_ROOT), "--output-json", str(output_json)]) == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))

    assert data["implementation_status"] == "SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED"


def test_audit_phase11_10p_output_md(tmp_path: Path) -> None:
    output_md = tmp_path / "audit.md"

    assert main(["--repo-root", str(REPO_ROOT), "--output-md", str(output_md)]) == 0

    assert "Phase 11.10P Sigma-Theta Initial-State Guard Audit" in output_md.read_text(
        encoding="utf-8"
    )


def test_audit_phase11_10p_lists_required_statuses() -> None:
    audit = build_audit(REPO_ROOT)

    assert "SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED" in audit["required_statuses"]


def test_audit_phase11_10p_lists_blocking_reasons() -> None:
    audit = build_audit(REPO_ROOT)

    assert (
        "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH"
        in audit["blocking_reasons_supported"]
    )
