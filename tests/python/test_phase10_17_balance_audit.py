import json
from pathlib import Path


AUDIT_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "comparison"
    / "phase10_17_balance_audit.json"
)


def load_audit():
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def test_phase10_17_audit_gate_allows_optional_balance_mode():
    audit = load_audit()

    assert audit["phase"] == "10.17A"
    assert audit["status"] == "AUDIT_COMPLETE"
    assert audit["physical_validation"] is False
    assert audit["implementation_performed"] is False
    assert audit["implementation_gate"] == "IMPLEMENTATION_ALLOWED_OPTIONAL_BALANCE_MODE"

    gate = audit["gate_conclusion"]
    assert gate["modern_lacks_annular_volumetric_pressure_balance"] is True
    assert gate["modern_has_required_inputs_for_optional_balance"] is True
    assert gate["gate"] == "IMPLEMENTATION_ALLOWED_OPTIONAL_BALANCE_MODE"


def test_phase10_17_audit_records_missing_modern_pressure_balance_inputs():
    audit = load_audit()
    topics = {item["topic"]: item for item in audit["comparison_findings"]}

    assert topics["annular_volume"]["classification"] == "MISSING_IN_MODERN_PRESSURE_MODEL"
    assert topics["compressibility"]["classification"] == "MISSING_IN_MODERN_PRESSURE_MODEL"
    assert topics["wellbore_pressure"]["classification"] == "MISSING_EXPLICIT_MODERN_OUTPUT"
    assert (
        topics["post_fracture_volume"]["classification"]
        == "AVAILABLE_FOR_OPTIONAL_BALANCE_DIAGNOSTIC"
    )


def test_phase10_17_audit_preserves_default_runtime_constraint():
    audit = load_audit()

    assert audit["modern_lot_pkn"]["pressure_model"]["status"] == "DIRECT_PKN_ONLY"
    assert audit["modern_lot_pkn"]["pressure_model"]["uses_annular_volume"] is False
    assert audit["modern_lot_pkn"]["pressure_model"]["uses_fluid_compressibility"] is False
    assert "Do not change default".lower() not in json.dumps(audit).lower()
    assert "DO_NOT_CHANGE_DEFAULT" in {
        item["classification"] for item in audit["comparison_findings"]
    }
