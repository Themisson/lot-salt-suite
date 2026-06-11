import csv
import json

import pytest

from tools import audit_phase11_5d_summary_maxima as audit


def write_timeseries(path, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow({column: "1" for column in columns})


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        audit.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "timeseries-csv" in capsys.readouterr().out


def test_all_required_columns_are_safe(tmp_path):
    csv_path = tmp_path / "timeseries.csv"
    write_timeseries(csv_path, ["time_s", *audit.REQUIRED_COLUMNS])

    summary = audit.audit(csv_path)

    assert summary["status"] == "SUMMARY_MAXIMA_PYTHON_ONLY_SAFE"
    assert summary["requires_cpp_change"] is False
    assert not summary["missing_columns"]


def test_missing_columns_block_maxima_summary(tmp_path):
    csv_path = tmp_path / "timeseries.csv"
    write_timeseries(csv_path, ["time_s", "wellbore_pressure_Pa"])

    summary = audit.audit(csv_path)

    assert summary["status"] == "SUMMARY_MAXIMA_BLOCKED_MISSING_FIELDS"
    assert "fracture_volume_m3" in summary["missing_columns"]


def test_cli_writes_json_and_markdown(tmp_path):
    csv_path = tmp_path / "timeseries.csv"
    write_timeseries(csv_path, ["time_s", *audit.REQUIRED_COLUMNS])
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"

    rc = audit.main(["--timeseries-csv", str(csv_path), "--output-json", str(output_json), "--output-md", str(output_md)])

    assert rc == 0
    assert json.loads(output_json.read_text(encoding="utf-8"))["status"] == "SUMMARY_MAXIMA_PYTHON_ONLY_SAFE"
    assert "max_fracture_volume_m3" in output_md.read_text(encoding="utf-8")
