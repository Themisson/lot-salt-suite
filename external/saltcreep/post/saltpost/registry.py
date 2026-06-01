"""Discover and normalize saltcreep result folders."""

from __future__ import annotations

from pathlib import Path
import glob as globlib

from .io import CaseResult, load_result


def discover_results(pattern: str | None = None,
                     paths: list[str | Path] | None = None) -> list[CaseResult]:
    result_paths: list[Path] = []
    if paths:
        result_paths.extend(Path(p) for p in paths)
    if pattern:
        result_paths.extend(Path(p) for p in globlib.glob(pattern))

    unique: dict[Path, Path] = {}
    for path in result_paths:
        if path.is_dir():
            unique[path.resolve()] = path

    results = [
        load_result(path)
        for _, path in sorted(unique.items(), key=lambda item: str(item[0]))
    ]
    return [r for r in results if r.closure is not None or r.displacements is not None]


def label_for(result: CaseResult, group_by: str | None = None) -> str:
    element = result.element_type
    dofs = result.n_dofs
    if group_by == "element":
        suffix = f"{element} ({dofs} GDL)" if dofs is not None else element
        return f"{result.case_name} - {suffix}"
    if group_by == "n_dofs":
        suffix = f"{dofs} GDL - {element}" if dofs is not None else element
        return f"{result.case_name} - {suffix}"
    return f"{result.case_name} - {element}" if element != "unknown" else result.case_name
