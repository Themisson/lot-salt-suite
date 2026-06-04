"""Benchmark wall-pressure evaluation modes on 2D axisymmetric meshes.

This script isolates the overhead of evaluating the pressure applied at the
well wall. It compares constant pressure, hydrostatic mud-weight pressure, and
time/depth CSV pressure on the same Q8 mechanical mesh.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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
RESULTS_DIR = ROOT / "results" / "benchmark_wall_pressure"
CSV_SCHEDULE = ROOT / "data" / "apb" / "mud_schedule_example.csv"

FLUID_MODES = ["constant", "hydrostatic_depth_profile", "csv_time_depth_profile"]
DEFAULT_THREADS = [1]


@dataclass(frozen=True)
class MeshSpec:
    label: str
    n_radial: int
    n_axial: int
    ratio: float


@dataclass(frozen=True)
class WallPressureSpec:
    fluid_mode: str
    mesh: MeshSpec
    threads: int
    total_h: float = 2.0
    dt_h: float = 0.5

    @property
    def case_name(self) -> str:
        mode = self.fluid_mode.replace("_depth_profile", "").replace("_time_depth_profile", "")
        return (
            f"bench_wall_pressure_{mode}_q8_"
            f"{self.mesh.n_radial}x{self.mesh.n_axial}_omp{self.threads}"
        )


def executable() -> Path:
    exe = ROOT / "build" / ("saltcreep.exe" if os.name == "nt" else "saltcreep")
    if not exe.exists():
        raise FileNotFoundError(f"Executable not found: {exe}")
    return exe


def parse_threads(value: str) -> list[int]:
    threads = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not threads or any(thread <= 0 for thread in threads):
        raise argparse.ArgumentTypeError("threads must be a comma-separated list of positive integers")
    return threads


def meshes_for_preset(preset: str) -> list[MeshSpec]:
    if preset == "smoke":
        return [MeshSpec("tiny", 3, 1, 10.0)]
    if preset == "standard":
        return [
            MeshSpec("small", 4, 2, 20.0),
            MeshSpec("medium", 6, 4, 50.0),
            MeshSpec("large", 8, 6, 80.0),
        ]
    if preset == "full":
        return [
            MeshSpec("small", 4, 2, 20.0),
            MeshSpec("medium", 6, 4, 50.0),
            MeshSpec("large", 8, 6, 80.0),
            MeshSpec("xlarge", 12, 8, 120.0),
        ]
    raise ValueError(f"Unknown preset: {preset}")


def build_specs(preset: str, threads: Iterable[int] | None = None,
                max_runs: int | None = None) -> list[WallPressureSpec]:
    thread_values = list(threads) if threads is not None else DEFAULT_THREADS
    specs = [
        WallPressureSpec(fluid_mode, mesh, thread)
        for mesh in meshes_for_preset(preset)
        for fluid_mode in FLUID_MODES
        for thread in thread_values
    ]
    return specs[:max_runs] if max_runs is not None else specs


def fluid_yaml(spec: WallPressureSpec) -> str:
    if spec.fluid_mode == "constant":
        return """fluid:
  mode: constant
  pressure_Pa: 4.85e7"""
    if spec.fluid_mode == "hydrostatic_depth_profile":
        return """fluid:
  mode: hydrostatic_depth_profile
  weight_lb_per_gal: 10.0
  surface_pressure_Pa: 0.0"""
    if spec.fluid_mode == "csv_time_depth_profile":
        return f"""fluid:
  mode: csv_time_depth_profile
  csv: {CSV_SCHEDULE.as_posix()}
  pressure_column: p_wall_Pa
  time_column: t_h
  z_column: z_m"""
    raise ValueError(f"Unknown fluid mode: {spec.fluid_mode}")


def case_yaml(spec: WallPressureSpec) -> str:
    return f"""name: {spec.case_name}

geometry:
  well_radius_m: 0.155575
  outer_radius_factor: 100
  layer_thickness_m: 1000

depths:
  water_depth_m: 1600
  burial_m: 2500
  salt_above_m: 0

lithology:
  primary: halita
  layers:
    - z_top_m: 0
      z_bottom_m: 350
      material: halita
      label: Halita superior
    - z_top_m: 350
      z_bottom_m: 430
      material: carnalita
      label: Carnalita
    - z_top_m: 430
      z_bottom_m: 760
      material: halita
      label: Halita media
    - z_top_m: 760
      z_bottom_m: 840
      material: taquidrita
      label: Taquidrita
    - z_top_m: 840
      z_bottom_m: 1000
      material: halita
      label: Halita inferior

{fluid_yaml(spec)}

stress:
  k0: 1.0
  geostatic_mode: depth_profile

element:
  type: axisym_2d_Q8

mesh:
  n_elements_radial: {spec.mesh.n_radial}
  n_elements_axial: {spec.mesh.n_axial}
  ratio: {spec.mesh.ratio}

creep:
  elastic_only: false
  secondary: false
  primary: false
  tertiary: false
  damage: false

thermal:
  enabled: false
  mode: constant
  T_K: 359.15
  alpha_thermal: 0.0

time:
  scheme: explicit
  total_h: {spec.total_h}
  dt_h: {spec.dt_h}

output:
  every_n_steps: 1
  vtu: false
"""


def write_case(spec: WallPressureSpec, output_dir: Path) -> Path:
    case_dir = output_dir / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    path = case_dir / f"{spec.case_name}.yaml"
    path.write_text(case_yaml(spec), encoding="utf-8")
    return path


def closure_final(result_dir: Path) -> float:
    path = result_dir / "closure.csv"
    if not path.exists():
        return math.nan
    df = pd.read_csv(path)
    if df.empty:
        return math.nan
    for column in ("closure_pct", "closure_percent"):
        if column in df.columns:
            return float(df[column].iloc[-1])
    return float(df.iloc[-1, 1])


def pressure_span(result_dir: Path) -> tuple[float, float]:
    path = result_dir / "wall_pressure_profile.csv"
    if not path.exists():
        return (math.nan, math.nan)
    df = pd.read_csv(path)
    if df.empty or "p_wall_Pa" not in df.columns:
        return (math.nan, math.nan)
    return (float(df["p_wall_Pa"].min()), float(df["p_wall_Pa"].max()))


def run_case(spec: WallPressureSpec, output_dir: Path = RESULTS_DIR,
             timeout_s: int | None = None) -> dict:
    case_path = write_case(spec, output_dir)
    result_dir = ROOT / "results" / spec.case_name
    shutil.rmtree(result_dir, ignore_errors=True)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(spec.threads)
    proc = subprocess.run(
        [str(executable()), str(case_path)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        check=False,
    )
    row = {
        "case_name": spec.case_name,
        "fluid_mode": spec.fluid_mode,
        "mesh_label": spec.mesh.label,
        "n_elements_radial": spec.mesh.n_radial,
        "n_elements_axial": spec.mesh.n_axial,
        "mesh_ratio": spec.mesh.ratio,
        "requested_threads": spec.threads,
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1500:],
        "stderr_tail": proc.stderr[-1500:],
        "case_path": str(case_path),
        "result_dir": str(result_dir),
    }
    metadata_path = result_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        row.update({
            "metadata_path": str(metadata_path),
            "wall_time_s": float(metadata.get("wall_time_s", 0.0)),
            "time_assembly_s": float(metadata.get("time_assembly_s", 0.0)),
            "time_solve_s": float(metadata.get("time_solve_s", 0.0)),
            "time_constitutive_s": float(metadata.get("time_constitutive_s", 0.0)),
            "n_dofs": int(metadata.get("n_dofs", 0)),
            "omp_threads": int(metadata.get("omp_threads", 0)),
            "element_type": metadata.get("element_type", "axisym_2d_Q8"),
            "fluid_csv": metadata.get("fluid_csv", ""),
        })
    else:
        row["status"] = "failed"
    p_min, p_max = pressure_span(result_dir)
    row["closure_final"] = closure_final(result_dir)
    row["p_wall_min_Pa"] = p_min
    row["p_wall_max_Pa"] = p_max
    return row


def run_suite(specs: Iterable[WallPressureSpec], output_dir: Path = RESULTS_DIR,
              keep_going: bool = True, timeout_s: int | None = None) -> list[dict]:
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


def add_overhead(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["overhead_vs_constant_pct"] = 0.0
    keys = ["mesh_label", "requested_threads"]
    for _, group in df.groupby(keys):
        base = group[group["fluid_mode"] == "constant"]
        if base.empty:
            continue
        t0 = float(base["wall_time_s"].iloc[0])
        mask = group.index
        if t0 > 0:
            df.loc[mask, "overhead_vs_constant_pct"] = (
                (df.loc[mask, "wall_time_s"] / t0 - 1.0) * 100.0
            )
    return df


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
    body = [
        "| " + " | ".join(fmt(row[column]) for column in columns) + " |"
        for _, row in subset.iterrows()
    ]
    return "\n".join([header, rule, *body])


def plot_outputs(df: pd.DataFrame, output_dir: Path) -> None:
    if df.empty:
        return
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7.2, 4.8))
    for mode, group in df.groupby("fluid_mode"):
        ordered = group.sort_values("n_dofs")
        plt.plot(ordered["n_dofs"], ordered["wall_time_s"], marker="o", label=mode)
    plt.xlabel("GDLs")
    plt.ylabel("Tempo total [s]")
    plt.title("Custo do carregamento de parede")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_dir / "wall_pressure_time_vs_dofs.png", dpi=300, bbox_inches="tight")
    plt.savefig(output_dir / "wall_pressure_time_vs_dofs.pdf", bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7.2, 4.8))
    for mode, group in df.groupby("fluid_mode"):
        if mode == "constant":
            continue
        ordered = group.sort_values("n_dofs")
        plt.plot(
            ordered["n_dofs"],
            ordered["overhead_vs_constant_pct"],
            marker="s",
            label=mode,
        )
    plt.axhline(0.0, color="#666666", linestyle="--", linewidth=1.0)
    plt.xlabel("GDLs")
    plt.ylabel("Sobrecusto vs pressão constante [%]")
    plt.title("Sobrecusto de p_wall(z,t)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_dir / "wall_pressure_overhead_vs_dofs.png", dpi=300, bbox_inches="tight")
    plt.savefig(output_dir / "wall_pressure_overhead_vs_dofs.pdf", bbox_inches="tight")
    plt.close()

    breakdown = df.sort_values(["mesh_label", "fluid_mode"])
    plt.figure(figsize=(8.0, 4.8))
    labels = [f"{row.mesh_label}\n{row.fluid_mode.replace('_', ' ')}" for row in breakdown.itertuples()]
    bottom = [0.0] * len(breakdown)
    for column, label, color in [
        ("time_assembly_s", "Montagem", "#1f77b4"),
        ("time_solve_s", "Solve", "#ff7f0e"),
        ("time_constitutive_s", "Constitutivo", "#2ca02c"),
    ]:
        values = breakdown[column].fillna(0.0).to_numpy()
        plt.bar(labels, values, bottom=bottom, label=label, color=color)
        bottom = [b + float(v) for b, v in zip(bottom, values)]
    plt.ylabel("Tempo [s]")
    plt.title("Breakdown por modo de pressão")
    plt.xticks(rotation=30, ha="right")
    plt.grid(True, axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "wall_pressure_breakdown.png", dpi=300, bbox_inches="tight")
    plt.savefig(output_dir / "wall_pressure_breakdown.pdf", bbox_inches="tight")
    plt.close()


def write_json(rows: list[dict], preset: str, output_dir: Path = RESULTS_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "preset": preset,
        "n_runs": len(rows),
        "n_success": sum(1 for row in rows if row.get("status") == "ok"),
        "results": rows,
    }
    path = output_dir / "benchmark_wall_pressure.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_report(rows: list[dict], output_dir: Path = RESULTS_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = add_overhead(successful_frame(rows))
    if not df.empty:
        df.to_csv(output_dir / "benchmark_wall_pressure.csv", index=False)
        plot_outputs(df, output_dir)

    summary = (
        df.groupby("fluid_mode", dropna=False)
        .agg(
            runs=("case_name", "count"),
            mean_wall_time_s=("wall_time_s", "mean"),
            mean_overhead_pct=("overhead_vs_constant_pct", "mean"),
            mean_n_dofs=("n_dofs", "mean"),
        )
        .reset_index()
        .sort_values("mean_wall_time_s")
        if not df.empty else pd.DataFrame()
    )
    by_mesh = (
        df.sort_values(["mesh_label", "fluid_mode"])[
            ["mesh_label", "fluid_mode", "n_dofs", "wall_time_s",
             "overhead_vs_constant_pct", "p_wall_min_Pa", "p_wall_max_Pa"]
        ]
        if not df.empty else pd.DataFrame()
    )

    report = [
        "# Benchmark de pressão na parede",
        "",
        f"Gerado em: {datetime.now(timezone.utc).isoformat()}",
        f"Execuções: {len(rows)} total, {len(df)} verdes, {len(rows) - len(df)} falhas.",
        "",
        "## Objetivo",
        "",
        "Comparar o custo de avaliar a pressão na parede como valor constante, perfil "
        "hidrostático por peso de lama e grade CSV `p_wall(t,z)` em malhas Q8 2D.",
        "",
        "## Resumo por modo",
        markdown_table(summary, ["fluid_mode", "runs", "mean_wall_time_s",
                                 "mean_overhead_pct", "mean_n_dofs"]),
        "",
        "## Detalhe por malha",
        markdown_table(by_mesh, ["mesh_label", "fluid_mode", "n_dofs", "wall_time_s",
                                 "overhead_vs_constant_pct", "p_wall_min_Pa",
                                 "p_wall_max_Pa"]),
        "",
        "## Arquivos gerados",
        "",
        "- `benchmark_wall_pressure.json`: resultados brutos e caminhos de cada caso.",
        "- `benchmark_wall_pressure.csv`: tabela plana para planilhas.",
        "- `wall_pressure_time_vs_dofs.png/pdf`: tempo total vs GDLs.",
        "- `wall_pressure_overhead_vs_dofs.png/pdf`: sobrecusto vs pressão constante.",
        "- `wall_pressure_breakdown.png/pdf`: montagem/solve/constitutivo por modo.",
    ]
    failed = [row for row in rows if row.get("status") != "ok"]
    if failed:
        report.extend(["", "## Falhas", ""])
        for row in failed[:40]:
            report.append(
                f"- `{row.get('case_name')}`: returncode={row.get('returncode')} "
                f"stderr={row.get('stderr_tail', '')[-300:]}"
            )
    path = output_dir / "benchmark_wall_pressure.md"
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return path


def write_plan(specs: list[WallPressureSpec], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = [
        {
            "case_name": spec.case_name,
            "fluid_mode": spec.fluid_mode,
            "threads": spec.threads,
            "mesh": spec.mesh.__dict__,
            "total_h": spec.total_h,
            "dt_h": spec.dt_h,
        }
        for spec in specs
    ]
    path = output_dir / "benchmark_wall_pressure_plan.json"
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=["smoke", "standard", "full"], default="standard")
    parser.add_argument("--threads", type=parse_threads, default=DEFAULT_THREADS,
                        help="Comma-separated OpenMP thread counts, e.g. 1,2,4.")
    parser.add_argument("--max-runs", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    parser.add_argument("--timeout-s", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    specs = build_specs(args.preset, args.threads, args.max_runs)
    plan_path = write_plan(specs, args.output_dir)
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
