"""Comparison metrics for saltcreep result series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .io import CaseResult


def align_series(reference: pd.DataFrame,
                 other: pd.DataFrame,
                 time_col: str = "t_h",
                 value_col: str = "closure_pct") -> pd.DataFrame:
    ref_t = reference[time_col].to_numpy(dtype=float)
    ref_y = reference[value_col].to_numpy(dtype=float)
    other_t = other[time_col].to_numpy(dtype=float)
    other_y = other[value_col].to_numpy(dtype=float)
    interp = np.interp(ref_t, other_t, other_y)
    denom = np.maximum(np.abs(ref_y), 1.0e-30)
    return pd.DataFrame({
        time_col: ref_t,
        "reference": ref_y,
        "value": interp,
        "relative_error": np.abs(interp - ref_y) / denom,
    })


def comparison_table(results: list[CaseResult],
                     reference: CaseResult | None = None) -> pd.DataFrame:
    if reference is None and results:
        reference = results[0]

    ref_final = reference.final_closure if reference else None
    rows = []
    for result in results:
        final_closure = result.final_closure
        if ref_final is None or final_closure is None or abs(ref_final) < 1.0e-30:
            rel_err = None
        else:
            rel_err = abs(final_closure - ref_final) / abs(ref_final)
        rows.append({
            "case": result.case_name,
            "element": result.element_type,
            "n_dofs": result.n_dofs,
            "closure_final_pct": final_closure,
            "error_vs_ref": rel_err,
            "wall_time_s": result.metadata.get("wall_time_s"),
            "time_scheme": result.metadata.get("time_scheme"),
            "path": str(result.path),
        })
    return pd.DataFrame(rows)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in df.iterrows():
        values = ["" if pd.isna(row[col]) else str(row[col]) for col in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"
