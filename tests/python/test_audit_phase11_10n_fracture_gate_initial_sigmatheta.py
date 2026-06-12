import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.audit_phase11_10n_fracture_gate_initial_sigmatheta import (  # noqa: E402
    build_audit,
    build_parser,
    main,
    write_markdown,
)


def test_help_mentions_initial_sigma_theta_state() -> None:
    help_text = build_parser().format_help()

    assert "initial sigma-theta state" in help_text


def test_audit_reports_required_core_fields() -> None:
    audit = build_audit(ROOT)

    assert audit["phase"] == "11.10N"
    assert audit["sigmatheta_initial_state"]
    assert audit["fracture_gate_status"]
    assert audit["pressure_semantics"]
    assert audit["sign_convention"]


def test_t0_lot_vs_drilling_distinction_is_explicit() -> None:
    audit = build_audit(ROOT)

    assert audit["t0_lot_vs_drilling_distinction"] is True


def test_dispatch_runtime_and_buz29_remain_blocked() -> None:
    audit = build_audit(ROOT)

    assert audit["dispatch_allowed_next"] is False
    assert audit["runtime_execution_allowed_next"] is False
    assert audit["buz29_execution_allowed_next"] is False


def test_recommended_next_phase_matches_conservative_initial_state_gate() -> None:
    audit = build_audit(ROOT)

    assert audit["sigmatheta_initial_state"] == "SIGMATHETA_INITIAL_STATE_MISSING"
    assert audit["fracture_gate_status"] == "FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING"
    assert audit["recommended_next_phase"] == "PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING"


def test_audit_detects_existing_sigma_theta_sources() -> None:
    audit = build_audit(ROOT)
    checks = audit["audit_checks"]

    assert checks["pkn_model_consumes_sigma_theta_static"] is True
    assert checks["pkn_model_consumes_sigma_theta_provider_runtime"] is True
    assert checks["parser_reads_sigma_theta_static"] is True
    assert checks["parser_reads_sigma_theta_time_series"] is True
    assert checks["salt_wall_stress_diagnostics_available_opt_in"] is True


def test_blocking_gaps_include_initial_state_and_semantic_alignment() -> None:
    audit = build_audit(ROOT)
    text = "\n".join(audit["blocking_gaps"])

    assert "sigma_theta_initial_after_drilling" in text
    assert "post-drilling" in text
    assert "Pressure source and sigma_theta reference" in text


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
    markdown = output_md.read_text(encoding="utf-8")

    assert rc == 0
    assert payload["phase"] == "11.10N"
    assert payload["dispatch_allowed_next"] is False
    assert payload["runtime_execution_allowed_next"] is False
    assert payload["buz29_execution_allowed_next"] is False
    assert "DISPATCH_ALLOWED_NEXT=false" in stdout.getvalue()
    assert "Phase 11.10N" in markdown


def test_write_markdown_mentions_gate_and_next_phase(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    write_markdown(build_audit(ROOT), output)

    text = output.read_text(encoding="utf-8")
    assert "SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH" in text
    assert "PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING" in text
