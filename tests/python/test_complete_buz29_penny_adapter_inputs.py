import json
import subprocess
import sys
from pathlib import Path

from tools.complete_buz29_penny_adapter_inputs import (
    PHASE,
    STATUS_COMPLETED_DIAGNOSTIC,
    STATUS_PARTIAL,
    evaluate_matrix,
)


SCRIPT = Path("tools/complete_buz29_penny_adapter_inputs.py")
MATRIX = Path(
    "tests/fixtures/comparison/phase_buz29_penny_adapter_inputs/"
    "buz29_penny_adapter_input_matrix.json"
)


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        stdin=subprocess.DEVNULL,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _complete_matrix(tmp_path: Path) -> Path:
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    for field in data["fields"]:
        field["status"] = "AVAILABLE_FROM_DIAGNOSTIC_SOURCE"
        field["value_available"] = True
        field["can_use_for_buz29_diagnostic"] = True
    data["all_required_inputs_complete"] = True
    data["blocking_fields"] = []
    data["ambiguous_fields"] = []
    data["resolved_input_created"] = True
    path = tmp_path / "complete_matrix.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def test_help() -> None:
    result = run_script("--help")
    assert result.returncode == 0
    assert "PennyShapedDiagnosticAdapter input completeness" in result.stdout


def test_repository_matrix_is_partial() -> None:
    report = evaluate_matrix(MATRIX)
    assert report["phase"] == PHASE
    assert report["input_status"] == STATUS_PARTIAL
    assert report["all_required_inputs_complete"] is False
    assert report["resolved_input_created"] is False


def test_repository_matrix_lists_blocking_fields() -> None:
    report = evaluate_matrix(MATRIX)
    assert "young_modulus_Pa" in report["blocking_fields"]
    assert "sigma_theta_compression_positive_Pa" in report["blocking_fields"]
    assert report["blocking_fields_count"] == 5


def test_repository_matrix_lists_ambiguous_fields() -> None:
    report = evaluate_matrix(MATRIX)
    assert report["ambiguous_fields"] == [
        "elapsed_since_opening_min",
        "wellbore_pressure_Pa",
    ]
    assert report["ambiguous_fields_count"] == 2


def test_repository_matrix_preserves_safety_flags() -> None:
    report = evaluate_matrix(MATRIX)
    assert report["diagnostic_only"] is True
    assert report["physically_validated"] is False
    assert report["legacy_equivalent"] is False
    assert report["runtime_dispatch_enabled"] is False


def test_complete_diagnostic_matrix_is_classified_complete(tmp_path: Path) -> None:
    report = evaluate_matrix(_complete_matrix(tmp_path))
    assert report["input_status"] == STATUS_COMPLETED_DIAGNOSTIC
    assert report["all_required_inputs_complete"] is True
    assert report["resolved_input_created"] is True
    assert report["recommended_next_phase"] == "PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_WITH_RUNNER"


def test_runtime_dispatch_true_is_rejected(tmp_path: Path) -> None:
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    data["runtime_dispatch_enabled"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    try:
        evaluate_matrix(path)
    except ValueError as exc:
        assert "runtime_dispatch_enabled" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected runtime dispatch rejection")


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    output_json = tmp_path / "completion.json"
    output_md = tmp_path / "completion.md"
    result = run_script(
        "--matrix",
        str(MATRIX),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    )
    assert result.returncode == 0
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["input_status"] == STATUS_PARTIAL
    assert "BUZ29_PENNY_ADAPTER_INPUTS_STILL_PARTIAL" in output_md.read_text(
        encoding="utf-8"
    )
