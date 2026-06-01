"""Run OpenMP scaling benchmarks for saltcreep."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "benchmark"
CASE_TEMPLATE = ROOT / "cases" / "tcc" / "modelo_A_Q8.yaml"


def executable() -> Path:
    exe = ROOT / "build" / ("saltcreep.exe" if os.name == "nt" else "saltcreep")
    if not exe.exists():
        raise FileNotFoundError(f"Executable not found: {exe}")
    return exe


def write_case(thread_count: int) -> Path:
    text = CASE_TEMPLATE.read_text(encoding="utf-8")
    case_name = f"benchmark_modelo_A_Q8_omp{thread_count}"
    text = re.sub(r"^name:\s+.*$", f"name: {case_name}", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^(\s*)total_h:\s+.*$", r"\g<1>total_h: 480", text, count=1, flags=re.MULTILINE)
    text = re.sub(
        r"^(\s*)every_n_steps:\s+.*$",
        r"\g<1>every_n_steps: 999999",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = text.replace("    - until_h: 360.0\n      dt_h: 1.0e-1",
                        "    - until_h: 480.0\n      dt_h: 1.0e-1")
    case_dir = RESULTS / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    case_path = case_dir / f"{case_name}.yaml"
    case_path.write_text(text, encoding="utf-8")
    return case_path


def run_case(thread_count: int) -> dict:
    case_path = write_case(thread_count)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(thread_count)
    env["SALTCREEP_OUTPUT_EVERY"] = "999999"
    subprocess.run([str(executable()), str(case_path)], cwd=ROOT, env=env, check=True)

    metadata_path = ROOT / "results" / case_path.stem / "metadata.json"
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    return {
        "threads": thread_count,
        "case_name": metadata["case_name"],
        "wall_time_s": metadata.get("wall_time_s", 0.0),
        "time_assembly_s": metadata.get("time_assembly_s", 0.0),
        "time_solve_s": metadata.get("time_solve_s", 0.0),
        "time_constitutive_s": metadata.get("time_constitutive_s", 0.0),
        "omp_threads_reported": metadata.get("omp_threads"),
    }


def plot_outputs(df: pd.DataFrame) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    baseline = float(df.loc[df["threads"] == 1, "wall_time_s"].iloc[0])
    df["speedup"] = baseline / df["wall_time_s"]
    df.to_csv(RESULTS / "benchmark_openmp.csv", index=False)

    plt.figure(figsize=(7.0, 4.5))
    plt.plot(df["threads"], df["speedup"], marker="o", linewidth=1.5)
    plt.plot(df["threads"], df["threads"], linestyle="--", color="#888888", label="ideal")
    plt.xlabel("Threads OpenMP")
    plt.ylabel("Speedup")
    plt.title("Speedup OpenMP - modelo_A Q8")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(RESULTS / "speedup_vs_threads.png", dpi=300, bbox_inches="tight")
    plt.savefig(RESULTS / "speedup_vs_threads.pdf", bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7.0, 4.5))
    bottom = pd.Series([0.0] * len(df), index=df.index)
    for column, label, color in [
        ("time_assembly_s", "Montagem", "#1f77b4"),
        ("time_solve_s", "Solve", "#ff7f0e"),
        ("time_constitutive_s", "Constitutivo", "#2ca02c"),
    ]:
        plt.bar(df["threads"].astype(str), df[column], bottom=bottom, label=label, color=color)
        bottom += df[column]
    plt.xlabel("Threads OpenMP")
    plt.ylabel("Tempo [s]")
    plt.title("Breakdown de tempo - modelo_A Q8")
    plt.grid(True, axis="y", alpha=0.3)
    plt.legend()
    plt.savefig(RESULTS / "time_breakdown.png", dpi=300, bbox_inches="tight")
    plt.savefig(RESULTS / "time_breakdown.pdf", bbox_inches="tight")
    plt.close()


def main() -> int:
    rows = [run_case(threads) for threads in (1, 2, 4)]
    df = pd.DataFrame(rows)
    plot_outputs(df)
    print(f"Benchmark salvo em {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
