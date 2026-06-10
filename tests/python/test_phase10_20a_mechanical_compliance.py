import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "audit_phase10_20a_mechanical_compliance.py"


def test_phase10_20a_help_exposes_output_dir():
    result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--output-dir" in result.stdout
    assert "mechanical annular compliance" in result.stdout


def test_phase10_20a_reports_partial_formulation_gate():
    result = subprocess.run(
        [sys.executable, str(TOOL)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    data = json.loads(result.stdout)

    assert data["gate"] == "MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL"
    assert data["classification"] == "ELASTIC_SIMPLE_FORMULATION_READY_AS_DIAGNOSTIC"
    assert data["diagnostic_baseline_10_19c"]["geometric_compressibility_1_Pa"] > 0


def test_phase10_20a_elastic_estimate_is_not_silent_calibration(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL), "--output-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    data = json.loads(result.stdout)
    estimate = data["elastic_annular_simple_estimate"]

    assert estimate["geometric_compressibility_1_Pa"] > 0
    assert 0 < estimate["ratio_to_diagnostic_geometric_compliance"] < 1
    assert data["predicted_first_dP_elastic_simple_Pa"] > data[
        "diagnostic_baseline_10_19c"
    ]["legacy_first_dP_Pa"]
    assert (tmp_path / "phase10_20a_mechanical_compliance_audit.json").exists()
    assert (tmp_path / "phase10_20a_mechanical_compliance_audit.csv").exists()
