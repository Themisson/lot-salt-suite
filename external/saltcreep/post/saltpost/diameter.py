"""Wellbore diameter helpers for SaltCreep wall profiles."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .io import CaseResult

M_TO_IN = 39.37007874015748


def wall_radius_m(result: CaseResult) -> float:
    radius = result.well_radius_m
    if radius is None:
        raise ValueError(f"{result.case_name}: cannot infer well radius")
    return float(radius)


def enrich_wall_profile(result: CaseResult) -> pd.DataFrame:
    """Return wall_profile with depth and diameter columns.

    New solver outputs already contain these columns. This function also supports
    older result folders by deriving the missing quantities from metadata and
    ``u_r_m``.
    """
    if result.wall_profile is None or result.wall_profile.empty:
        raise ValueError(f"{result.case_name}: wall_profile.csv is missing")
    df = result.wall_profile.copy()
    radius = wall_radius_m(result)
    if "depth_m" not in df.columns:
        df["depth_m"] = result.depth_origin_m + df["z_m"].astype(float)
    if "diameter_m" not in df.columns:
        df["diameter_m"] = 2.0 * (radius + df["u_r_m"].astype(float))
    if "diameter_in" not in df.columns:
        df["diameter_in"] = df["diameter_m"] * M_TO_IN
    if "original_diameter_in" not in df.columns:
        df["original_diameter_in"] = 2.0 * radius * M_TO_IN
    return df


def nearest_time(df: pd.DataFrame, target_h: float | None) -> float:
    times = sorted(float(t) for t in df["t_h"].dropna().unique())
    if not times:
        raise ValueError("empty time series")
    if target_h is None:
        return times[-1]
    return min(times, key=lambda t: abs(t - target_h))


def profile_at_time(result: CaseResult, target_h: float | None = None) -> pd.DataFrame:
    df = enrich_wall_profile(result)
    actual = nearest_time(df, target_h)
    return df[np.isclose(df["t_h"].astype(float), actual)].sort_values("depth_m")


def diameter_at_depth(result: CaseResult, depth_m: float | None = None) -> pd.DataFrame:
    """Interpolate wall diameter at an absolute depth for every output time."""
    df = enrich_wall_profile(result)
    if depth_m is None:
        depth_m = float(df["depth_m"].min())

    rows: list[dict] = []
    for t_h, frame in df.groupby("t_h", sort=True):
        ordered = frame.sort_values("depth_m")
        depths = ordered["depth_m"].to_numpy(dtype=float)
        diameters = ordered["diameter_in"].to_numpy(dtype=float)
        if len(depths) == 1:
            diameter = float(diameters[0])
        else:
            clipped = float(np.clip(depth_m, depths.min(), depths.max()))
            diameter = float(np.interp(clipped, depths, diameters))
        rows.append({"t_h": float(t_h), "depth_m": float(depth_m), "diameter_in": diameter})
    return pd.DataFrame(rows)
