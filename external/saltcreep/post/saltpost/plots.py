"""Publication-style plots for saltcreep comparisons."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .compare import align_series, comparison_table
from .diameter import diameter_at_depth, profile_at_time
from .export import write_table_formats
from .io import CaseResult
from .layers import color_for_lithology, normalized_layers
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


def _pressure_unit(max_p_pa: float) -> tuple[float, str]:
    if max_p_pa >= 1.0e6:
        return 1.0e-6, "MPa"
    if max_p_pa >= 1.0e3:
        return 1.0e-3, "kPa"
    return 1.0, "Pa"


def _profile_for_time(df: pd.DataFrame, t_h: float) -> pd.DataFrame:
    times = df["t_h"].to_numpy(dtype=float)
    actual = float(df.iloc[np.argmin(np.abs(times - t_h))]["t_h"])
    return df[np.isclose(df["t_h"], actual)].copy()


def _pressure_depth_column(df: pd.DataFrame) -> str:
    return "depth_m" if "depth_m" in df.columns else "z_m"


def _selected_depths(df: pd.DataFrame) -> list[float]:
    depth_col = _pressure_depth_column(df)
    depths = sorted(float(z) for z in df[depth_col].dropna().unique())
    if len(depths) <= 3:
        return depths
    targets = [depths[0], depths[len(depths) // 2], depths[-1]]
    selected: list[float] = []
    for target in targets:
        closest = min(depths, key=lambda z: abs(z - target))
        if closest not in selected:
            selected.append(closest)
    return selected


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


def plot_wall_pressure_profile(result: CaseResult, out_dir: Path,
                               target_h: float | None = None) -> None:
    df = result.wall_pressure_profile
    if df is None or df.empty or "p_wall_Pa" not in df:
        return

    selected = _selected_times(df, target_h)
    if not selected:
        return

    depth_col = _pressure_depth_column(df)
    max_p = float(df["p_wall_Pa"].abs().max())
    scale, unit = _pressure_unit(max_p)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for idx, t_h in enumerate(selected):
        frame = _profile_for_time(df, t_h).sort_values(depth_col)
        ax.plot(
            frame["p_wall_Pa"] * scale,
            frame[depth_col],
            label=_time_label(float(frame["t_h"].iloc[0])),
            color=color_for(None, idx),
            marker=marker_for(None, idx),
            markevery=max(len(frame) // 8, 1),
        )
    ax.set_xlabel(f"Pressão na parede [{unit}]")
    ax.set_ylabel("Profundidade [m]" if depth_col == "depth_m" else "z local [m]")
    ax.set_title(f"Perfil de pressão na parede - {result.case_name}")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(title="Tempo")
    save_figure(fig, out_dir, f"{result.case_name}_perfil_pressao_parede")


def plot_wall_pressure_time(result: CaseResult, out_dir: Path) -> None:
    df = result.wall_pressure_profile
    if df is None or df.empty or "p_wall_Pa" not in df:
        return

    depth_col = _pressure_depth_column(df)
    depths = _selected_depths(df)
    if not depths:
        return

    max_p = float(df["p_wall_Pa"].abs().max())
    scale, unit = _pressure_unit(max_p)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for idx, depth in enumerate(depths):
        depth_values = df[depth_col].to_numpy(dtype=float)
        actual = float(depth_values[np.argmin(np.abs(depth_values - depth))])
        series = df[np.isclose(df[depth_col], actual)].sort_values("t_h")
        ax.plot(
            series["t_h"],
            series["p_wall_Pa"] * scale,
            label=f"{depth_col}={actual:.4g} m",
            color=color_for(None, idx),
            marker=marker_for(None, idx),
            markevery=max(len(series) // 8, 1),
        )
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel(f"Pressão na parede [{unit}]")
    ax.set_title(f"Pressão na parede vs tempo - {result.case_name}")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Profundidade")
    save_figure(fig, out_dir, f"{result.case_name}_pressao_parede_vs_tempo")


def plot_wall_pressure_map(result: CaseResult, out_dir: Path) -> None:
    df = result.wall_pressure_profile
    if df is None or df.empty or "p_wall_Pa" not in df:
        return

    depth_col = _pressure_depth_column(df)
    if df["t_h"].nunique() < 2 or df[depth_col].nunique() < 2:
        return

    grouped = (
        df.groupby(["t_h", depth_col], as_index=False)["p_wall_Pa"]
        .mean()
        .sort_values(["t_h", depth_col])
    )
    pivot = grouped.pivot(index=depth_col, columns="t_h", values="p_wall_Pa")
    max_p = float(grouped["p_wall_Pa"].abs().max())
    scale, unit = _pressure_unit(max_p)

    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    mesh = ax.pcolormesh(
        pivot.columns.to_numpy(dtype=float),
        pivot.index.to_numpy(dtype=float),
        pivot.to_numpy(dtype=float) * scale,
        shading="auto",
        cmap="viridis",
    )
    fig.colorbar(mesh, ax=ax, label=f"Pressão na parede [{unit}]")
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Profundidade [m]" if depth_col == "depth_m" else "z local [m]")
    ax.set_title(f"Mapa p_wall(z,t) - {result.case_name}")
    ax.invert_yaxis()
    save_figure(fig, out_dir, f"{result.case_name}_mapa_pressao_parede")


def _add_lithology_bands(ax, result: CaseResult) -> None:
    layers = normalized_layers(result)
    if not layers:
        return
    x0, x1 = ax.get_xlim()
    span = x1 - x0
    text_x = x0 + 0.73 * span
    for idx, layer in enumerate(layers):
        top = -layer.absolute_top(result)
        bottom = -layer.absolute_bottom(result)
        ymin, ymax = sorted([top, bottom])
        ax.axhspan(
            ymin,
            ymax,
            color=color_for_lithology(layer.material, idx),
            alpha=0.10,
            linewidth=0,
            zorder=0,
        )
        ax.text(
            text_x,
            0.5 * (top + bottom),
            layer.label.capitalize(),
            ha="left",
            va="center",
            fontsize=10,
            alpha=0.85,
        )


def plot_wellbore_diameter_profile(results: list[CaseResult],
                                   out_dir: Path,
                                   target_h: float | None = None,
                                   group_by: str | None = None) -> None:
    series: list[tuple[CaseResult, pd.DataFrame]] = []
    for result in results:
        try:
            series.append((result, profile_at_time(result, target_h)))
        except ValueError:
            continue
    if not series:
        return

    apply_style()
    fig, ax = plt.subplots(figsize=(7.0, 7.2))
    all_same = _all_elements_same([result for result, _ in series])
    for idx, (result, frame) in enumerate(series):
        ax.plot(
            frame["diameter_in"],
            -frame["depth_m"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(frame) // 8, 1),
            zorder=3,
        )
    original = next(
        (float(frame["original_diameter_in"].iloc[0]) for _, frame in series
         if "original_diameter_in" in frame),
        None,
    )
    if original is not None:
        ax.axvline(original, color="#111111", linestyle="--", linewidth=1.5,
                   label="diametro original", zorder=2)
    _add_lithology_bands(ax, series[0][0])
    selected_t = float(series[0][1]["t_h"].iloc[0])
    ax.set_title(f"Diametro do poco - t = {_time_label(selected_t)}")
    ax.set_xlabel("Diametro [in]")
    ax.set_ylabel("Profundidade [m]")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "diametro_poco_vs_profundidade")


def plot_diameter_at_depth(results: list[CaseResult],
                           out_dir: Path,
                           depth_m: float | None = None,
                           group_by: str | None = None) -> None:
    series: list[tuple[CaseResult, pd.DataFrame]] = []
    for result in results:
        try:
            series.append((result, diameter_at_depth(result, depth_m)))
        except ValueError:
            continue
    if not series:
        return

    actual_depth = float(series[0][1]["depth_m"].iloc[0])
    apply_style()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    all_same = _all_elements_same([result for result, _ in series])
    for idx, (result, df) in enumerate(series):
        ax.plot(
            df["t_h"],
            df["diameter_in"],
            label=label_for(result, group_by),
            color=get_color(idx, result.element_type, all_same),
            marker=get_marker(idx, result.element_type, all_same),
            markevery=max(len(df) // 8, 1),
        )
    ax.set_title(f"Profundidade: {-actual_depth:.1f} m")
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Diametro [in]")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, out_dir, "diametro_vs_tempo_na_profundidade")


def plot_lithology_column(result: CaseResult, out_dir: Path) -> None:
    layers = normalized_layers(result)
    if not layers:
        return

    apply_style()
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.set_xlim(0.0, 1.0)
    y_values = []
    for idx, layer in enumerate(layers):
        top = -layer.absolute_top(result)
        bottom = -layer.absolute_bottom(result)
        ymin, ymax = sorted([top, bottom])
        y_values.extend([ymin, ymax])
        ax.axhspan(
            ymin,
            ymax,
            xmin=0.0,
            xmax=1.0,
            color=color_for_lithology(layer.material, idx),
            alpha=0.95,
        )
        ax.text(0.18, 0.5 * (top + bottom), layer.label.capitalize(),
                ha="center", va="center", fontsize=16)
        ax.text(0.65, 0.5 * (top + bottom),
                f"{layer.absolute_top(result):.0f}-{layer.absolute_bottom(result):.0f}",
                ha="center", va="center", fontsize=16)
    ax.set_xticks([])
    ax.set_ylabel("Profundidade [m]")
    ax.set_title(f"Coluna litologica - {result.case_name}")
    ax.set_ylim(min(y_values), max(y_values))
    save_figure(fig, out_dir, f"{result.case_name}_coluna_litologica")


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
