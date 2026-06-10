import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "audit_phase10_20a_mechanical_compliance.py"


def load_tool_module():
    spec = importlib.util.spec_from_file_location(
        "audit_phase10_20a_mechanical_compliance", TOOL
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_phase10_20a_help_exposes_output_dir():
    subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_phase10_20a_reports_partial_formulation_gate():
    tool = load_tool_module()
    data = tool.build_report()

    assert data["gate"] == "MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL"
    assert data["classification"] == "ELASTIC_SIMPLE_FORMULATION_READY_AS_DIAGNOSTIC"
    assert data["diagnostic_baseline_10_19c"]["geometric_compressibility_1_Pa"] > 0


def test_phase10_20a_elastic_estimate_is_not_silent_calibration(tmp_path):
    tool = load_tool_module()
    data = tool.build_report()
    tool.write_outputs(data, tmp_path)
    estimate = data["elastic_annular_simple_estimate"]

    assert estimate["geometric_compressibility_1_Pa"] > 0
    assert 0 < estimate["ratio_to_diagnostic_geometric_compliance"] < 1
    assert data["predicted_first_dP_elastic_simple_Pa"] > data[
        "diagnostic_baseline_10_19c"
    ]["legacy_first_dP_Pa"]
    assert (tmp_path / "phase10_20a_mechanical_compliance_audit.json").exists()
    assert (tmp_path / "phase10_20a_mechanical_compliance_audit.csv").exists()
