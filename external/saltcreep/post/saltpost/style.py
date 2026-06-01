"""Shared plotting style for saltcreep post-processing."""

from __future__ import annotations

ELEMENT_COLORS = {
    "axisym_1d_L3": "#1f77b4",
    "axisym_2d_Q4": "#ff7f0e",
    "axisym_2d_T3": "#2ca02c",
    "axisym_2d_Q8": "#d62728",
    "axisym_2d_Q9": "#9467bd",
    "axisym_2d_AQ9": "#17becf",
    "axisym_2d_T6": "#8c564b",
}

ELEMENT_MARKERS = {
    "axisym_1d_L3": "o",
    "axisym_2d_Q4": "s",
    "axisym_2d_T3": "^",
    "axisym_2d_Q8": "D",
    "axisym_2d_Q9": "P",
    "axisym_2d_AQ9": "*",
    "axisym_2d_T6": "X",
}

DEFAULT_COLOR = "#4c4c4c"
CASE_COLORS = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]
CASE_MARKERS = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h"]
DEFAULT_MARKERS = CASE_MARKERS
FIGSIZE = (7.0, 4.5)
DPI = 300


def apply_style() -> None:
    import matplotlib as mpl

    mpl.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 9,
        "lines.linewidth": 1.5,
        "savefig.dpi": DPI,
        "figure.dpi": DPI,
    })


def color_for(element_type: str | None, index: int = 0) -> str:
    if element_type and element_type in ELEMENT_COLORS:
        return ELEMENT_COLORS[element_type]
    return CASE_COLORS[index % len(CASE_COLORS)]


def marker_for(element_type: str | None, index: int = 0) -> str:
    if element_type and element_type in ELEMENT_MARKERS:
        return ELEMENT_MARKERS[element_type]
    return DEFAULT_MARKERS[index % len(DEFAULT_MARKERS)]


def get_color(case_index: int, element_type: str | None,
              all_elements_same: bool) -> str:
    if all_elements_same:
        return CASE_COLORS[case_index % len(CASE_COLORS)]
    return ELEMENT_COLORS.get(
        element_type or "",
        CASE_COLORS[case_index % len(CASE_COLORS)],
    )


def get_marker(case_index: int, element_type: str | None,
               all_elements_same: bool) -> str:
    if all_elements_same:
        return CASE_MARKERS[case_index % len(CASE_MARKERS)]
    return ELEMENT_MARKERS.get(
        element_type or "",
        CASE_MARKERS[case_index % len(CASE_MARKERS)],
    )
