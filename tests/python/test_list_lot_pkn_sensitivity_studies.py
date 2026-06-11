import json
from pathlib import Path

import pytest

from tools import list_lot_pkn_sensitivity_studies as studies


FIXTURE = Path("tests/fixtures/comparison/studies_index_fixture.yaml")
REAL_INDEX = Path("cases/validation/sensitivity/studies_index.yaml")


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        studies.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "validate" in capsys.readouterr().out


def test_lists_fixture_study():
    payload = studies.build_payload(FIXTURE)

    assert payload["study_count"] == 2
    assert payload["studies"][0]["id"] == "fixture_cgeom"


def test_filters_by_tag():
    payload = studies.build_payload(FIXTURE, tag="modern-refined")

    assert payload["study_count"] == 1
    assert payload["studies"][0]["id"] == "fixture_cgeom"


def test_filters_by_status():
    payload = studies.build_payload(FIXTURE, status="archived")

    assert payload["study_count"] == 1
    assert payload["studies"][0]["id"] == "fixture_archived"


def test_validates_existing_matrix():
    payload = studies.build_payload(FIXTURE, tag="modern-refined", validate=True)

    assert payload["validation_status"] == "OK"
    assert payload["validation"][0]["matrix_exists"] is True


def test_validation_fails_when_matrix_missing(tmp_path):
    index = tmp_path / "index.yaml"
    index.write_text(
        "studies:\n"
        "  - id: missing\n"
        "    title: Missing\n"
        "    matrix: missing.yaml\n"
        "    route: modern-refined\n"
        "    status: active\n"
        "    tags: [fixture]\n"
        "    caveat: missing\n",
        encoding="utf-8",
    )

    payload = studies.build_payload(index, validate=True)

    assert payload["validation_status"] == "FAILED"
    assert payload["validation"][0]["status"] == "MISSING_MATRIX"


def test_emit_json(capsys):
    assert studies.main(["--index", str(FIXTURE), "--tag", "modern-refined", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["study_count"] == 1
    assert payload["studies"][0]["id"] == "fixture_cgeom"


def test_real_index_registers_buz67d_matrix():
    payload = studies.build_payload(REAL_INDEX, validate=True)

    assert payload["validation_status"] == "OK"
    assert payload["studies"][0]["id"] == "buz67d_cgeom_sensitivity"
