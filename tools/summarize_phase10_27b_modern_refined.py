from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PHASE = "10.27B"
SOURCE = "DOCUMENTED_PHASE_SUMMARY"


SUMMARY: dict[str, Any] = {
    "mode": "modern_refined",
    "legacy_equivalence_status": "NOT_LEGACY_EQUIVALENT",
    "pressure_scale_status": "DIAGNOSTICALLY_GOOD",
    "opening_time_status": "DIFFERENT_BUT_NOT_AUTOMATIC_ERROR",
    "apbsalt1d_status": "METADATA_ONLY_BLOCKED",
    "pressure_source_timing_status": "BLOCKED_BY_GEOMETRY",
    "recommended_next_phase": "MODERN_REFINED_DOCUMENTATION_AND_VALIDATION_CONTINUATION",
    "source": SOURCE,
    "metrics": {
        "legacy_max_pressure_Pa": 69035836.1743195,
        "modern_max_pressure_Pa": 67331393.612597,
        "relative_error_max_pressure": -0.02468924338685035,
        "legacy_opening_time_s": 510.0,
        "modern_opening_time_s": 660.0,
        "opening_time_error_s": 150.0,
        "legacy_sink_delay_s": 30.0,
        "modern_sink_delay_s": 30.0,
        "pressure_at_opening_relative_error": 0.008415423398363079,
    },
    "preserved_physical_parameters": {
        "initial_pressure_Pa": 26732215.17314985,
        "injection_rate_bbl_min": 0.5,
        "injection_time_min": 12.5,
        "shutin_time_min": 9.5,
        "fluid_density_ppg": 11.5,
        "fluid_compressibility_1_per_Pa": 6.4e-10,
        "thermal_alpha_1_per_degC": 8.0e-4,
        "drill_pipe_od_in": 5.5,
        "profTeste_m": 4374.0,
        "constant_geometric_compliance_1_per_Pa": 1.8571966938610005e-8,
        "sink_timing": "next_step",
    },
    "non_equivalent_geometry": {
        "outer_radius": "LOT_Tese/APBSalt1D 8 m versus modern bridge/default 1.556 m",
        "radial_elements": "LOT_Tese/APBSalt1D 15 versus modern default/bridge 40",
        "ratio": "LOT_Tese/APBSalt1D 10; modern-refined does not consume ratio",
        "sampling": "legacy elem0/sig(2,0) is not available in time-series route",
        "sigmaTheta_source": "refined time-series, not runtime salt wall stress",
    },
    "classifications": [
        "BUZ67D_MODERN_REFINED_VALIDATION_DOCUMENTED",
        "MODERN_REFINED_NOT_LEGACY_EQUIVALENT",
        "PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY",
        "APBSALT1D_SAMPLING_BRIDGE_BLOCKED",
    ],
    "caveats": [
        "O modern-refined mode nao e regressao estrita contra o LOT_Tese.",
        "Abertura em 660 s nao e erro automatico sem equivalencia geometrica.",
        "constant_geometric permanece baseline diagnostica, nao modelo fisico validado.",
        "sigmaTheta runtime real continua trabalho futuro.",
        "results/ outputs sao artefatos locais e nao devem ser versionados.",
    ],
}


def build_summary() -> dict[str, Any]:
    return {"phase": PHASE, **SUMMARY}


def _write_markdown(summary: dict[str, Any], path: Path) -> None:
    metrics = summary["metrics"]
    lines = [
        "# Phase 10.27B BUZ67D modern-refined summary",
        "",
        f"- mode: `{summary['mode']}`",
        f"- source: `{summary['source']}`",
        f"- legacy_equivalence_status: `{summary['legacy_equivalence_status']}`",
        f"- pressure_scale_status: `{summary['pressure_scale_status']}`",
        f"- opening_time_status: `{summary['opening_time_status']}`",
        f"- pressure_source_timing_status: `{summary['pressure_source_timing_status']}`",
        f"- recommended_next_phase: `{summary['recommended_next_phase']}`",
        "",
        "## Metrics",
        "",
        f"- legacy_max_pressure_Pa: `{metrics['legacy_max_pressure_Pa']}`",
        f"- modern_max_pressure_Pa: `{metrics['modern_max_pressure_Pa']}`",
        f"- relative_error_max_pressure: `{metrics['relative_error_max_pressure']}`",
        f"- legacy_opening_time_s: `{metrics['legacy_opening_time_s']}`",
        f"- modern_opening_time_s: `{metrics['modern_opening_time_s']}`",
        f"- opening_time_error_s: `{metrics['opening_time_error_s']}`",
        f"- legacy_sink_delay_s: `{metrics['legacy_sink_delay_s']}`",
        f"- modern_sink_delay_s: `{metrics['modern_sink_delay_s']}`",
        "",
        "## Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in summary["classifications"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in summary["caveats"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    summary = build_summary()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_markdown(summary, output_md)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize Phase 10.27B BUZ67D modern-refined diagnostic package."
    )
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    summary = run(build_parser().parse_args(argv))
    print(
        json.dumps(
            {
                "phase": summary["phase"],
                "mode": summary["mode"],
                "legacy_equivalence_status": summary["legacy_equivalence_status"],
                "pressure_scale_status": summary["pressure_scale_status"],
                "opening_time_status": summary["opening_time_status"],
                "pressure_source_timing_status": summary["pressure_source_timing_status"],
                "recommended_next_phase": summary["recommended_next_phase"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
