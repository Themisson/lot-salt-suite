"""Lithology layer utilities for plotting."""

from __future__ import annotations

from dataclasses import dataclass

from .io import CaseResult


@dataclass(frozen=True)
class PlotLayer:
    z_top_m: float
    z_bottom_m: float
    material: str
    label: str

    def absolute_top(self, result: CaseResult) -> float:
        return result.depth_origin_m + self.z_top_m

    def absolute_bottom(self, result: CaseResult) -> float:
        return result.depth_origin_m + self.z_bottom_m


LITHOLOGY_COLORS = {
    "halita": "#5da5da",
    "carnalita": "#f28e2b",
    "taquidrita": "#e15759",
    "anhidrita": "#bab0ac",
}


def normalized_layers(result: CaseResult) -> list[PlotLayer]:
    layers: list[PlotLayer] = []
    for raw in result.lithology_layers:
        material = str(raw.get("material") or result.lithology_primary or "litologia")
        label = str(raw.get("label") or material)
        layers.append(PlotLayer(
            z_top_m=float(raw.get("z_top_m", 0.0)),
            z_bottom_m=float(raw.get("z_bottom_m", 0.0)),
            material=material,
            label=label,
        ))
    return [layer for layer in layers if layer.z_bottom_m > layer.z_top_m]


def color_for_lithology(material: str, index: int = 0) -> str:
    key = material.strip().lower()
    if key in LITHOLOGY_COLORS:
        return LITHOLOGY_COLORS[key]
    fallback = ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"]
    return fallback[index % len(fallback)]
