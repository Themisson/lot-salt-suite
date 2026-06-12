import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT = Path("tools/validate_phase11_11f_limited_gate_fixtures.py")
FIXTURES = Path("tests/fixtures/comparison/phase11_11f")


def run_script(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=check,
        text=True,
    )


def load_report(tmp_path: Path) -> dict:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    return json.loads(output.read_text(encoding="utf-8"))


def copy_fixtures(tmp_path: Path) -> Path:
    target = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, target)
    return target


def test_help() -> None:
    run_script("--help")
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11F" in text
    assert "--fixtures-dir" in text


def test_valid_fixtures(tmp_path: Path) -> None:
    data = load_report(tmp_path)
    assert data["fixture_status"] == "LIMITED_GATE_FIXTURES_VALID"
    assert data["fixture_count"] == 6


def test_metadata_valid(tmp_path: Path) -> None:
    data = load_report(tmp_path)
    metadata = data["metadata"]
    assert metadata["phase"] == "11.11F"
    assert metadata["limited_gate_mode_supported"] is True
    assert "LIMITED_GATE_DIAGNOSTIC_ONLY" in metadata["required_caveats"]


def test_default_disabled_covered(tmp_path: Path) -> None:
    assert load_report(tmp_path)["default_disabled_covered"] is True


def test_pkn_limited_gate_covered(tmp_path: Path) -> None:
    assert load_report(tmp_path)["pkn_limited_gate_covered"] is True


def test_penny_limited_gate_covered(tmp_path: Path) -> None:
    assert load_report(tmp_path)["penny_limited_gate_covered"] is True


def test_dispatch_true_invalid_covered(tmp_path: Path) -> None:
    assert load_report(tmp_path)["dispatch_true_invalid_covered"] is True


def test_missing_sigmatheta_blocks_covered(tmp_path: Path) -> None:
    assert load_report(tmp_path)["missing_sigmatheta_blocks_covered"] is True


def test_invalid_model_blocked_covered(tmp_path: Path) -> None:
    assert load_report(tmp_path)["invalid_model_blocked_covered"] is True


def test_runtime_dispatch_enabled_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["runtime_dispatch_enabled"] is False


def test_buz29_execution_allowed_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["buz29_execution_allowed"] is False


def test_pkn_behavior_change_allowed_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["pkn_behavior_change_allowed"] is False


def test_penny_shaped_runtime_enabled_false(tmp_path: Path) -> None:
    assert load_report(tmp_path)["penny_shaped_runtime_enabled"] is False


def test_json_generation(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    run_script("--fixtures-dir", str(FIXTURES), "--output-json", str(output))
    text = output.read_text(encoding="utf-8")
    assert "LIMITED_GATE_FIXTURES_VALID" in text
    assert "PHASE11_11G_VALIDATE_LIMITED_GATE_ON_CONTROLLED_CASES" in text


def test_markdown_generation(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    run_script("--fixtures-dir", str(FIXTURES), "--output-md", str(output))
    text = output.read_text(encoding="utf-8")
    assert "LIMITED_GATE_FIXTURES_VALID" in text
    assert "pkn_limited_gate_covered" in text


def test_missing_fixture_fails(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    (fixtures / "limited_gate_enabled_pkn.yaml").unlink()
    output = tmp_path / "report.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output),
        check=False,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert data["fixture_status"] == "LIMITED_GATE_FIXTURES_INVALID"


def test_invalid_metadata_fails(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    path = fixtures / "limited_gate_fixtures_metadata.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["runtime_dispatch_enabled"] = True
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    output = tmp_path / "report.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output),
        check=False,
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert any("runtime_dispatch_enabled must be false" in item for item in report["errors"])


def test_invalid_fixture_content_fails(tmp_path: Path) -> None:
    fixtures = copy_fixtures(tmp_path)
    path = fixtures / "limited_gate_enabled_pkn.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["lot"]["fracture"]["fracture_gate_diagnostics"]["mode"] = "pre_runner"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    output = tmp_path / "report.json"
    result = run_script(
        "--fixtures-dir",
        str(fixtures),
        "--output-json",
        str(output),
        check=False,
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert any("diagnostics.mode must be limited_gate" in item for item in report["errors"])
