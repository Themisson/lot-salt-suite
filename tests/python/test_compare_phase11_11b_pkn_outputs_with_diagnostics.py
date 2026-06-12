import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import compare_phase11_11b_pkn_outputs_with_diagnostics as tool  # noqa: E402


SCRIPT = Path("tools/compare_phase11_11b_pkn_outputs_with_diagnostics.py")


def write_pair(root: Path, case_id: str, *, changed: bool = False, diagnostic: bool = True) -> None:
    disabled = root / case_id / "disabled"
    enabled = root / case_id / "enabled"
    disabled.mkdir(parents=True)
    enabled.mkdir(parents=True)
    (disabled / "result.json").write_text('{"pressure": 1}\n', encoding="utf-8")
    (enabled / "result.json").write_text(
        '{"pressure": 2}\n' if changed else '{"pressure": 1}\n', encoding="utf-8"
    )
    (disabled / "timeseries.csv").write_text("time_s,pressure_Pa\n0,1\n", encoding="utf-8")
    (enabled / "timeseries.csv").write_text("time_s,pressure_Pa\n0,1\n", encoding="utf-8")
    if diagnostic:
        (enabled / "diagnostic_fracture_gate.json").write_text(
            '{"gate_status":"FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE"}\n',
            encoding="utf-8",
        )


def test_help_contract_is_declared() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "Phase 11.11B" in text
    assert "--fixture-root" in text
    assert "--diagnostic-mode" in text


def test_fixture_pairs_generate_ok_report(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    write_pair(fixtures, "minimal")
    output = tmp_path / "report.json"

    assert tool.main(["--fixture-root", str(fixtures), "--output-json", str(output)]) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["comparison_status"] == "PKN_OUTPUTS_UNCHANGED_WITH_DIAGNOSTICS"
    assert report["diagnostic_mode"] == "pre_runner"
    assert report["physical_outputs_identical"] is True
    assert report["diagnostic_output_isolated"] is True
    assert report["pkn_behavior_changed"] is False


def test_markdown_output_mentions_isolation(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    write_pair(fixtures, "leakoff")
    output = tmp_path / "report.md"

    assert tool.main(["--fixture-root", str(fixtures), "--output-md", str(output)]) == 0

    text = output.read_text(encoding="utf-8")
    assert "diagnostic_output_isolated" in text
    assert "pkn_behavior_changed" in text


def test_changed_result_is_rejected(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    write_pair(fixtures, "minimal", changed=True)
    output = tmp_path / "report.json"

    assert tool.main(["--fixture-root", str(fixtures), "--output-json", str(output)]) == 1

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["comparison_status"] == "PKN_OUTPUTS_CHANGED_OR_DIAGNOSTIC_NOT_ISOLATED"
    assert report["pkn_behavior_changed"] is True
    assert report["cases"][0]["changed_files"] == ["result.json"]


def test_missing_diagnostic_output_is_rejected(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    write_pair(fixtures, "minimal", diagnostic=False)
    output = tmp_path / "report.json"

    assert tool.main(["--fixture-root", str(fixtures), "--output-json", str(output)]) == 1

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["diagnostic_output_isolated"] is False


def test_limited_gate_mode_is_reported(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    write_pair(fixtures, "minimal")
    output = tmp_path / "report.json"

    assert (
        tool.main(
            [
                "--fixture-root",
                str(fixtures),
                "--diagnostic-mode",
                "limited_gate",
                "--phase-label",
                "11.11E",
                "--output-json",
                str(output),
            ]
        )
        == 0
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["phase"] == "11.11E"
    assert report["diagnostic_mode"] == "limited_gate"
    assert report["comparison_status"] == "PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE"


def test_empty_fixture_root_fails(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()

    try:
        tool.main(["--fixture-root", str(fixtures)])
    except ValueError as exc:
        assert "case/disabled and case/enabled pairs" in str(exc)
    else:
        raise AssertionError("empty fixture root should fail")
