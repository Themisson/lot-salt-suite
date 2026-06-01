#!/usr/bin/env python3
"""
generate_docs_index.py — Gera docs/index.html a partir dos arquivos docs/*.md

Uso:
    python tools/generate_docs_index.py
    python tools/generate_docs_index.py --dry-run   # apenas imprime, não salva

O script:
1. Lê tools/docs_status.yaml para status de cada seção
2. Converte docs/*.md para HTML usando python-markdown
3. Injeta nas seções do template HTML
4. Atualiza painel de status, sumário e métricas do projeto
5. Salva docs/index.html
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Instale pyyaml: pip install pyyaml")
    sys.exit(1)

try:
    import markdown
except ImportError:
    print("Instale markdown: pip install markdown")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
STATUS_FILE = ROOT / "tools" / "docs_status.yaml"
OUTPUT = DOCS_DIR / "index.html"

# Mapeamento: seção do index.html → arquivo docs/*.md
SECTION_MAP = {
    "overview":        "00_project_overview.md",
    "inventory":       "01_repository_inventory.md",
    "lot":             "02_lot_formulation.md",
    "apb":             "03_apb_formulation.md",
    "salt":            "04_salt_creep_models.md",
    "input":           "05_input_output_formats.md",
    "validation_plan": "06_validation_plan.md",
    "architecture":    "07_target_architecture.md",
    "issues":          "08_known_issues.md",
    "migration":       "09_migration_plan.md",
    "postprocess":     "10_postprocessing_plan.md",
    "cli":             "11_cli_usage.md",
    "results":         "12_validation_results.md",
    "coupling":        "13_coupling_lot_apb_salt.md",
    "devguide":        "14_developer_workflow.md",
    "changelog":       "15_changelog.md",
    "saltcreep_governance": "16_saltcreep_governance.md",
    "lot_pkn_roadmap": "17_lot_pkn_roadmap.md",
    "lot_legacy_inventory": "audits/lot_legacy_inventory.md",
    "pkn_legacy_path": "audits/pkn_legacy_path.md",
    "non_pkn_models_status": "audits/non_pkn_models_status.md",
}

STATUS_LABELS = {
    "not_started":   ("Não iniciado", "#6b7280"),
    "planned":       ("Planejado",    "#3b82f6"),
    "in_progress":   ("Em andamento", "#f59e0b"),
    "implemented":   ("Implementado", "#8b5cf6"),
    "validated":     ("Validado",     "#10b981"),
    "risk":          ("Risco",        "#ef4444"),
    "completed":     ("Concluído",    "#10b981"),
}

STATUS_CLASSES = {
    "not_started":   "pill-muted",
    "planned":       "pill-info",
    "in_progress":   "pill-warn",
    "implemented":   "pill-impl",
    "validated":     "pill-ok",
    "risk":          "pill-bad",
    "completed":     "pill-ok",
}


def load_status() -> dict:
    if not STATUS_FILE.exists():
        print(f"AVISO: {STATUS_FILE} não encontrado. Usando status padrão.")
        return {}
    with STATUS_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def md_to_html(md_file: Path) -> str:
    if not md_file.exists():
        return f"<p><em>Arquivo não encontrado: {md_file.name}</em></p>"
    text = md_file.read_text(encoding="utf-8")
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "attr_list"],
    )


def status_badge(status: str) -> str:
    label, _ = STATUS_LABELS.get(status, ("Desconhecido", "#9ca3af"))
    css_class = STATUS_CLASSES.get(status, "pill-muted")
    return f'<span class="pill {css_class}">{label}</span>'


def section_title(md_name: str) -> str:
    md_file = DOCS_DIR / md_name
    if md_file.exists():
        for line in md_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return md_name.replace(".md", "").replace("_", " ").replace("/", " / ").title()


def build_toc(status: dict) -> str:
    docs_status = status.get("docs", {})
    items = []
    for sec_id, md_name in SECTION_MAP.items():
        title = section_title(md_name)
        sec_status = docs_status.get(sec_id, "not_started")
        css_class = STATUS_CLASSES.get(sec_status, "pill-muted")
        items.append(
            f'<a href="#{sec_id}"><span>{title}</span>'
            f'<span class="toc-dot {css_class}"></span></a>'
        )
    return "\n".join(items)


def build_sections(status: dict) -> str:
    docs_status = status.get("docs", {})
    parts = []
    for sec_id, md_name in SECTION_MAP.items():
        sec_status = docs_status.get(sec_id, "not_started")
        html_content = md_to_html(DOCS_DIR / md_name)
        badge = status_badge(sec_status)
        title = section_title(md_name)
        parts.append(
            f'<section id="{sec_id}" class="doc-section">\n'
            f'<div class="section-header">'
            f'<span class="section-kicker">Documento</span>'
            f'{badge}'
            f'</div>\n'
            f'<div class="section-source">{title}</div>\n'
            f'{html_content}\n'
            f'</section>\n'
        )
    return "\n".join(parts)


def build_hero_stats(status: dict) -> str:
    phases = status.get("phases", {})
    test_counts = status.get("test_counts", {})
    validation = status.get("validation", {})

    completed_phases = sum(1 for v in phases.values() if v in ("completed", "in_progress"))
    total_phases = len(phases)
    cpp_tests = test_counts.get("cpp_tests", 0)
    py_tests = test_counts.get("python_tests", 0)
    v_done = sum(1 for v in validation.values() if v not in ("not_started",))

    return f"""
    <div class="status-grid">
      <article class="status-card">
        <h3>Fases</h3>
        <span class="pill pill-ok">{completed_phases}/{total_phases}</span>
        <p>Fases concluídas ou em andamento no plano técnico do projeto.</p>
      </article>
      <article class="status-card">
        <h3>Testes C++</h3>
        <span class="pill pill-info">{cpp_tests}</span>
        <p>Testes Catch2 registrados como verdes na última execução documentada.</p>
      </article>
      <article class="status-card">
        <h3>Testes Python</h3>
        <span class="pill pill-muted">{py_tests}</span>
        <p>Testes pytest registrados no pacote de pós-processamento.</p>
      </article>
      <article class="status-card">
        <h3>Validações</h3>
        <span class="pill pill-warn">{v_done}/10</span>
        <p>Status da suíte V0-V9; validação numérica só conta quando registrada.</p>
      </article>
    </div>
    """


def generate_html(status: dict, dry_run: bool = False) -> str:
    today = date.today().isoformat()
    last_updated = status.get("last_updated", today)
    version = status.get("project_version", "0.1.0")

    toc = build_toc(status)
    sections = build_sections(status)
    hero = build_hero_stats(status)

    # Aviso se nenhuma validação numérica foi executada
    validation = status.get("validation", {})
    any_validated = any(v == "validated" for v in validation.values())
    warning_html = ""
    if not any_validated:
        warning_html = """
    <div class="notice notice-warn">
      <strong>Aviso:</strong> nenhuma validação numérica de regressão contra legado
      foi marcada como validada. Testes sintéticos e validações de contrato aparecem
      em <a href="#results">Resultados de Validação</a>.
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>lot-salt-suite — Documentação Técnica</title>
<style>
  :root {{
    --dark:#172033;
    --accent:#0f766e;
    --accent2:#14b8a6;
    --bg:#f4f6f8;
    --paper:#ffffff;
    --text:#1f2937;
    --muted:#6b7280;
    --line:#e5e7eb;
    --soft:#f9fafb;
    --code:#111827;
    --ok:#15803d;
    --warn:#a16207;
    --bad:#b91c1c;
    --info:#1d4ed8;
    --impl:#6d28d9;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.58;
  }}
  header {{
    background: linear-gradient(135deg, var(--dark), var(--accent));
    color: white;
    padding: 42px 56px;
  }}
  header h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
  header p {{ margin: 6px 0; color: #eef2f7; max-width: 980px; }}
  header .small {{ color: #d1d5db; }}
  main {{
    max-width: 1280px;
    margin: 0 auto;
    background: var(--paper);
    padding: 34px 52px 64px;
  }}
  .toc {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: rgba(255,255,255,.96);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px 16px;
    margin: -10px 0 26px;
    box-shadow: 0 8px 20px rgba(15,23,42,.08);
    backdrop-filter: blur(8px);
  }}
  .toc strong {{ display: block; margin-bottom: 8px; }}
  .toc a {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin: 4px 8px 4px 0;
    padding: 5px 9px;
    border-radius: 6px;
    background: #f3f4f6;
    color: #1f2937;
    text-decoration: none;
    font-size: 13px;
  }}
  .toc a:hover {{ background: #ccfbf1; color: #134e4a; }}
  .toc-dot {{ width: 8px; height: 8px; border-radius: 999px; display: inline-block; }}
  .hero {{ margin: 4px 0 28px; }}
  .hero h2 {{
    margin: 0 0 8px;
    padding: 0;
    border: 0;
    color: var(--dark);
    font-size: 28px;
  }}
  .hero p {{ color: var(--muted); max-width: 880px; }}
  .status-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 14px;
    margin: 18px 0;
  }}
  .status-card {{
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px 16px;
    background: #ffffff;
  }}
  .status-card h3 {{ margin: 0 0 8px; color: #1f2937; font-size: 16px; }}
  .status-card p {{ color: var(--muted); font-size: 13px; margin: 10px 0 0; }}
  .pill {{
    display: inline-block;
    border-radius: 999px;
    padding: 3px 9px;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: .02em;
  }}
  .pill-ok {{ background: #dcfce7; color: #166534; }}
  .pill-warn {{ background: #fef3c7; color: #92400e; }}
  .pill-bad {{ background: #fee2e2; color: #991b1b; }}
  .pill-info {{ background: #dbeafe; color: #1e40af; }}
  .pill-impl {{ background: #ede9fe; color: #5b21b6; }}
  .pill-muted {{ background: #f3f4f6; color: #4b5563; }}
  .notice {{
    border-left: 5px solid var(--info);
    background: #eff6ff;
    padding: 16px 20px;
    margin: 18px 0;
  }}
  .notice-warn {{ border-left-color: #f59e0b; background: #fffbeb; }}
  .doc-section {{
    border-top: 1px solid var(--line);
    padding: 26px 0 18px;
    margin: 0 0 12px;
  }}
  .section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
  }}
  .section-kicker {{
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
  }}
  .section-source {{ color: var(--muted); font-size: 13px; margin-bottom: 12px; }}
  h1, h2, h3, h4 {{ color: #1f2937; letter-spacing: 0; }}
  h1 {{ font-size: 28px; margin: 18px 0 10px; }}
  h2 {{
    margin-top: 42px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent2);
    font-size: 22px;
  }}
  h3 {{ margin-top: 28px; color: #0f766e; }}
  h4 {{ margin-top: 20px; }}
  p {{ line-height: 1.7; margin: 0.55rem 0; }}
  a {{ color: #0f766e; }}
  table {{ border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 14px; }}
  th {{
    background: #f3f4f6;
    text-align: left;
    text-transform: uppercase;
    font-size: 12px;
    letter-spacing: .06em;
  }}
  td, th {{ border: 1px solid var(--line); padding: 9px 11px; vertical-align: top; }}
  tr:hover td {{ background: #f9fafb; }}
  code {{
    font-family: Consolas, 'Courier New', monospace;
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 3px;
    color: #0f766e;
    font-size: .9em;
  }}
  pre {{
    background: var(--code);
    color: #e5e7eb;
    padding: 16px;
    border-radius: 8px;
    overflow: auto;
    white-space: pre-wrap;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 13px;
  }}
  pre code {{ color: inherit; background: none; padding: 0; }}
  ul, ol {{ padding-left: 1.5rem; }}
  li {{ margin: 4px 0; line-height: 1.6; }}
  blockquote {{
    background: #f9fafb;
    border-left: 5px solid #6b7280;
    padding: 14px 18px;
    margin: 16px 0;
    color: #374151;
  }}
  footer {{ color: var(--muted); font-size: 13px; text-align: center; margin-top: 32px; padding: 16px; }}
  @media (max-width: 760px) {{
    header {{ padding: 30px 22px; }}
    header h1 {{ font-size: 27px; }}
    main {{ padding: 22px 18px 42px; }}
    .toc {{ position: static; }}
    .toc a {{ display: flex; }}
    table {{ display: block; overflow-x: auto; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Manual Técnico — lot-salt-suite</h1>
  <p>Documentação navegável do simulador integrado de Leak-Off Test, APB e fluência de sal para poços em formações salinas.</p>
  <p class="small">Versão {version} · Atualizado em {last_updated} · Gerado em {today}</p>
</header>
<main>
  <nav class="toc">
    <strong>Navegação rápida</strong>
    {toc}
  </nav>
  <div class="hero">
    <h2>lot-salt-suite</h2>
    <p>Painel consolidado de estado do projeto, formulações, contratos de entrada, validação, arquitetura e riscos conhecidos.</p>
    {hero}
  </div>
  {warning_html}
  {sections}
  <footer>lot-salt-suite v{version} · Gerado em {today} por generate_docs_index.py</footer>
</main>
</body>
</html>"""

    if not dry_run:
        OUTPUT.write_text(html, encoding="utf-8")
        print(f"docs/index.html gerado: {OUTPUT}")
    else:
        print("Dry-run: HTML gerado (não salvo).")

    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera docs/index.html")
    parser.add_argument("--dry-run", action="store_true", help="Imprimir sem salvar")
    args = parser.parse_args()

    status = load_status()
    generate_html(status, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
