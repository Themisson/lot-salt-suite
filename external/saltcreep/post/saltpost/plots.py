"""Publication-style plots for saltcreep comparisons."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .compare import align_series, comparison_table
from .export import write_table_formats
from .io import CaseResult
from .registry import label_for
from .style import FIGSIZE, apply_style, color_for, get_color, get_marker, marker_for
from .units import auto_displacement_unit


def save_figure(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def _all_elements_same(results: list[CaseResult]) -> bool:
    elements = {r.element_type for r in results}
    return len(elements) <= 1


def plot_closure(results: list[CaseResult], out_dir: Path,
                 group_by: str | None = None) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(results)
    for idx, result in enumerate(results):
        if result.closure is None:
            continue
        ax.plot(
            result.closure["t_h"],
            result.closure["closure_pct"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(result.closure) // 8, 1),
        )
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Fechamento [%]")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "closure_vs_tempo")


def plot_relative_error(results: list[CaseResult], reference: CaseResult,
                        out_dir: Path, group_by: str | None = None) -> None:
    if reference.closure is None:
        return
    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(results)
    for idx, result in enumerate(results):
        if result is reference or result.closure is None:
            continue
        aligned = align_series(reference.closure, result.closure)
        ax.plot(
            aligned["t_h"],
            aligned["relative_error"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(aligned) // 8, 1),
        )
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Erro relativo")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "erro_relativo_vs_tempo")


def plot_final_closure_vs_dofs(results: list[CaseResult], out_dir: Path) -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(results)
    for idx, result in enumerate(results):
        if result.final_closure is None or result.n_dofs is None:
            continue
        ax.scatter(
            result.n_dofs,
            result.final_closure,
            label=label_for(result, None),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            s=48,
        )
    ax.set_xlabel("Graus de liberdade")
    ax.set_ylabel("Fechamento final [%]")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "fechamento_final_vs_gdls")


def _selected_times(df: pd.DataFrame, target_h: float | None = None) -> list[float]:
    times = sorted(float(t) for t in df["t_h"].dropna().unique())
    if not times:
        return []
    if target_h is not None:
        return [min(times, key=lambda t: abs(t - target_h))]

    final = times[-1]
    targets = [0.0, 0.25 * final, 0.5 * final, 0.75 * final, final]
    selected: list[float] = []
    for target in targets:
        closest = min(times, key=lambda t: abs(t - target))
        if closest not in selected:
            selected.append(closest)
    return selected


def _time_label(t_h: float) -> str:
    if abs(t_h) < 1.0e-12:
        return "0 h"
    if t_h < 1.0:
        return f"{t_h:.3g} h"
    return f"{t_h:.4g} h"


def _profile_for_time(df: pd.DataFrame, t_h: float) -> pd.DataFrame:
    times = df["t_h"].to_numpy(dtype=float)
    actual = float(df.iloc[np.argmin(np.abs(times - t_h))]["t_h"])
    return df[np.isclose(df["t_h"], actual)].copy()


def plot_wall_displacement(results: list[CaseResult], out_dir: Path,
                           group_by: str | None = None) -> None:
    series = [r for r in results if r.closure is not None and "u_wall_m" in r.closure]
    if not series:
        return

    max_u = max(float(r.closure["u_wall_m"].abs().max()) for r in series)
    scale, unit = auto_displacement_unit(max_u)
    radius = next((r.inner_radius_m for r in series if r.inner_radius_m is not None), None)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(series)
    for idx, result in enumerate(series):
        ax.plot(
            result.closure["t_h"],
            result.closure["u_wall_m"] * scale,
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(result.closure) // 8, 1),
        )
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel(f"Deslocamento radial [{unit}]")
    if radius is not None:
        ax.set_title(f"Deslocamento radial na parede (Ri = {radius:.6g} m)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "deslocamento_parede_vs_tempo")


def plot_radial_profile(result: CaseResult, out_dir: Path,
                        target_h: float | None = None) -> None:
    df = result.displacement_profile
    if df is None or df.empty:
        return

    selected = _selected_times(df, target_h)
    if not selected:
        return
    max_u = float(df["u_r_m"].abs().max())
    scale, unit = auto_displacement_unit(max_u)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for idx, t_h in enumerate(selected):
        frame = _profile_for_time(df, t_h)
        radial = (
            frame.groupby("r_m", as_index=False)["u_r_m"]
            .mean()
            .sort_values("r_m")
        )
        ax.plot(
            radial["r_m"],
            radial["u_r_m"] * scale,
            label=_time_label(float(frame["t_h"].iloc[0])),
            color=color_for(None, idx),
            marker=marker_for(None, idx),
            markevery=max(len(radial) // 8, 1),
        )
    ax.set_xlabel("Raio [m]")
    ax.set_ylabel(f"Deslocamento radial [{unit}]")
    ax.set_title(f"Perfil radial de deslocamento - {result.case_name}")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Tempo")
    save_figure(fig, out_dir, f"{result.case_name}_perfil_radial_ur")


def plot_wall_profile(result: CaseResult, out_dir: Path,
                      target_h: float | None = None) -> None:
    df = result.wall_profile
    if df is None or df.empty:
        return

    selected = _selected_times(df, target_h)
    if not selected:
        return
    max_u = float(df["u_r_m"].abs().max())
    scale, unit = auto_displacement_unit(max_u)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for idx, t_h in enumerate(selected):
        frame = _profile_for_time(df, t_h).sort_values("z_m")
        ax.plot(
            frame["u_r_m"] * scale,
            frame["z_m"],
            label=_time_label(float(frame["t_h"].iloc[0])),
            color=color_for(None, idx),
            marker=marker_for(None, idx),
            markevery=max(len(frame) // 8, 1),
        )
    ax.set_xlabel(f"Deslocamento radial [{unit}]")
    ax.set_ylabel("Profundidade local z [m]")
    ax.set_title(f"Perfil vertical na parede - {result.case_name}")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Tempo")
    save_figure(fig, out_dir, f"{result.case_name}_perfil_parede_ur")


def plot_field_map(result: CaseResult, out_dir: Path,
                   target_h: float | None = None) -> None:
    df = result.displacement_profile
    if df is None or df.empty:
        return
    selected = _selected_times(df, target_h)
    if not selected:
        return
    frame = _profile_for_time(df, selected[0])
    if frame["z_m"].nunique() < 2 or frame["r_m"].nunique() < 2:
        return

    max_u = float(frame["u_r_m"].abs().max())
    scale, unit = auto_displacement_unit(max_u)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    contour = ax.tricontourf(
        frame["r_m"],
        frame["z_m"],
        frame["u_r_m"] * scale,
        levels=24,
        cmap="coolwarm",
    )
    fig.colorbar(contour, ax=ax, label=f"Deslocamento radial [{unit}]")
    ax.set_xlabel("Raio [m]")
    ax.set_ylabel("Profundidade local z [m]")
    ax.set_title(f"Mapa u_r - {result.case_name} - {_time_label(float(frame['t_h'].iloc[0]))}")
    save_figure(fig, out_dir, f"{result.case_name}_mapa_ur")


def _damage_thresholds(result: CaseResult) -> list[float]:
    values = result.metadata.get("damage_thresholds") or [0.1, 0.3, 0.5, 0.8]
    failure = result.metadata.get("failure_D_critical")
    thresholds = [float(v) for v in values]
    if failure is not None:
        thresholds.append(float(failure))
    return sorted(set(round(v, 12) for v in thresholds if 0.0 < float(v) < 1.0))


def plot_damage_wall(results: list[CaseResult], out_dir: Path,
                     group_by: str | None = None) -> None:
    series = [r for r in results if r.damage_wall is not None and not r.damage_wall.empty]
    if not series:
        return

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(series)
    for idx, result in enumerate(series):
        ax.plot(
            result.damage_wall["t_h"],
            result.damage_wall["D"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(result.damage_wall) // 8, 1),
        )
    for threshold in _damage_thresholds(series[0]):
        ax.axhline(threshold, color="#666666", linestyle="--", linewidth=1.0, alpha=0.5)
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Dano D [-]")
    ax.set_title("Evolução do dano na parede")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "dano_parede_vs_tempo")


def plot_creep_rate(results: list[CaseResult], out_dir: Path,
                    group_by: str | None = None) -> None:
    series = [r for r in results if r.damage_wall is not None and not r.damage_wall.empty]
    if not series:
        return

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(series)
    for idx, result in enumerate(series):
        ax.semilogy(
            result.damage_wall["t_h"],
            result.damage_wall["eps_dot"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(result.damage_wall) // 8, 1),
        )
        if result.damage_events is not None and not result.damage_events.empty:
            infl = result.damage_events[result.damage_events["event_type"] == "inflection"]
            if not infl.empty:
                event = infl.iloc[0]
                ax.axvline(float(event["t_h"]), color=get_color(idx, result.element_type, all_same),
                           linestyle=":", linewidth=1.0, alpha=0.8)
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Taxa efetiva de fluência [1/s]")
    ax.set_title("Taxa de fluência na parede")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "taxa_fluencia_parede")


def plot_damage_comparison(results: list[CaseResult], out_dir: Path,
                           group_by: str | None = None) -> None:
    if len(results) < 2:
        return
    plot_closure(results, out_dir, group_by)


def plot_phase_space(results: list[CaseResult], out_dir: Path,
                     group_by: str | None = None) -> None:
    series = [r for r in results if r.damage_wall is not None and not r.damage_wall.empty]
    if not series:
        return

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same(series)
    for idx, result in enumerate(series):
        sigma_mpa = result.damage_wall["sigma_ef"] / 1.0e6
        ax.plot(
            sigma_mpa,
            result.damage_wall["D"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(result.damage_wall) // 8, 1),
        )
    ax.set_xlabel("Tensão efetiva [MPa]")
    ax.set_ylabel("Dano D [-]")
    ax.set_title("Espaço de fase tensão-dano")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "espaco_fase_sigmaef_D")


def write_comparison_outputs(results: list[CaseResult],
                             out_dir: Path,
                             reference: CaseResult | None = None,
                             output_format: str = "default") -> pd.DataFrame:
    table = comparison_table(results, reference)
    write_table_formats(table, out_dir, "comparison_table", output_format)
    return table
