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
4. Atualiza hero stats (fases, testes, módulos)
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
    label, color = STATUS_LABELS.get(status, ("Desconhecido", "#9ca3af"))
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:4px;font-size:0.75rem;font-weight:600;">{label}</span>'
    )


def build_sidebar(status: dict) -> str:
    docs_status = status.get("docs", {})
    items = []
    for sec_id, md_name in SECTION_MAP.items():
        title = md_name.replace(".md", "").replace("_", " ").title()
        sec_status = docs_status.get(sec_id, "not_started")
        _, color = STATUS_LABELS.get(sec_status, ("", "#6b7280"))
        items.append(
            f'<li><a href="#{sec_id}" style="color:{color}">{title}</a></li>'
        )
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def build_sections(status: dict) -> str:
    docs_status = status.get("docs", {})
    parts = []
    for sec_id, md_name in SECTION_MAP.items():
        sec_status = docs_status.get(sec_id, "not_started")
        html_content = md_to_html(DOCS_DIR / md_name)
        badge = status_badge(sec_status)
        parts.append(
            f'<section id="{sec_id}" class="doc-section">\n'
            f'<div class="section-header">{badge}</div>\n'
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
    <div class="hero-stats">
      <div class="stat"><span class="stat-num">{completed_phases}/{total_phases}</span><span class="stat-label">Fases ativas</span></div>
      <div class="stat"><span class="stat-num">{cpp_tests}</span><span class="stat-label">Testes C++</span></div>
      <div class="stat"><span class="stat-num">{py_tests}</span><span class="stat-label">Testes Python</span></div>
      <div class="stat"><span class="stat-num">{v_done}/10</span><span class="stat-label">Validações V0-V9</span></div>
    </div>
    """


def generate_html(status: dict, dry_run: bool = False) -> str:
    today = date.today().isoformat()
    last_updated = status.get("last_updated", today)
    version = status.get("project_version", "0.1.0")

    sidebar = build_sidebar(status)
    sections = build_sections(status)
    hero = build_hero_stats(status)

    # Aviso se nenhuma validação foi executada
    validation = status.get("validation", {})
    any_validated = any(v == "validated" for v in validation.values())
    warning_html = ""
    if not any_validated:
        warning_html = """
    <div style="background:#fef3c7;border:1px solid #f59e0b;padding:12px 16px;margin:16px 0;border-radius:6px;">
      <strong>Aviso:</strong> Nenhuma validação foi executada ainda no código novo.
      Os resultados em <a href="#results">Resultados de Validação</a> refletem planos,
      não execuções reais.
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>lot-salt-suite — Documentação Técnica</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; display: flex; min-height: 100vh; }}
  #sidebar {{ width: 260px; min-width: 260px; background: #1e293b; padding: 24px 16px; overflow-y: auto; position: sticky; top: 0; height: 100vh; }}
  #sidebar h1 {{ font-size: 1rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px; }}
  #sidebar .version {{ font-size: 0.7rem; color: #64748b; margin-bottom: 20px; }}
  #sidebar ul {{ list-style: none; }}
  #sidebar li {{ margin: 4px 0; }}
  #sidebar a {{ text-decoration: none; font-size: 0.85rem; padding: 4px 8px; display: block; border-radius: 4px; transition: background 0.15s; }}
  #sidebar a:hover {{ background: #334155; }}
  #main {{ flex: 1; padding: 32px 40px; overflow-y: auto; max-width: 900px; }}
  .hero {{ background: linear-gradient(135deg, #1e3a5f, #0f172a); padding: 32px; border-radius: 12px; margin-bottom: 32px; }}
  .hero h2 {{ font-size: 1.8rem; color: #38bdf8; margin-bottom: 8px; }}
  .hero p {{ color: #94a3b8; margin-bottom: 16px; }}
  .hero-stats {{ display: flex; gap: 24px; flex-wrap: wrap; }}
  .stat {{ text-align: center; }}
  .stat-num {{ display: block; font-size: 1.6rem; font-weight: 700; color: #38bdf8; }}
  .stat-label {{ font-size: 0.75rem; color: #64748b; }}
  .doc-section {{ background: #1e293b; border-radius: 8px; padding: 24px; margin-bottom: 24px; }}
  .section-header {{ margin-bottom: 12px; }}
  h1, h2, h3, h4 {{ color: #f1f5f9; margin: 1rem 0 0.5rem; }}
  h1 {{ font-size: 1.5rem; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
  h2 {{ font-size: 1.2rem; color: #38bdf8; }}
  p {{ line-height: 1.7; color: #cbd5e1; margin: 0.5rem 0; }}
  a {{ color: #38bdf8; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.85rem; }}
  th {{ background: #334155; padding: 8px 12px; text-align: left; color: #94a3b8; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #1e293b; }}
  tr:hover td {{ background: #334155; }}
  code {{ background: #0f172a; padding: 2px 6px; border-radius: 3px; font-family: 'Consolas', monospace; font-size: 0.85em; color: #7dd3fc; }}
  pre {{ background: #0f172a; padding: 16px; border-radius: 6px; overflow-x: auto; margin: 1rem 0; }}
  pre code {{ padding: 0; background: none; }}
  ul, ol {{ padding-left: 1.5rem; color: #cbd5e1; }}
  li {{ margin: 4px 0; line-height: 1.6; }}
  blockquote {{ border-left: 3px solid #38bdf8; padding: 8px 16px; background: #0f172a; margin: 1rem 0; color: #94a3b8; }}
  footer {{ color: #475569; font-size: 0.75rem; text-align: center; margin-top: 32px; padding: 16px; }}
</style>
</head>
<body>
<nav id="sidebar">
  <h1>lot-salt-suite</h1>
  <div class="version">v{version} · {last_updated}</div>
  {sidebar}
</nav>
<main id="main">
  {warning_html}
  <div class="hero">
    <h2>lot-salt-suite</h2>
    <p>Simulador integrado de LOT, APB e fluência de sal para poços em formações salinas.</p>
    {hero}
  </div>
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
