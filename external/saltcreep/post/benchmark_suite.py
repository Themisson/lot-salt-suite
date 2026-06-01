"""Benchmark matrix runner for saltcreep.

The default preset is intentionally modest so a developer can run it during a
workday. Use ``--preset full`` to expand to the Cartesian product requested for
performance campaigns.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "benchmark"

ELEMENTS = [
    "axisym_1d_L3",
    "axisym_2d_Q4",
    "axisym_2d_T3",
    "axisym_2d_Q8",
    "axisym_2d_Q9",
    "axisym_2d_T6",
    "axisym_2d_AQ9",
]
MODELS = ["DM", "EDMT", "Wang2004", "AubertinISV_SH_D", "ISV_SH_DM"]
ENVELOPES = ["Spier", "Ratigan", "DeVries", "Hunsche"]
THERMAL_MODES = ["none", "profile", "conduction_1d", "conduction_2d"]
THREADS = [1, 2, 4]


@dataclass(frozen=True)
class StandardCase:
    name: str
    lithology: str
    water_depth_m: float
    burial_m: float
    salt_above_m: float
    fluid_ppg: float
    k0: float
    total_h: float
    dt_h: float
    closure_min_pct: float
    closure_max_pct: float


@dataclass(frozen=True)
class BenchmarkSpec:
    base_case: StandardCase
    element: str
    model: str
    envelope: str | None
    thermal_mode: str
    threads: int
    n_radial: int
    n_axial: int
    ratio: float

    @property
    def case_name(self) -> str:
        parts = [
            "bench",
            self.base_case.name,
            self.element.replace("axisym_", "").replace("_", ""),
            self.model.lower().replace("_", ""),
            self.thermal_mode.replace("_", ""),
            f"omp{self.threads}",
        ]
        if self.envelope:
            parts.insert(4, self.envelope.lower())
        return "_".join(parts)


STANDARD_CASES = [
    StandardCase("modelo_A", "halita", 1600.0, 4100.0, 0.0, 9.6, 1.0, 12.0, 1.0, -25.0, 25.0),
    StandardCase("modelo_E", "taquidrita", 1600.0, 4100.0, 25.0, 18.0, 1.0, 2.0, 0.25, -100.0, 100.0),
    StandardCase("sestsal_base", "halita", 0.0, 5237.0, 0.0, 10.0, 1.0, 12.0, 1.0, -25.0, 25.0),
    StandardCase("sestsal_repasse", "halita", 500.0, 3500.0, 0.0, 12.0, 0.9, 12.0, 1.0, -25.0, 25.0),
    StandardCase("sestsal_project61", "halita", 800.0, 4600.0, 50.0, 11.5, 1.1, 12.0, 1.0, -40.0, 40.0),
]


def executable() -> Path:
    exe = ROOT / "build" / ("saltcreep.exe" if os.name == "nt" else "saltcreep")
    if not exe.exists():
        raise FileNotFoundError(f"Executable not found: {exe}")
    return exe


def is_1d(element: str) -> bool:
    return element == "axisym_1d_L3"


def is_valid_combination(spec: BenchmarkSpec) -> bool:
    if spec.thermal_mode == "conduction_1d" and not is_1d(spec.element):
        return False
    if spec.thermal_mode == "conduction_2d" and is_1d(spec.element):
        return False
    if spec.envelope is not None and spec.model != "Wang2004":
        return False
    if spec.model == "Wang2004" and spec.envelope not in ENVELOPES:
        return False
    if spec.model != "Wang2004" and spec.envelope is not None:
        return False
    return True


def default_mesh_for(element: str, preset: str) -> tuple[int, int, float]:
    if preset == "full":
        return (30 if is_1d(element) else 16, 2 if not is_1d(element) else 1, 100.0)
    if preset == "standard":
        return (10 if is_1d(element) else 6, 2 if not is_1d(element) else 1, 20.0)
    return (4 if is_1d(element) else 3, 1, 4.0)


def full_matrix(preset: str) -> list[BenchmarkSpec]:
    cases = STANDARD_CASES if preset == "full" else STANDARD_CASES[:1]
    specs: list[BenchmarkSpec] = []
    for base in cases:
        for element in ELEMENTS:
            n_radial, n_axial, ratio = default_mesh_for(element, preset)
            for model in MODELS:
                envelopes = ENVELOPES if model == "Wang2004" else [None]
                for envelope in envelopes:
                    for thermal_mode in THERMAL_MODES:
                        for threads in THREADS:
                            spec = BenchmarkSpec(
                                base, element, model, envelope, thermal_mode,
                                threads, n_radial, n_axial, ratio,
                            )
                            if is_valid_combination(spec):
                                specs.append(spec)
    return specs


def standard_matrix() -> list[BenchmarkSpec]:
    base = STANDARD_CASES[0]
    specs: list[BenchmarkSpec] = []

    for element in ELEMENTS:
        n_radial, n_axial, ratio = default_mesh_for(element, "standard")
        for threads in THREADS:
            specs.append(BenchmarkSpec(base, element, "DM", None, "none", threads,
                                       n_radial, n_axial, ratio))

    for model in MODELS:
        envelopes = ENVELOPES if model == "Wang2004" else [None]
        for envelope in envelopes:
            specs.append(BenchmarkSpec(base, "axisym_2d_Q8", model, envelope,
                                       "profile", 1, 6, 2, 20.0))

    for thermal_mode, element in [
        ("none", "axisym_1d_L3"),
        ("profile", "axisym_1d_L3"),
        ("conduction_1d", "axisym_1d_L3"),
        ("conduction_2d", "axisym_2d_Q8"),
    ]:
        n_radial, n_axial, ratio = default_mesh_for(element, "standard")
        specs.append(BenchmarkSpec(base, element, "DM", None, thermal_mode, 1,
                                   n_radial, n_axial, ratio))

    for case in STANDARD_CASES[1:]:
        specs.append(BenchmarkSpec(case, "axisym_1d_L3", "DM", None, "none", 1,
                                   10, 1, 20.0))

    unique: dict[str, BenchmarkSpec] = {}
    for spec in specs:
        if is_valid_combination(spec):
            unique[spec.case_name] = spec
    return list(unique.values())


def build_matrix(preset: str, max_runs: int | None = None) -> list[BenchmarkSpec]:
    if preset == "smoke":
        specs = [BenchmarkSpec(STANDARD_CASES[0], "axisym_1d_L3", "DM", None,
                               "none", 1, 3, 1, 2.0)]
    elif preset == "standard":
        specs = standard_matrix()
    elif preset == "full":
        specs = full_matrix("full")
    else:
        raise ValueError(f"Unknown preset: {preset}")
    return specs[:max_runs] if max_runs is not None else specs


def creep_yaml(spec: BenchmarkSpec) -> str:
    common = [
        "  elastic_only: false",
        f"  primary_model: {'isv_sh_dm' if spec.model == 'ISV_SH_DM' else 'EDMT'}",
        f"  tertiary_model: {'wang_2004' if spec.model == 'Wang2004' else 'aubertin_isv_sh_d' if spec.model == 'AubertinISV_SH_D' else 'MottaV1'}",
        f"  dilatancy_envelope: {spec.envelope or 'Spier'}",
    ]
    if spec.model == "DM":
        flags = ["  secondary: true", "  primary: false", "  tertiary: false", "  damage: false"]
    elif spec.model == "EDMT":
        flags = ["  secondary: true", "  primary: true", "  tertiary: false", "  damage: false"]
    elif spec.model == "ISV_SH_DM":
        flags = ["  secondary: true", "  primary: true", "  tertiary: false", "  damage: false"]
    elif spec.model == "Wang2004":
        flags = ["  secondary: true", "  primary: false", "  tertiary: true", "  damage: true"]
    elif spec.model == "AubertinISV_SH_D":
        flags = ["  secondary: true", "  primary: false", "  tertiary: true", "  damage: false"]
    else:
        raise ValueError(f"Unknown model: {spec.model}")
    return "\n".join(["creep:", *flags, *common])


def thermal_yaml(spec: BenchmarkSpec) -> str:
    mode = spec.thermal_mode
    if mode == "none":
        return """thermal:
  enabled: false
  mode: constant
  T_K: 359.15
  alpha_thermal: 0.0"""
    if mode == "profile":
        return """thermal:
  enabled: true
  mode: profile
  seabed_temp_C: 4.0
  grad_C_per_m: 0.01442
  alpha_thermal: 0.0"""
    if mode == "conduction_1d":
        return """thermal:
  enabled: true
  mode: conduction_1d
  initial_temp_C: 80.0
  inner_wall_temp_C: 90.0
  outer_bc: prescribed
  outer_temp_C: 60.0
  k_W_m_K: 5.4
  rho_kg_m3: 2160
  cp_J_kg_K: 860
  dt_thermal_h: 1.0
  beta: 0.5
  alpha_thermal: 0.0"""
    if mode == "conduction_2d":
        return """thermal:
  enabled: true
  mode: conduction_2d
  initial_temp_C: 80.0
  inner_wall_temp_C: 90.0
  outer_bc: prescribed
  outer_temp_C: 60.0
  top_bc: flux_zero
  bottom_bc: flux_zero
  k_W_m_K: 5.4
  rho_kg_m3: 2160
  cp_J_kg_K: 860
  dt_thermal_h: 1.0
  beta: 0.5
  alpha_thermal: 0.0
  layers:
    - z_top_m: 0.0
      z_bottom_m: 0.5
      k_W_per_mK: 5.4
      rho_kg_per_m3: 2160
      cp_J_per_kgK: 860
    - z_top_m: 0.5
      z_bottom_m: 1.0
      k_W_per_mK: 3.1
      rho_kg_per_m3: 1600
      cp_J_per_kgK: 920"""
    raise ValueError(f"Unknown thermal mode: {mode}")


def time_scheme_for(spec: BenchmarkSpec) -> str:
    if spec.model in {"Wang2004", "AubertinISV_SH_D"}:
        return "implicit_adaptive"
    if spec.base_case.lithology == "taquidrita":
        return "implicit_adaptive"
    return "explicit"


def case_yaml(spec: BenchmarkSpec) -> str:
    scheme = time_scheme_for(spec)
    return f"""name: {spec.case_name}

geometry:
  well_radius_m: 0.155575
  outer_radius_factor: 80

depths:
  water_depth_m: {spec.base_case.water_depth_m}
  burial_m: {spec.base_case.burial_m}
  salt_above_m: {spec.base_case.salt_above_m}

lithology:
  primary: {spec.base_case.lithology}

fluid:
  weight_lb_per_gal: {spec.base_case.fluid_ppg}

stress:
  k0: {spec.base_case.k0}
  overburden_grad_Pa_per_m: 21000

element:
  type: {spec.element}

mesh:
  n_elements_radial: {spec.n_radial}
  n_elements_axial: {spec.n_axial}
  ratio: {spec.ratio}

{creep_yaml(spec)}

{thermal_yaml(spec)}

time:
  total_h: {spec.base_case.total_h}
  dt_h: {spec.base_case.dt_h}
  scheme: {scheme}
  tol_local: 1.0e-9
  tol_global: 1.0e-4
  dt_min_h: 1.0e-8
  dt_max_h: {max(spec.base_case.dt_h, 1.0)}

output:
  every_n_steps: 1000000
  vtu: false
  damage_tracking: false
"""


def read_closure_final(result_dir: Path) -> float | None:
    closure_path = result_dir / "closure.csv"
    if not closure_path.exists():
        return None
    closure = pd.read_csv(closure_path)
    if closure.empty or "closure_pct" not in closure:
        return None
    return float(closure["closure_pct"].iloc[-1])


def validate_closure(spec: BenchmarkSpec, closure_final: float | None) -> tuple[bool, str]:
    if closure_final is None:
        return False, "closure.csv missing or empty"
    if not math.isfinite(closure_final):
        return False, "closure_final is not finite"
    if not (spec.base_case.closure_min_pct <= closure_final <= spec.base_case.closure_max_pct):
        return False, (
            f"closure_final={closure_final:.6g} outside "
            f"[{spec.base_case.closure_min_pct}, {spec.base_case.closure_max_pct}]"
        )
    return True, "ok"


def run_case(spec: BenchmarkSpec,
             output_dir: Path = RESULTS_DIR,
             timeout_s: int | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    case_dir = output_dir / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    case_path = case_dir / f"{spec.case_name}.yaml"
    case_path.write_text(case_yaml(spec), encoding="utf-8")

    result_dir = ROOT / "results" / spec.case_name
    shutil.rmtree(result_dir, ignore_errors=True)

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(spec.threads)
    env["SALTCREEP_OUTPUT_EVERY"] = "1000000"
    proc = subprocess.run(
        [str(executable()), str(case_path)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )

    row = {
        "case_name": spec.case_name,
        "base_case": spec.base_case.name,
        "element": spec.element,
        "model": spec.model,
        "envelope": spec.envelope or "",
        "thermal_mode": spec.thermal_mode,
        "requested_threads": spec.threads,
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }
    if proc.returncode != 0:
        return row

    metadata_path = result_dir / "metadata.json"
    if not metadata_path.exists():
        row.update({"status": "failed", "stderr_tail": "metadata.json not written"})
        return row

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    closure_final = read_closure_final(result_dir)
    closure_ok, closure_message = validate_closure(spec, closure_final)
    row.update({
        "metadata_path": str(metadata_path),
        "wall_time_s": float(metadata.get("wall_time_s", 0.0)),
        "time_assembly_s": float(metadata.get("time_assembly_s", 0.0)),
        "time_solve_s": float(metadata.get("time_solve_s", 0.0)),
        "time_constitutive_s": float(metadata.get("time_constitutive_s", 0.0)),
        "closure_final": closure_final,
        "n_dofs": int(metadata.get("n_dofs", 0)),
        "omp_threads": int(metadata.get("omp_threads", 0)),
        "time_scheme": metadata.get("time_scheme", ""),
        "thermal_enabled": bool(metadata.get("thermal_enabled", False)),
        "closure_check": closure_message,
    })
    if not closure_ok:
        row["status"] = "failed"
    return row


def run_suite(specs: Iterable[BenchmarkSpec],
              output_dir: Path = RESULTS_DIR,
              keep_going: bool = True,
              timeout_s: int | None = None) -> list[dict]:
    rows: list[dict] = []
    for index, spec in enumerate(specs, start=1):
        print(f"[{index}] {spec.case_name}")
        row = run_case(spec, output_dir=output_dir, timeout_s=timeout_s)
        rows.append(row)
        if row["status"] != "ok" and not keep_going:
            break
    return rows


def successful_frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df[df["status"] == "ok"].copy()


def markdown_table(df: pd.DataFrame, columns: list[str], floatfmt: str = ".4g") -> str:
    if df.empty:
        return "_Sem dados bem-sucedidos._"
    subset = df[columns].copy()

    def fmt(value: object) -> str:
        if isinstance(value, float):
            return format(value, floatfmt)
        return str(value)

    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| " + " | ".join(fmt(row[column]) for column in columns) + " |"
        for _, row in subset.iterrows()
    ]
    return "\n".join([header, rule, *rows])


def aggregate_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if df.empty:
        return {}
    tables: dict[str, pd.DataFrame] = {}
    tables["by_element"] = (
        df.groupby("element", dropna=False)
        .agg(
            runs=("case_name", "count"),
            mean_wall_time_s=("wall_time_s", "mean"),
            min_wall_time_s=("wall_time_s", "min"),
            max_wall_time_s=("wall_time_s", "max"),
            mean_n_dofs=("n_dofs", "mean"),
        )
        .reset_index()
        .sort_values("mean_wall_time_s")
    )
    tables["by_model"] = (
        df.groupby("model", dropna=False)
        .agg(
            runs=("case_name", "count"),
            mean_wall_time_s=("wall_time_s", "mean"),
            mean_assembly_s=("time_assembly_s", "mean"),
            mean_solve_s=("time_solve_s", "mean"),
            mean_constitutive_s=("time_constitutive_s", "mean"),
        )
        .reset_index()
        .sort_values("mean_wall_time_s")
    )
    mode = df[["base_case", "thermal_mode", "requested_threads"]].mode().iloc[0]
    common = df[
        (df["base_case"] == mode["base_case"]) &
        (df["thermal_mode"] == mode["thermal_mode"]) &
        (df["requested_threads"] == mode["requested_threads"])
    ].copy()
    tables["breakdown_common"] = common[
        ["case_name", "element", "model", "time_assembly_s",
         "time_solve_s", "time_constitutive_s", "wall_time_s"]
    ].sort_values("wall_time_s").head(20)

    key_cols = ["base_case", "element", "model", "envelope", "thermal_mode"]
    speed_rows = []
    for key, group in df.groupby(key_cols, dropna=False):
        baseline = group[group["requested_threads"] == 1]
        if baseline.empty:
            continue
        t1 = float(baseline["wall_time_s"].iloc[0])
        for _, row in group.iterrows():
            speed_rows.append({
                "base_case": key[0],
                "element": key[1],
                "model": key[2],
                "envelope": key[3],
                "thermal_mode": key[4],
                "threads": int(row["requested_threads"]),
                "wall_time_s": float(row["wall_time_s"]),
                "speedup": t1 / float(row["wall_time_s"]) if row["wall_time_s"] > 0 else math.nan,
            })
    tables["speedup"] = pd.DataFrame(speed_rows).sort_values(
        ["base_case", "element", "model", "thermal_mode", "threads"]
    )
    tables["dofs_by_element"] = (
        df.groupby("element", dropna=False)
        .agg(
            runs=("case_name", "count"),
            mean_n_dofs=("n_dofs", "mean"),
            min_n_dofs=("n_dofs", "min"),
            max_n_dofs=("n_dofs", "max"),
        )
        .reset_index()
        .sort_values("mean_n_dofs")
    )
    return tables


def plot_time_vs_dofs(df: pd.DataFrame, output_dir: Path) -> None:
    if df.empty:
        return
    plt.figure(figsize=(7.2, 4.8))
    for element, group in df.groupby("element"):
        plt.scatter(group["n_dofs"], group["wall_time_s"], label=element, s=42, alpha=0.8)
    plt.xlabel("GDLs")
    plt.ylabel("Tempo total [s]")
    plt.title("Benchmark: tempo vs GDLs")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=8)
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "benchmark_time_vs_dofs.png", dpi=300, bbox_inches="tight")
    plt.savefig(output_dir / "benchmark_time_vs_dofs.pdf", bbox_inches="tight")
    plt.close()


def write_report(rows: list[dict], output_dir: Path = RESULTS_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = successful_frame(rows)
    tables = aggregate_tables(df)
    plot_time_vs_dofs(df, output_dir)

    report = [
        "# Benchmark suite SaltCreep",
        "",
        f"Gerado em: {datetime.now(timezone.utc).isoformat()}",
        f"Execuções: {len(rows)} total, {len(df)} verdes, {len(rows) - len(df)} falhas.",
        "",
        "## Tabela 1 — tempo total vs elemento",
        markdown_table(tables.get("by_element", pd.DataFrame()),
                       ["element", "runs", "mean_wall_time_s", "min_wall_time_s",
                        "max_wall_time_s", "mean_n_dofs"]),
        "",
        "## Tabela 2 — tempo total vs modelo",
        markdown_table(tables.get("by_model", pd.DataFrame()),
                       ["model", "runs", "mean_wall_time_s", "mean_assembly_s",
                        "mean_solve_s", "mean_constitutive_s"]),
        "",
        "## Tabela 3 — breakdown da configuração mais comum",
        markdown_table(tables.get("breakdown_common", pd.DataFrame()),
                       ["case_name", "element", "model", "time_assembly_s",
                        "time_solve_s", "time_constitutive_s", "wall_time_s"]),
        "",
        "## Tabela 4 — speedup OpenMP",
        markdown_table(tables.get("speedup", pd.DataFrame()).head(60),
                       ["base_case", "element", "model", "envelope",
                        "thermal_mode", "threads", "wall_time_s", "speedup"]),
        "",
        "## Tabela 5 — GDLs finais vs elemento",
        markdown_table(tables.get("dofs_by_element", pd.DataFrame()),
                       ["element", "runs", "mean_n_dofs", "min_n_dofs", "max_n_dofs"]),
        "",
        "## Gráfico",
        "",
        "- `benchmark_time_vs_dofs.png/pdf`: tempo total vs GDLs.",
    ]

    failed = [row for row in rows if row.get("status") != "ok"]
    if failed:
        report.extend(["", "## Falhas", ""])
        for row in failed[:50]:
            report.append(
                f"- `{row.get('case_name')}`: returncode={row.get('returncode')} "
                f"status={row.get('status')} check={row.get('closure_check', '')}"
            )

    path = output_dir / "benchmark_report.md"
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return path


def write_json(rows: list[dict], preset: str, output_dir: Path = RESULTS_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "preset": preset,
        "n_runs": len(rows),
        "n_success": sum(1 for row in rows if row.get("status") == "ok"),
        "results": rows,
    }
    path = output_dir / "benchmark_suite.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=["smoke", "standard", "full"], default="standard")
    parser.add_argument("--max-runs", type=int, default=None,
                        help="Limit the number of generated runs.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only write the planned matrix JSON, do not run the solver.")
    parser.add_argument("--stop-on-failure", action="store_true")
    parser.add_argument("--timeout-s", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    specs = build_matrix(args.preset, args.max_runs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = args.output_dir / "benchmark_plan.json"
    plan_path.write_text(
        json.dumps([spec.__dict__ | {"base_case": spec.base_case.__dict__}
                    for spec in specs], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if args.dry_run:
        print(f"Plano salvo em {plan_path} ({len(specs)} casos)")
        return 0

    rows = run_suite(
        specs,
        output_dir=args.output_dir,
        keep_going=not args.stop_on_failure,
        timeout_s=args.timeout_s,
    )
    json_path = write_json(rows, args.preset, args.output_dir)
    report_path = write_report(rows, args.output_dir)
    failures = sum(1 for row in rows if row.get("status") != "ok")
    print(f"Resultados: {json_path}")
    print(f"Relatório: {report_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
