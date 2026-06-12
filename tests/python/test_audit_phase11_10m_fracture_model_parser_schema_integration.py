import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.audit_phase11_10m_fracture_model_parser_schema_integration import (  # noqa: E402
    build_audit,
    build_parser,
    main,
    write_markdown,
)


SCRIPT = ROOT / "tools" / "audit_phase11_10m_fracture_model_parser_schema_integration.py"


def test_help_mentions_parser_schema_integration() -> None:
    help_text = build_parser().format_help()

    assert "fracture_model parser/schema integration" in help_text


def test_audit_reports_integrated_status() -> None:
    audit = build_audit(ROOT)

    assert audit["phase"] == "11.10M"
    assert audit["integration_status"] == "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATED"
    assert audit["field"] == "lot.fracture.fracture_model"


def test_schema_policy_and_allowed_values() -> None:
    audit = build_audit(ROOT)

    assert audit["schema_policy"] == "SCHEMA_STRICT_CANONICAL_ONLY"
    assert audit["allowed_canonical_values"] == ["PKN", "PENNY_SHAPED"]
    assert audit["default_fracture_model"] == "PKN"


def test_missing_field_and_error_behaviors() -> None:
    audit = build_audit(ROOT)

    assert audit["missing_field_behavior"] == "DEFAULT_TO_PKN"
    assert audit["explicit_empty_behavior"] == "ERROR_EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED"
    assert audit["unsupported_model_behavior"] == "ERROR_UNSUPPORTED_FRACTURE_MODEL"


def test_runtime_and_buz29_remain_blocked() -> None:
    audit = build_audit(ROOT)

    assert audit["runtime_dispatch_enabled"] is False
    assert audit["buz29_execution_allowed"] is False
    assert audit["lot_pkn_behavior_changed"] is False


def test_sigma_theta_initial_state_gate_is_recorded() -> None:
    audit = build_audit(ROOT)

    assert audit["sigma_theta_initial_state_audit_required"] is True
    assert audit["future_gate"]["gate"] == "SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH"
    assert (
        audit["future_gate"]["secondary_gate"]
        == "ALIGN_PRESSURE_AND_SIGMATHETA_SEMANTICS_BEFORE_FRACTURE_MODEL_SELECTION"
    )


def test_parser_schema_checks_are_true() -> None:
    audit = build_audit(ROOT)

    assert all(audit["parser_schema_checks"].values())


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"

    stdout = StringIO()
    with redirect_stdout(stdout):
        rc = main(
            [
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ]
        )

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["integration_status"] == "FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATED"
    assert "RUNTIME_DISPATCH_ENABLED=false" in stdout.getvalue()
    assert "Phase 11.10M" in output_md.read_text(encoding="utf-8")


def test_write_markdown_mentions_required_gate(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    write_markdown(build_audit(ROOT), output)

    text = output.read_text(encoding="utf-8")
    assert "SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH" in text
    assert "BUZ29-PENNY was not executed" in text
