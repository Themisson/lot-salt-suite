"""Post-processing helpers for saltcreep results."""

from .io import CaseResult, load_result
from .registry import discover_results
from .compare import align_series, comparison_table
from .studies import discover_study_results
from .units import auto_displacement_unit
from .vtk import discover_vtu, has_pyvista, load_vtu

__all__ = [
    "CaseResult",
    "align_series",
    "auto_displacement_unit",
    "comparison_table",
    "discover_vtu",
    "discover_results",
    "discover_study_results",
    "has_pyvista",
    "load_result",
    "load_vtu",
]
