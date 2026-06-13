import json
import subprocess
import sys
from pathlib import Path

from tools.audit_post_drilling_sigma_theta_provider import build_audit


SCRIPT = Path("tools/audit_post_drilling_sigma_theta_provider.py")


def test_help() -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--help"], check=True, text=True)


def test_generates_json(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-json", str(output)],
        check=True,
        text=True,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["implementation_status"] == "POST_DRILLING_SIGMATHETA_PROVIDER_IMPLEMENTED"


def test_generates_markdown(tmp_path: Path) -> None:
    output = tmp_path / "audit.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-md", str(output)],
        check=True,
        text=True,
    )
    assert "PostDrillingSigmaThetaProvider" in output.read_text(encoding="utf-8")


def test_supported_sources_include_elastic() -> None:
    assert "ELASTIC_INITIAL_WELLBORE_STATE" in build_audit()["supported_sources"]


def test_unknown_source_rejected() -> None:
    assert build_audit()["unknown_source_rejected"] is True


def test_physical_flags_rejected() -> None:
    audit = build_audit()
    assert audit["physically_validated_true_rejected"] is True
    assert audit["legacy_equivalent_true_rejected"] is True


def test_runtime_dispatch_remains_false() -> None:
    assert build_audit()["runtime_dispatch_enabled"] is False


def test_pre_runner_not_wired_yet() -> None:
    assert build_audit()["wiring_to_pre_runner"] is False
