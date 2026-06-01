"""3D axisymmetric wellbore visualization from SaltCreep wall profiles."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .diameter import profile_at_time
from .io import load_result


def _selected_wall_frame(result_dir: str | Path, time_h: float | None):
    result = load_result(result_dir)
    frame = profile_at_time(result, time_h)
    radius = result.well_radius_m
    if radius is None:
        raise ValueError(f"{result.case_name}: cannot infer well radius")
    return result, frame, float(radius)


def _surface(radius: np.ndarray, z_display: np.ndarray, angle_deg: float, n_theta: int):
    theta = np.linspace(0.0, np.radians(angle_deg), n_theta)
    theta_grid, radius_grid = np.meshgrid(theta, radius)
    _, z_grid = np.meshgrid(theta, z_display)
    x = radius_grid * np.cos(theta_grid)
    y = radius_grid * np.sin(theta_grid)
    return x, y, z_grid, theta


def _add_cut_faces(ax, radius: np.ndarray, z_display: np.ndarray,
                   theta: np.ndarray, color: str) -> None:
    if len(radius) < 2:
        return
    for t_val in [theta[0], theta[-1]]:
        x_cut = radius * np.cos(t_val)
        y_cut = radius * np.sin(t_val)
        verts = [list(zip(x_cut, y_cut, z_display))]
        face = Poly3DCollection(verts, color=color, alpha=0.35,
                                edgecolor="#334155", linewidth=0.6)
        ax.add_collection3d(face)


def _set_axes_equal(ax) -> None:
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()
    ranges = [
        abs(x_limits[1] - x_limits[0]),
        abs(y_limits[1] - y_limits[0]),
        abs(z_limits[1] - z_limits[0]),
    ]
    middles = [np.mean(x_limits), np.mean(y_limits), np.mean(z_limits)]
    radius = 0.5 * max(ranges + [1.0e-9])
    ax.set_xlim3d([middles[0] - radius, middles[0] + radius])
    ax.set_ylim3d([middles[1] - radius, middles[1] + radius])
    ax.set_zlim3d([middles[2] - radius, middles[2] + radius])


def make_axisym_3d(
    result_dir: str | Path,
    save: str | Path | None = None,
    time_h: float | None = None,
    angle_deg: float = 270.0,
    displacement_scale: float | None = None,
) -> Path:
    """Generate a 3D sector view of original and deformed wellbore wall."""
    result, frame, radius = _selected_wall_frame(result_dir, time_h)
    out = Path(save) if save else Path(result_dir) / f"{result.case_name}_axisym_3d.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    ordered = frame.sort_values("depth_m")
    depth = ordered["depth_m"].to_numpy(dtype=float)
    if len(depth) == 1:
        depth = np.array([depth[0] - 0.5, depth[0] + 0.5], dtype=float)
        ur = np.repeat(float(ordered["u_r_m"].iloc[0]), 2)
    else:
        ur = ordered["u_r_m"].to_numpy(dtype=float)

    z_display = -depth
    max_u = float(np.nanmax(np.abs(ur))) if len(ur) else 0.0
    if displacement_scale is None:
        height = max(float(np.nanmax(depth) - np.nanmin(depth)), 1.0)
        if max_u > 1.0e-14:
            displacement_scale = min((0.08 * height) / max_u, (0.70 * radius) / max_u)
        else:
            displacement_scale = 1.0

    r0 = np.full_like(z_display, radius)
    rd = np.maximum(radius + displacement_scale * ur, 0.05 * radius)

    fig = plt.figure(figsize=(9.0, 7.2))
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    x0, y0, z0, theta = _surface(r0, z_display, angle_deg, 56)
    xd, yd, zd, _ = _surface(rd, z_display, angle_deg, 56)
    ax.plot_surface(x0, y0, z0, color="#d1d5db", edgecolor="#64748b",
                    linewidth=0.12, alpha=0.30)
    ax.plot_surface(xd, yd, zd, color="#60a5fa", edgecolor="#1e3a8a",
                    linewidth=0.18, alpha=0.68)
    _add_cut_faces(ax, rd, z_display, theta, "#60a5fa")
    ax.set_title(
        f"{result.case_name} - parede axissimetrica 3D - t = {float(ordered['t_h'].iloc[0]):.4g} h"
    )
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Cota Z = -profundidade [m]")
    ax.view_init(elev=24, azim=-45)
    _set_axes_equal(ax)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out
