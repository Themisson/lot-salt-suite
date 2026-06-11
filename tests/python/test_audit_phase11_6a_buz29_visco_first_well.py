from pathlib import Path

import pytest

from tools import audit_phase11_6a_buz29_visco_first_well as audit


def write_first_well(root: Path, model_line: str) -> Path:
    path = root / "BUZ29-VISCO-first-well.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '#include "apb_code/APB1da.h"\n'
        "int main() {\n"
        "  vector<Temperature*> vtemp;\n"
        "  vtemp.push_back(new Temperature(2061., 3506., dA, A0, Af, 10));\n"
        "  vector<Fluids*> vfluids;\n"
        "  vfluids.push_back(new Fluids(0, false, 2061., 3506., 26.6, 101325.));\n"
        "  vfluids[0]->setPFluid(11., 8E-4, 6.40E-10);\n"
        "  //vfluids[0]->setLeakoffProps(\"pa_min\", 3., \"pkn\");\n"
        f"  {model_line}\n"
        "  MatrixXd mdepths(10, 3);\n"
        "  mdepths << 2061., 2158., 1;\n"
        "  Layers* layers = new Layers(1, mdepths, tier, 2061., vsolids, vrock, vfluids, vtemp);\n"
        "  APB1da simulation(0.1, 0.1, 1E-8, 13., 0, false, true, 6, 0.4);\n"
        '  std::string filePath = "results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat";\n'
        "}\n",
        encoding="utf-8",
    )
    return path


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        audit.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "legacy-root" in capsys.readouterr().out


def test_first_well_penny_shaped_is_not_pkn(tmp_path):
    write_first_well(tmp_path, 'vfluids[0]->setLeakoffProps("pa_min", 3., "penny-shaped");')

    summary = audit.audit(tmp_path)

    assert summary["source_status"] == "BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND"
    assert summary["primary_classification"] == "BUZ29_VISCO_FIRST_WELL_NOT_PKN"
    assert summary["modern_pkn_ready"] is False
    assert summary["parameters"]["active_fracture_model"]["value"] == "PENNY_SHAPED"


def test_first_well_source_absent(tmp_path):
    summary = audit.audit(tmp_path)

    assert summary["source_status"] == "BUZ29_VISCO_FIRST_WELL_SOURCE_NOT_FOUND"
    assert summary["primary_classification"] == "BUZ29_VISCO_FIRST_WELL_BLOCKED_SOURCE_NOT_FOUND"


def test_first_well_pkn_ready_when_active_pkn_and_fields_present(tmp_path):
    write_first_well(tmp_path, 'vfluids[0]->setLeakoffProps("pa_min", 3., "pkn");')

    summary = audit.audit(tmp_path)

    assert summary["primary_classification"] == "BUZ29_VISCO_FIRST_WELL_PKN_READY_FOR_FUTURE_YAML"
    assert summary["future_yaml_readiness"] == "BUZ29_VISCO_FIRST_WELL_READY_FOR_FUTURE_MODERN_YAML"


def test_commented_pkn_does_not_override_active_non_pkn(tmp_path):
    write_first_well(tmp_path, 'vfluids[0]->setLeakoffProps("pa_min", 3., "circular");')

    summary = audit.audit(tmp_path)

    assert summary["parameters"]["commented_pkn_evidence"]["value"] == "present"
    assert summary["parameters"]["active_fracture_model"]["value"] == "KGD_CIRCULAR"
    assert summary["primary_classification"] == "BUZ29_VISCO_FIRST_WELL_NOT_PKN"


def test_markdown_and_json_outputs(tmp_path):
    write_first_well(tmp_path / "legacy", 'vfluids[0]->setLeakoffProps("pa_min", 3., "penny-shaped");')
    out_json = tmp_path / "out" / "audit.json"
    out_md = tmp_path / "out" / "audit.md"

    rc = audit.main(["--legacy-root", str(tmp_path / "legacy"), "--output-json", str(out_json), "--output-md", str(out_md)])

    assert rc == 0
    assert "BUZ29_VISCO_FIRST_WELL_NOT_PKN" in out_json.read_text(encoding="utf-8")
    assert "penny-shaped" in out_md.read_text(encoding="utf-8")
