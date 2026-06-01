"""VTK/VTU helpers for saltcreep visual outputs."""

from __future__ import annotations

from pathlib import Path
import importlib.util


def has_pyvista() -> bool:
    return importlib.util.find_spec("pyvista") is not None


def load_vtu(path: str | Path):
    """Load a VTU file with PyVista.

    PyVista is intentionally optional so CSV-only post-processing stays light.
    """
    if not has_pyvista():
        raise RuntimeError(
            "PyVista is not installed. Install pyvista to load VTU files."
        )
    import pyvista as pv  # type: ignore

    return pv.read(Path(path))


def discover_vtu(result_dir: str | Path) -> list[Path]:
    return sorted(Path(result_dir).glob("*.vtu"))
