from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "comparison"

LEVEL0_CAVEATS = [
    "legacy time unit is unknown",
    "legacy Layer is 1-based and not equivalent to wall_gp_*",
    "sigmaTheta is not exported by legacy output",
    "pw is not exported by legacy output",
    "margin is not exported by legacy output",
    "opened is not exported by legacy output",
    "comparison is structural only, not physical validation",
]


def parse_legacy_dat(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)

    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
    useful_lines = [line for line in lines if line.strip()]
    fields = {line.strip() for line in useful_lines if line.strip().isalpha()}

    time_index = next((i for i, line in enumerate(lines) if line.strip() == "Time"), None)
    times: list[float] = []
    if time_index is not None and time_index + 1 < len(lines):
        times = [float(value) for value in lines[time_index + 1].split()]

    layers = [
        lines[i + 1].strip()
        for i, line in enumerate(lines[:-1])
        if line.strip() == "Layer" and lines[i + 1].strip()
    ]

    n_records = 0
    for i, line in enumerate(lines[:-1]):
        if line.strip() == "dP":
            n_rows = int(lines[i + 1].strip())
            n_records += n_rows * len(times)

    return {
        "source": str(path),
        "legacy_dat_n_records": n_records,
        "legacy_dat_time_min_raw": min(times) if times else None,
        "legacy_dat_time_max_raw": max(times) if times else None,
        "legacy_dat_fields": sorted(fields | {"Time"} if times else fields),
        "legacy_dat_n_layers": len(set(layers)),
        "caveats": LEVEL0_CAVEATS,
    }


def parse_legacy_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data if isinstance(data, list) else [data]
    times: list[float] = []
    n_layers = 0
    n_records = 0
    fields: set[str] = set()

    for case in cases:
        annuli = case.get("annuli", {})
        fields.update(case.keys())
        for annulus in annuli.values():
            md_values = annulus.get("md", [])
            n_layers += len(md_values)
            for result in annulus.get("results_by_time", []):
                fields.update(result.keys())
                if "time" in result:
                    times.append(float(result["time"]))
                n_records += max(1, len(md_values))

    return {
        "source": str(path),
        "legacy_json_n_records": n_records,
        "legacy_json_n_times": len(set(times)),
        "legacy_json_time_min_raw": min(times) if times else None,
        "legacy_json_time_max_raw": max(times) if times else None,
        "legacy_json_n_layers": n_layers,
        "legacy_json_fields": sorted(fields),
        "caveats": LEVEL0_CAVEATS,
    }


def parse_modern_csv(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    time_column = "time_s" if "time_s" in fields else None
    times = [float(row[time_column]) for row in rows] if time_column else []

    return {
        "source": str(path),
        "modern_csv_n_records": len(rows),
        "modern_csv_time_min_s": min(times) if times else None,
        "modern_csv_time_max_s": max(times) if times else None,
        "modern_csv_fields": fields,
        "caveats": LEVEL0_CAVEATS,
    }


def test_parse_legacy_dat_fixture() -> None:
    metadata = parse_legacy_dat(FIXTURE_DIR / "legacy_buz67d_sample.dat")

    assert metadata["legacy_dat_n_records"] > 0
    assert metadata["legacy_dat_time_min_raw"] == 0.0
    assert metadata["legacy_dat_time_max_raw"] == 12.5
    assert "Time" in metadata["legacy_dat_fields"]
    assert "Layer" in metadata["legacy_dat_fields"]
    assert "dP" in metadata["legacy_dat_fields"]
    assert metadata["legacy_dat_n_layers"] == 1


def test_parse_legacy_json_fixture() -> None:
    metadata = parse_legacy_json(FIXTURE_DIR / "legacy_score_mro28_sample.json")

    assert metadata["legacy_json_n_records"] > 0
    assert metadata["legacy_json_n_times"] == 1
    assert metadata["legacy_json_time_min_raw"] == 0.0
    assert metadata["legacy_json_time_max_raw"] == 0.0
    assert metadata["legacy_json_n_layers"] == 2
    assert "pressure" in metadata["legacy_json_fields"]


def test_parse_modern_csv_fixture() -> None:
    metadata = parse_modern_csv(FIXTURE_DIR / "modern_buz67d_sample.csv")

    assert metadata["modern_csv_n_records"] == 15
    assert metadata["modern_csv_time_min_s"] == 0.0
    assert metadata["modern_csv_time_max_s"] == 420.0
    assert "time_s" in metadata["modern_csv_fields"]
    assert "net_pressure_Pa" in metadata["modern_csv_fields"]


def test_level0_record_count() -> None:
    legacy_dat = parse_legacy_dat(FIXTURE_DIR / "legacy_buz67d_sample.dat")
    legacy_json = parse_legacy_json(FIXTURE_DIR / "legacy_score_mro28_sample.json")
    modern_csv = parse_modern_csv(FIXTURE_DIR / "modern_buz67d_sample.csv")

    assert legacy_dat["legacy_dat_n_records"] > 0
    assert legacy_json["legacy_json_n_records"] > 0
    assert modern_csv["modern_csv_n_records"] > 0


def test_level0_time_range() -> None:
    legacy_dat = parse_legacy_dat(FIXTURE_DIR / "legacy_buz67d_sample.dat")
    legacy_json = parse_legacy_json(FIXTURE_DIR / "legacy_score_mro28_sample.json")
    modern_csv = parse_modern_csv(FIXTURE_DIR / "modern_buz67d_sample.csv")

    assert legacy_dat["legacy_dat_time_max_raw"] >= legacy_dat["legacy_dat_time_min_raw"]
    assert legacy_json["legacy_json_time_max_raw"] >= legacy_json["legacy_json_time_min_raw"]
    assert modern_csv["modern_csv_time_max_s"] >= modern_csv["modern_csv_time_min_s"]
    assert "legacy time unit is unknown" in legacy_dat["caveats"]


def test_level0_field_presence() -> None:
    legacy_dat = parse_legacy_dat(FIXTURE_DIR / "legacy_buz67d_sample.dat")
    legacy_json = parse_legacy_json(FIXTURE_DIR / "legacy_score_mro28_sample.json")
    modern_csv = parse_modern_csv(FIXTURE_DIR / "modern_buz67d_sample.csv")

    assert {"Time", "Layer", "dP"}.issubset(set(legacy_dat["legacy_dat_fields"]))
    assert {"annuli", "pressure", "volume"}.issubset(set(legacy_json["legacy_json_fields"]))
    assert {"time_s", "fracture_width_m", "net_pressure_Pa"}.issubset(
        set(modern_csv["modern_csv_fields"])
    )


def test_level0_caveats_preserved() -> None:
    metadata = parse_legacy_dat(FIXTURE_DIR / "legacy_buz67d_sample.dat")
    caveats = "\n".join(metadata["caveats"])

    assert "legacy time unit is unknown" in caveats
    assert "legacy Layer is 1-based" in caveats
    assert "sigmaTheta is not exported" in caveats
    assert "pw is not exported" in caveats
    assert "margin is not exported" in caveats
    assert "opened is not exported" in caveats
    assert "structural only" in caveats
