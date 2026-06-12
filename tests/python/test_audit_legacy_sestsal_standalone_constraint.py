from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.audit_legacy_sestsal_standalone_constraint import (  # noqa: E402
    CAUSE,
    GATE,
    SECONDARY_GATE,
    STATUS,
    build_audit,
    build_parser,
    hydrostatic_norm_sigd,
    main,
)


def write_fixture_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    material = tmp_path / "legance" / "LOT_Tese" / "src" / "sestsal" / "material.cpp"
    material.parent.mkdir(parents=True)
    material.write_text(
        "\n".join(
            [
                "void Material::creepFunction(double T, Vector3d sig, Vector3d &b, double &sigde){",
                "double norm_sigd = sqrt(sigd(0)*sigd(0)+sigd(1)*sigd(1)+sigd(2)*sigd(2));",
                "Vector3d dev = 1./norm_sigd * sigd;",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    material2 = tmp_path / "legance" / "LOT_APB_v5" / "src" / "sestsal" / "material.cpp"
    material2.parent.mkdir(parents=True)
    material2.write_text(material.read_text(encoding="utf-8"), encoding="utf-8")
    apb = tmp_path / "legance" / "LOT_Tese" / "src" / "apb_code" / "APB1da.cpp"
    apb.parent.mkdir(parents=True)
    apb.write_text(
        "\n".join(
            [
                "mdl->setInnerPressure(pi + dP);",
                "mdl->setInnerTemperature(Ti + dT);",
                "x = mdl->solveThermalViscoStep(dt);",
            ]
        ),
        encoding="utf-8",
    )
    return material, material2, apb


def test_help_mentions_standalone_constraint() -> None:
    assert "standalone constraints" in build_parser().format_help()


def test_hydrostatic_state_has_zero_deviatoric_norm() -> None:
    assert hydrostatic_norm_sigd(12.0, 12.0, 12.0) == 0.0


def test_audit_classifies_legacy_sestsal_standalone_as_unsupported(tmp_path: Path) -> None:
    material, material2, apb = write_fixture_tree(tmp_path)
    audit = build_audit(repo_root=tmp_path, lot_tese_material=material, lot_apb_material=material2, apb1da=apb)
    assert audit["status"] == STATUS
    assert audit["cause"] == CAUSE
    assert audit["gate"] == GATE
    assert audit["standalone_validation_supported"] is False


def test_audit_detects_norm_sigd_nan_risk(tmp_path: Path) -> None:
    material, material2, apb = write_fixture_tree(tmp_path)
    audit = build_audit(repo_root=tmp_path, lot_tese_material=material, lot_apb_material=material2, apb1da=apb)
    assert audit["hydrostatic_state_divides_by_zero"] is True
    assert audit["norm_sigd_zero_generates_nan_risk"] is True


def test_audit_records_total_vs_perturbation_displacement_gate(tmp_path: Path) -> None:
    material, material2, apb = write_fixture_tree(tmp_path)
    audit = build_audit(repo_root=tmp_path, lot_tese_material=material, lot_apb_material=material2, apb1da=apb)
    assert audit["secondary_gate"] == SECONDARY_GATE
    assert audit["displacement_reference_comparison_status"] == "BLOCKED_TOTAL_VS_PERTURBATION_REFERENCE_MISMATCH"


def test_cli_writes_json(tmp_path: Path) -> None:
    material, material2, apb = write_fixture_tree(tmp_path)
    output_json = tmp_path / "audit.json"
    exit_code = main(
        [
            "--repo-root",
            str(tmp_path),
            "--lot-tese-material",
            str(material),
            "--lot-apb-material",
            str(material2),
            "--apb1da",
            str(apb),
            "--output-json",
            str(output_json),
        ]
    )
    assert exit_code == 0
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["gate"] == GATE
