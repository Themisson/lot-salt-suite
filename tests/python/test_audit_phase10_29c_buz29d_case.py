from pathlib import Path

import pytest

from tools import audit_phase10_29c_buz29d_case as audit


def write_case(path: Path, model_line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '#include "apb_code/APB1da.h"\n'
        "int main() {\n"
        "  vector<Fluids*> vfluids;\n"
        "  vfluids.push_back(new Fluids(0, false, 2061., 3506., 26.6, 101325.));\n"
        "  vfluids[0]->setPFluid(11., 8E-4, 6.40E-10);\n"
        f"  {model_line}\n"
        "  MatrixXd mdepths(1, 3);\n"
        "  mdepths << 3486., 3506., 20;\n"
        "  Layers* layers = new Layers(1, mdepths, tier, 2061., vsolids, vrock, vfluids, vtemp);\n"
        "  APB1da simulation(0.1, 0.1, 1E-8, 13., 0, false, true, 6, 0.4);\n"
        '  simulation.setSaveName("results/7-BUZ-29D-RJS10_PKN.dat");\n'
        "}\n",
        encoding="utf-8",
    )


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        audit.build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "legacy-root" in capsys.readouterr().out


def test_buz29d_found_in_fixture(tmp_path):
    write_case(tmp_path / "BUZ29-PKN.cpp", 'vfluids[0]->setLeakoffProps("pa_min", 3., "pkn");')

    summary = audit.audit(tmp_path)

    assert summary["buz29d_source_status"] == "BUZ29D_READY_FOR_FUTURE_MODERN_REFINED_YAML"
    assert summary["model_status"] == "BUZ29D_MODERN_REFINED_READY"


def test_buz29d_absent(tmp_path):
    summary = audit.audit(tmp_path)

    assert summary["buz29d_source_status"] == "BUZ29D_SOURCE_NOT_FOUND"
    assert summary["model_status"] == "NO_SOURCE"


def test_pkn_model_detected(tmp_path):
    write_case(tmp_path / "BUZ29D-pkn.cpp", 'vfluids[0]->setLeakoffProps("pa_min", 3., "pkn");')

    candidates = audit.find_candidates(tmp_path)

    assert candidates[0].model == "PKN"


def test_non_pkn_model_detected(tmp_path):
    write_case(tmp_path / "BUZ29D-penny.cpp", 'vfluids[0]->setLeakoffProps("pa_min", 3., "penny-shaped");')

    summary = audit.audit(tmp_path)

    assert summary["model_status"] == "BUZ29D_NOT_PKN"
    assert summary["future_yaml_readiness"] == "BUZ29D_MODERN_YAML_NOT_READY"


def test_missing_critical_fields(tmp_path):
    (tmp_path / "BUZ29D-pkn.cpp").write_text(
        'int main() { vfluids[0]->setLeakoffProps("pa_min", 3., "pkn"); }\n',
        encoding="utf-8",
    )

    summary = audit.audit(tmp_path)

    assert summary["model_status"] == "BUZ29D_MISSING_CRITICAL_FIELDS"
    assert "simulation" in summary["missing_fields"]
