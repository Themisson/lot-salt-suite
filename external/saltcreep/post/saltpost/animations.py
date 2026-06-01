"""GIF/MP4 animations for saltcreep results."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
import numpy as np
import pandas as pd

from .io import CaseResult
from .style import apply_style
from .units import auto_displacement_unit
from .vtk import discover_vtu, has_pyvista, load_vtu


def _writer(output_format: str, fps: int):
    if output_format == "mp4" and FFMpegWriter.isAvailable():
        return FFMpegWriter(fps=fps)
    return PillowWriter(fps=fps)


def _extension(output_format: str) -> str:
    return ".mp4" if output_format == "mp4" and FFMpegWriter.isAvailable() else ".gif"


def _save_animation(
    fig: plt.Figure,
    update: Callable[[int], object],
    n_frames: int,
    out_path: Path,
    fps: int,
    output_format: str,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    animation = FuncAnimation(fig, update, frames=n_frames, interval=1000 / max(fps, 1))
    animation.save(out_path, writer=_writer(output_format, fps))
    plt.close(fig)
    return out_path


def animate_closure(
    result: CaseResult,
    out_dir: str | Path,
    fps: int = 4,
    output_format: str = "gif",
) -> Path | None:
    if result.closure is None or result.closure.empty:
        return None
    df = result.closure.sort_values("t_h")
    apply_style()
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    line, = ax.plot([], [], color="#1f77b4", marker="o", markevery=max(len(df) // 8, 1))
    ax.set_xlim(float(df["t_h"].min()), float(df["t_h"].max()))
    y_min = float(df["closure_pct"].min())
    y_max = float(df["closure_pct"].max())
    pad = max(abs(y_max - y_min) * 0.08, 1.0e-9)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.set_xlabel("Tempo [h]")
    ax.set_ylabel("Fechamento [%]")
    ax.grid(True, alpha=0.3)
    title = ax.set_title("")

    def update(frame: int):
        window = df.iloc[:frame + 1]
        line.set_data(window["t_h"], window["closure_pct"])
        title.set_text(f"{result.case_name} · t = {float(window['t_h'].iloc[-1]):.4g} h")
        return line, title

    suffix = _extension(output_format)
    return _save_animation(
        fig, update, len(df), Path(out_dir) / f"{result.case_name}_anim_closure{suffix}", fps, output_format
    )


def _selected_frames(df: pd.DataFrame, max_frames: int = 30) -> list[float]:
    times = sorted(float(t) for t in df["t_h"].dropna().unique())
    if len(times) <= max_frames:
        return times
    indices = np.linspace(0, len(times) - 1, max_frames).round().astype(int)
    return [times[int(i)] for i in indices]


def animate_ur(
    result: CaseResult,
    out_dir: str | Path,
    fps: int = 4,
    output_format: str = "gif",
) -> Path | None:
    df = result.displacement_profile
    if df is None or df.empty:
        return None

    times = _selected_frames(df)
    if not times:
        return None
    max_u = float(df["u_r_m"].abs().max())
    scale, unit = auto_displacement_unit(max_u)
    is_map = df["z_m"].nunique() > 1 and df["r_m"].nunique() > 1

    apply_style()
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    title = ax.set_title("")
    colorbar_created = False

    def update(frame_index: int):
        nonlocal colorbar_created
        ax.clear()
        t_h = times[frame_index]
        frame = df[np.isclose(df["t_h"], t_h)]
        if is_map:
            contour = ax.tricontourf(
                frame["r_m"], frame["z_m"], frame["u_r_m"] * scale,
                levels=24, cmap="coolwarm",
            )
            if not colorbar_created:
                fig.colorbar(contour, ax=ax, label=f"u_r [{unit}]")
                colorbar_created = True
            ax.set_xlabel("Raio [m]")
            ax.set_ylabel("Profundidade local z [m]")
        else:
            radial = frame.groupby("r_m", as_index=False)["u_r_m"].mean().sort_values("r_m")
            ax.plot(radial["r_m"], radial["u_r_m"] * scale, color="#1f77b4", marker="o")
            ax.set_xlabel("Raio [m]")
            ax.set_ylabel(f"u_r [{unit}]")
            ax.grid(True, alpha=0.3)
        ax.set_title(f"{result.case_name} · u_r · t = {t_h:.4g} h")
        return title,

    suffix = _extension(output_format)
    return _save_animation(
        fig, update, len(times), Path(out_dir) / f"{result.case_name}_anim_ur{suffix}", fps, output_format
    )


def animate_vtu_scalar(
    result: CaseResult,
    scalar: str,
    out_dir: str | Path,
    fps: int = 4,
    output_format: str = "gif",
) -> Path | None:
    vtus = discover_vtu(result.path)
    if not vtus or not has_pyvista():
        return None

    frames = []
    for vtu in vtus[:30]:
        mesh = load_vtu(vtu)
        if scalar not in mesh.point_data:
            continue
        points = np.asarray(mesh.points)
        values = np.asarray(mesh.point_data[scalar])
        frames.append((vtu, points[:, 0], points[:, 1], values))
    if not frames:
        return None

    apply_style()
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    v_min = min(float(np.nanmin(v)) for _, _, _, v in frames)
    v_max = max(float(np.nanmax(v)) for _, _, _, v in frames)
    colorbar_created = False

    def update(frame_index: int):
        nonlocal colorbar_created
        ax.clear()
        vtu, x, y, values = frames[frame_index]
        contour = ax.tricontourf(x, y, values, levels=24, cmap="viridis",
                                 vmin=v_min, vmax=v_max)
        if not colorbar_created:
            fig.colorbar(contour, ax=ax, label=scalar)
            colorbar_created = True
        ax.set_xlabel("Raio [m]")
        ax.set_ylabel("Profundidade local z [m]")
        ax.set_title(f"{result.case_name} · {scalar} · {vtu.stem}")
        return contour.collections

    suffix = _extension(output_format)
    safe_scalar = scalar.replace("_", "")
    return _save_animation(
        fig, update, len(frames), Path(out_dir) / f"{result.case_name}_anim_{safe_scalar}{suffix}",
        fps, output_format
    )


def animate_result(
    result: CaseResult,
    kind: str,
    out_dir: str | Path,
    fps: int = 4,
    output_format: str = "gif",
) -> list[Path]:
    kinds = ["closure", "ur", "damage", "temperature"] if kind == "all" else [kind]
    outputs: list[Path] = []
    for item in kinds:
        path: Path | None
        if item == "closure":
            path = animate_closure(result, out_dir, fps, output_format)
        elif item == "ur":
            path = animate_ur(result, out_dir, fps, output_format)
        elif item == "damage":
            path = animate_vtu_scalar(result, "damage_D", out_dir, fps, output_format)
        elif item == "temperature":
            path = animate_vtu_scalar(result, "temperature_K", out_dir, fps, output_format)
        else:
            raise ValueError(f"unknown animation kind: {item}")
        if path is not None:
            outputs.append(path)
    return outputs
