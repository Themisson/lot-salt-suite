"""Static HTML dashboard generation for saltpost outputs."""

from __future__ import annotations

from pathlib import Path
import html
import os
import shutil

import pandas as pd

from .io import CaseResult
from .studies import variant_key


def _rel(path: Path, base: Path) -> str:
    return Path(os.path.relpath(path, base)).as_posix()


def _copy_assets(source_dir: Path, report_dir: Path) -> list[Path]:
    assets = report_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for pattern in ("*.png", "*.gif"):
        for src in sorted(source_dir.glob(pattern)):
            dst = assets / src.name
            shutil.copy2(src, dst)
            copied.append(dst)
    return copied


def _file_link(path: Path, report_dir: Path, label: str) -> str:
    if not path.exists():
        return ""
    href = html.escape(_rel(path.resolve(), report_dir.resolve()))
    return f'<a href="{href}">{html.escape(label)}</a>'


def _result_links(result: CaseResult, report_dir: Path) -> str:
    links: list[str] = []
    for filename in ("metadata.json", "closure.csv", "displacements.csv",
                     "displacements_profile.csv", "wall_profile.csv",
                     "damage_wall.csv", "damage_events.csv"):
        link = _file_link(result.path / filename, report_dir, filename)
        if link:
            links.append(link)
    for pvd in sorted(result.path.glob("*.pvd")):
        links.append(_file_link(pvd, report_dir, pvd.name))
    vtus = sorted(result.path.glob("*.vtu"))
    if vtus:
        links.append(_file_link(vtus[0], report_dir, f"{vtus[0].name} (+{len(vtus)-1})"))
    return " · ".join(links)


def _metadata_table(results: list[CaseResult], vary: str | None = None) -> str:
    rows = []
    for result in results:
        variant = variant_key(result, vary) if vary else result.element_type
        rows.append({
            "case": result.case_name,
            "variant": variant,
            "element": result.element_type,
            "n_dofs": result.n_dofs,
            "closure_final_pct": result.final_closure,
            "time_scheme": result.metadata.get("time_scheme"),
            "wall_time_s": result.metadata.get("wall_time_s"),
            "omp_threads": result.metadata.get("omp_threads"),
        })
    df = pd.DataFrame(rows)
    return df.to_html(index=False, classes="data", border=0, escape=True)


def generate_dashboard(
    results: list[CaseResult],
    plot_dir: str | Path,
    report_dir: str | Path = "results/report",
    study: str | None = None,
    vary: str | None = None,
) -> Path:
    """Generate a self-contained static dashboard around existing plot files."""
    plot_dir = Path(plot_dir)
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    copied_assets = _copy_assets(plot_dir, report_dir)

    title = "SaltCreep Dashboard"
    subtitle = "Comparação de resultados"
    if study:
        subtitle = f"Estudo {study}"
        if vary:
            subtitle += f" · variação: {vary}"

    figures_html = "\n".join(
        f'<figure><img src="{html.escape(_rel(asset, report_dir))}" alt="{html.escape(asset.stem)}">'
        f"<figcaption>{html.escape(asset.stem.replace('_', ' '))}</figcaption></figure>"
        for asset in copied_assets
    )
    if not figures_html:
        figures_html = "<p>Nenhuma figura encontrada no diretório de saída.</p>"

    case_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(result.case_name)}</td>"
        f"<td>{html.escape(result.element_type)}</td>"
        f"<td>{'' if result.n_dofs is None else result.n_dofs}</td>"
        f"<td>{'' if result.final_closure is None else f'{result.final_closure:.6g}'}</td>"
        f"<td>{_result_links(result, report_dir)}</td>"
        "</tr>"
        for result in results
    )

    comparison_links = []
    for filename in ("comparison_table.csv", "comparison_table.md", "comparison_table.tex"):
        link = _file_link(plot_dir / filename, report_dir, filename)
        if link:
            comparison_links.append(link)

    html_text = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ --ink:#1f2933; --muted:#5b6673; --rule:#d8dee7; --accent:#1f77b4; --bg:#f7f8fb; }}
    body {{ margin:0; font-family: Georgia, 'Times New Roman', serif; color:var(--ink); background:var(--bg); }}
    header {{ padding:32px 42px 18px; background:#fff; border-bottom:1px solid var(--rule); }}
    main {{ padding:26px 42px 46px; max-width:1180px; margin:0 auto; }}
    h1 {{ margin:0 0 6px; font-size:30px; }}
    h2 {{ margin-top:30px; border-bottom:1px solid var(--rule); padding-bottom:8px; }}
    .muted {{ color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:18px; }}
    .card, figure {{ background:#fff; border:1px solid var(--rule); border-radius:8px; padding:16px; }}
    figure {{ margin:0; }}
    img {{ width:100%; height:auto; display:block; }}
    figcaption {{ margin-top:9px; color:var(--muted); font-size:13px; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; }}
    th, td {{ padding:9px 10px; border-bottom:1px solid var(--rule); text-align:left; vertical-align:top; }}
    th {{ color:#111827; background:#eef2f7; }}
    a {{ color:var(--accent); text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    .links {{ background:#fff; border:1px solid var(--rule); border-radius:8px; padding:16px; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <p class="muted">{html.escape(subtitle)} · {len(results)} caso(s)</p>
  </header>
  <main>
    <section>
      <h2>Figuras</h2>
      <div class="grid">{figures_html}</div>
    </section>
    <section>
      <h2>Resumo de metadados</h2>
      {_metadata_table(results, vary)}
    </section>
    <section>
      <h2>Arquivos por caso</h2>
      <table>
        <tr><th>Caso</th><th>Elemento</th><th>GDLs</th><th>Closure final [%]</th><th>Arquivos</th></tr>
        {case_rows}
      </table>
    </section>
    <section>
      <h2>Tabelas comparativas</h2>
      <div class="links">{' · '.join(comparison_links) if comparison_links else 'Nenhuma tabela encontrada.'}</div>
    </section>
  </main>
</body>
</html>
"""
    out = report_dir / "index.html"
    out.write_text(html_text, encoding="utf-8")
    return out

