"""Export helpers for publication-style saltpost outputs."""

from __future__ import annotations

from pathlib import Path
import csv
import re
import shutil

import pandas as pd


def slugify(value: str | None, default: str = "comparison") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value or "").strip("_").lower()
    return text or default


def context_suffix(study: str | None = None, vary: str | None = None) -> str:
    base = slugify(study, "comparison")
    if vary:
        return f"{base}_by_{slugify(vary)}"
    return base


def write_table_formats(
    table: pd.DataFrame,
    out_dir: Path,
    stem: str,
    output_format: str = "default",
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / f"{stem}.csv", index=False)
    markdown = _dataframe_to_markdown(table)
    (out_dir / f"{stem}.md").write_text(markdown, encoding="utf-8")
    if output_format == "paper":
        (out_dir / f"{stem}.tex").write_text(
            _dataframe_to_latex(table),
            encoding="utf-8",
        )


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in df.iterrows():
        values = ["" if pd.isna(row[col]) else str(row[col]) for col in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _latex_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _dataframe_to_latex(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    spec = "l" * max(len(cols), 1)
    lines = [
        rf"\begin{{tabular}}{{{spec}}}",
        r"\hline",
        " & ".join(_latex_escape(c) for c in cols) + r" \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(" & ".join(_latex_escape(row[col]) for col in df.columns) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", ""])
    return "\n".join(lines)


def export_paper_bundle(
    out_dir: Path,
    study: str | None = None,
    vary: str | None = None,
) -> Path:
    """Copy figures/tables to a deterministic paper/ folder."""
    out_dir = Path(out_dir)
    paper_dir = out_dir / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    suffix = context_suffix(study, vary)

    manifest_rows: list[dict[str, str]] = []
    stems = sorted({p.stem for p in out_dir.glob("*.png")} | {p.stem for p in out_dir.glob("*.pdf")})
    for index, stem in enumerate(stems, start=1):
        paper_stem = f"fig_{index:02d}_{slugify(stem)}_{suffix}"
        for ext in (".png", ".pdf"):
            src = out_dir / f"{stem}{ext}"
            if not src.exists():
                continue
            dst = paper_dir / f"{paper_stem}{ext}"
            shutil.copy2(src, dst)
            manifest_rows.append({
                "type": "figure",
                "source": str(src),
                "paper_file": str(dst),
            })

    for table_name in ("comparison_table", "summary"):
        table_path = out_dir / f"{table_name}.csv"
        if not table_path.exists():
            continue
        table = pd.read_csv(table_path)
        stem = f"tab_{slugify(table_name)}_{suffix}"
        write_table_formats(table, paper_dir, stem, output_format="paper")
        for ext in ("csv", "md", "tex"):
            manifest_rows.append({
                "type": "table",
                "source": str(table_path),
                "paper_file": str(paper_dir / f"{stem}.{ext}"),
            })

    manifest_path = paper_dir / "paper_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["type", "source", "paper_file"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    return paper_dir
