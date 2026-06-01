"""Unit helpers for physical displacement plots."""

from __future__ import annotations


def auto_displacement_unit(u_max_m: float) -> tuple[float, str]:
    """Return scale factor and unit label for a displacement magnitude in meters."""
    magnitude = abs(float(u_max_m))
    if magnitude < 0.001:
        return 1.0e6, "μm"
    if magnitude < 0.01:
        return 1.0e3, "mm"
    if magnitude < 1.0:
        return 1.0e2, "cm"
    return 1.0, "m"
