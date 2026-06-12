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
    "future_features": "16_future_features.md",
    "devguide":        "14_developer_workflow.md",
    "changelog":       "15_changelog.md",
    "saltcreep_governance": "16_saltcreep_governance.md",
    "lot_pkn_roadmap": "17_lot_pkn_roadmap.md",
    "saltcreep_eigen_migration_plan": "20_saltcreep_eigen_migration_plan.md",
    "saltcreep_eigen_compatibility_audit": "audits/saltcreep_eigen_compatibility_audit.md",
    "lot_legacy_inventory": "audits/lot_legacy_inventory.md",
    "pkn_legacy_path": "audits/pkn_legacy_path.md",
    "non_pkn_models_status": "audits/non_pkn_models_status.md",
    "r09_pkn_conversion_experiment": "audits/R09_pkn_conversion_experiment.md",
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

NAV_GROUPS = [
    (
        "Base do projeto",
        [
            "overview",
            "inventory",
            "architecture",
            "devguide",
            "changelog",
        ],
    ),
    (
        "Formulações",
        [
            "lot",
            "apb",
            "salt",
            "coupling",
            "future_features",
            "issues",
        ],
    ),
    (
        "Entrada, CLI e validação",
        [
            "input",
            "cli",
            "validation_plan",
            "results",
            "migration",
            "postprocess",
        ],
    ),
    (
        "LOT/PKN e auditorias",
        [
            "saltcreep_governance",
            "lot_pkn_roadmap",
            "saltcreep_eigen_migration_plan",
            "saltcreep_eigen_compatibility_audit",
            "lot_legacy_inventory",
            "pkn_legacy_path",
            "non_pkn_models_status",
            "r09_pkn_conversion_experiment",
        ],
    ),
]


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


def strip_first_h1(html_content: str) -> str:
    return re.sub(r"\s*<h1(?:\s+id=\"[^\"]+\")?>.*?</h1>\s*", "", html_content, count=1, flags=re.S)


def build_sidebar(status: dict) -> str:
    docs_status = status.get("docs", {})
    groups = []
    rendered = set()

    for label, sec_ids in NAV_GROUPS:
        links = []
        for sec_id in sec_ids:
            if sec_id not in SECTION_MAP:
                continue
            rendered.add(sec_id)
            title = section_title(SECTION_MAP[sec_id])
            sec_status = docs_status.get(sec_id, "not_started")
            css_class = STATUS_CLASSES.get(sec_status, "pill-muted")
            links.append(
                f'<a href="#{sec_id}" data-title="{title.lower()}">'
                f'<span>{title}</span><span class="nav-dot {css_class}"></span></a>'
            )
        if links:
            groups.append(
                '<div class="nav-group">\n'
                f'  <div class="label">{label}</div>\n'
                f'  {"".join(links)}\n'
                '</div>'
            )

    remaining = [sec_id for sec_id in SECTION_MAP if sec_id not in rendered]
    if remaining:
        links = []
        for sec_id in remaining:
            title = section_title(SECTION_MAP[sec_id])
            sec_status = docs_status.get(sec_id, "not_started")
            css_class = STATUS_CLASSES.get(sec_status, "pill-muted")
            links.append(
                f'<a href="#{sec_id}" data-title="{title.lower()}">'
                f'<span>{title}</span><span class="nav-dot {css_class}"></span></a>'
            )
        groups.append(
            '<div class="nav-group">\n'
            '  <div class="label">Outros documentos</div>\n'
            f'  {"".join(links)}\n'
            '</div>'
        )

    return "\n".join(groups)


def build_sections(status: dict) -> str:
    docs_status = status.get("docs", {})
    parts = []
    for sec_id, md_name in SECTION_MAP.items():
        sec_status = docs_status.get(sec_id, "not_started")
        html_content = strip_first_h1(md_to_html(DOCS_DIR / md_name))
        badge = status_badge(sec_status)
        title = section_title(md_name)
        parts.append(
            f'<section id="{sec_id}">\n'
            f'<div class="section-meta"><span>Documento</span>{badge}</div>\n'
            f'<h3>{title}</h3>\n'
            f'<div class="doc-body">\n{html_content}\n</div>\n'
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

    return f"""<div class="stat-row">
      <div class="stat"><div class="n coppc">{completed_phases}/{total_phases}</div><div class="l">fases ativas/concluídas</div></div>
      <div class="stat"><div class="n tealc">{cpp_tests}</div><div class="l">testes C++ verdes</div></div>
      <div class="stat"><div class="n coppc">{py_tests}</div><div class="l">testes Python registrados</div></div>
      <div class="stat"><div class="n tealc">{v_done}/10</div><div class="l">validações iniciadas</div></div>
    </div>"""


def generate_html(status: dict, dry_run: bool = False) -> str:
    today = date.today().isoformat()
    last_updated = status.get("last_updated", today)
    version = status.get("project_version", "0.1.0")

    sidebar = build_sidebar(status)
    sections = build_sections(status)
    hero = build_hero_stats(status)

    # Aviso se nenhuma validação numérica foi executada
    validation = status.get("validation", {})
    any_validated = any(v == "validated" for v in validation.values())
    warning_html = ""
    if not any_validated:
        warning_html = """<div class="note warn">
      <span class="nt">Aviso de validação</span>
      Nenhuma validação numérica de regressão contra legado foi marcada como validada.
      Testes sintéticos e validações de contrato aparecem em <a href="#results">Resultados de Validação</a>.
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>lot-salt-suite — Documentação Técnica</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,400&family=Hanken+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:#211b14;
    --ink-soft:#4a4239;
    --paper:#f7f3ec;
    --paper-2:#efe8dc;
    --sidebar:#191f23;
    --sidebar-2:#222a2f;
    --sidebar-ink:#c7cdcf;
    --sidebar-ink-dim:#7d878c;
    --copper:#b4632c;
    --copper-bright:#d07a3c;
    --teal:#1f6f6b;
    --teal-bright:#2c8f89;
    --rule:#ddd3c4;
    --rule-soft:#e8e0d2;
    --code-bg:#20262a;
    --code-ink:#dfe4e3;
    --warn:#9a5b1f;
    --ok:#2c7a4b;
    --bad:#a33a2a;
    --info:#2f638f;
    --impl:#6b4a86;
    --shadow:0 1px 2px rgba(33,27,20,.06),0 8px 28px rgba(33,27,20,.08);
    --maxw:880px;
    --sbw:300px;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html{{scroll-behavior:smooth}}
  body{{
    font-family:'Hanken Grotesk',Arial,sans-serif;
    background:var(--paper);
    color:var(--ink);
    line-height:1.65;
    font-size:16px;
    -webkit-font-smoothing:antialiased;
  }}
  .sidebar{{
    position:fixed;top:0;left:0;bottom:0;width:var(--sbw);
    background:var(--sidebar);
    color:var(--sidebar-ink);
    display:flex;flex-direction:column;
    border-right:1px solid #0e1316;
    z-index:50;
  }}
  .brand{{padding:26px 26px 18px;border-bottom:1px solid #0e1316}}
  .brand h1{{
    font-family:'Fraunces',Georgia,serif;
    font-weight:600;font-size:25px;letter-spacing:0;
    color:#f2ede4;line-height:1.05;display:flex;align-items:baseline;gap:8px;
  }}
  .brand h1 .dot{{color:var(--copper-bright)}}
  .brand .sub{{font-size:12px;color:var(--sidebar-ink-dim);margin-top:7px;letter-spacing:.02em;font-weight:500}}
  .brand .ver{{
    display:inline-block;margin-top:12px;
    font-family:'IBM Plex Mono',Consolas,monospace;
    font-size:10.5px;letter-spacing:.04em;color:var(--teal-bright);
    border:1px solid #2c3a3a;background:#16201f;padding:3px 8px;border-radius:5px;
  }}
  .search-wrap{{padding:16px 20px 8px}}
  .search-wrap input{{
    width:100%;background:var(--sidebar-2);border:1px solid #2e373c;color:#e7ebec;
    font-family:'IBM Plex Mono',Consolas,monospace;font-size:12.5px;
    padding:9px 12px;border-radius:7px;outline:none;transition:border-color .15s;
  }}
  .search-wrap input:focus{{border-color:var(--teal)}}
  .search-wrap input::placeholder{{color:#69737a}}
  nav{{flex:1;overflow-y:auto;padding:8px 12px 40px}}
  nav::-webkit-scrollbar{{width:9px}}
  nav::-webkit-scrollbar-thumb{{background:#2b3338;border-radius:5px}}
  .nav-group{{margin-top:18px}}
  .nav-group > .label{{
    font-size:10.5px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
    color:var(--sidebar-ink-dim);padding:0 14px 7px;
  }}
  nav a{{
    display:flex;align-items:center;justify-content:space-between;gap:10px;
    color:var(--sidebar-ink);text-decoration:none;font-size:13.5px;
    padding:6.5px 14px;border-radius:7px;transition:background .13s,color .13s;
  }}
  nav a:hover{{background:#232c31;color:#fff}}
  nav a.active{{background:#243230;color:#fff;box-shadow:inset 2px 0 0 var(--copper-bright)}}
  .nav-dot{{width:8px;height:8px;border-radius:999px;display:inline-block;flex:0 0 auto}}
  .nav-hidden{{display:none!important}}
  .pill{{
    display:inline-block;border-radius:999px;padding:3px 9px;
    font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;
  }}
  .pill-ok,.nav-dot.pill-ok{{background:#dfeee5;color:#24643d}}
  .pill-warn,.nav-dot.pill-warn{{background:#f4e3c7;color:#7a4b1b}}
  .pill-bad,.nav-dot.pill-bad{{background:#f2d6cf;color:#8c2f23}}
  .pill-info,.nav-dot.pill-info{{background:#d9e8ef;color:#245c7e}}
  .pill-impl,.nav-dot.pill-impl{{background:#e8e0ef;color:#5c3d77}}
  .pill-muted,.nav-dot.pill-muted{{background:#e8e0d2;color:#5a5043}}
  main{{margin-left:var(--sbw);padding:0}}
  .hero{{
    background:
      radial-gradient(900px 380px at 88% -10%, rgba(180,99,44,.12), transparent 60%),
      radial-gradient(700px 340px at 0% 0%, rgba(31,111,107,.10), transparent 55%),
      var(--paper);
    border-bottom:1px solid var(--rule);
    padding:62px 60px 46px;
  }}
  .hero .eyebrow{{
    font-family:'IBM Plex Mono',Consolas,monospace;font-size:12px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--copper);font-weight:600;
  }}
  .hero h2{{
    font-family:'Fraunces',Georgia,serif;font-weight:600;
    font-size:46px;line-height:1.04;letter-spacing:0;margin:14px 0 0;max-width:800px;
  }}
  .hero p{{margin-top:18px;max-width:700px;font-size:17px;color:var(--ink-soft)}}
  .lead{{font-size:17.5px;color:var(--ink)!important;max-width:720px}}
  .stat-row{{display:flex;gap:14px;flex-wrap:wrap;margin-top:30px}}
  .stat{{
    background:#fff;border:1px solid var(--rule);border-radius:8px;
    padding:14px 18px;min-width:132px;box-shadow:var(--shadow);
  }}
  .stat .n{{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:27px;line-height:1}}
  .stat .n.tealc{{color:var(--teal)}}
  .stat .n.coppc{{color:var(--copper)}}
  .stat .l{{font-size:11.5px;color:var(--ink-soft);margin-top:5px;letter-spacing:.02em}}
  .content{{padding:18px 60px 120px;max-width:calc(var(--maxw) + 120px)}}
  section{{padding-top:40px;scroll-margin-top:20px}}
  section > h3{{
    font-family:'Fraunces',Georgia,serif;font-weight:600;
    font-size:30px;letter-spacing:0;padding-bottom:12px;margin-bottom:8px;
    border-bottom:2px solid var(--ink);display:inline-block;
  }}
  .section-meta{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
  .section-meta > span:first-child{{
    font-family:'IBM Plex Mono',Consolas,monospace;font-size:11px;letter-spacing:.12em;
    text-transform:uppercase;color:var(--copper);font-weight:600;
  }}
  .doc-body h2{{
    font-family:'Fraunces',Georgia,serif;font-weight:600;
    font-size:21px;margin:30px 0 10px;letter-spacing:0;color:var(--ink);
  }}
  .doc-body h3{{font-size:18px;margin:24px 0 8px;color:var(--teal);font-weight:700}}
  .doc-body h4{{font-size:16px;margin:18px 0 8px;color:var(--ink);font-weight:700}}
  .doc-body p{{margin:13px 0;color:var(--ink-soft)}}
  .doc-body p strong{{color:var(--ink);font-weight:600}}
  a{{color:var(--teal);text-decoration:none;border-bottom:1px solid var(--teal-bright)}}
  a:hover{{background:#e7efee}}
  ul,ol{{margin:14px 0 14px 4px;padding-left:22px;color:var(--ink-soft)}}
  li{{margin:7px 0}}
  li strong{{color:var(--ink)}}
  .note{{
    border-left:3px solid var(--teal);background:#edf4f3;
    padding:13px 18px;border-radius:0 8px 8px 0;margin:16px 0;
    font-size:14.5px;color:#234b48;
  }}
  .note.warn{{border-left-color:var(--warn);background:#f8efe2;color:#6e4a1e}}
  .note .nt{{font-weight:700;display:block;margin-bottom:3px;font-size:12px;letter-spacing:.05em;text-transform:uppercase}}
  blockquote{{
    border-left:3px solid var(--teal);background:#edf4f3;
    padding:13px 18px;border-radius:0 8px 8px 0;margin:16px 0;color:#234b48;
  }}
  table{{border-collapse:collapse;width:100%;margin:16px 0;font-size:13.5px}}
  th,td{{text-align:left;padding:9px 13px;border-bottom:1px solid var(--rule-soft);vertical-align:top}}
  th{{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-soft);border-bottom:2px solid var(--rule)}}
  td{{color:var(--ink-soft)}}
  td code,th code{{font-family:'IBM Plex Mono',Consolas,monospace;font-size:12px;color:var(--copper)}}
  tr:hover td{{background:#fbf8f2}}
  code{{
    font-family:'IBM Plex Mono',Consolas,monospace;font-size:.88em;
    background:var(--paper-2);color:#7a4420;
    padding:1.5px 6px;border-radius:5px;border:1px solid var(--rule-soft);
  }}
  pre{{
    background:var(--code-bg);color:var(--code-ink);border-radius:8px;
    padding:18px 20px;overflow-x:auto;white-space:pre;
    font-family:'IBM Plex Mono',Consolas,monospace;font-size:13px;line-height:1.6;
    margin:16px 0;border:1px solid #2c343a;
  }}
  pre code{{font-family:inherit;color:inherit;background:none;padding:0;border:none;white-space:pre}}
  .code-wrap{{margin:16px 0}}
  .code-head{{
    display:flex;align-items:center;justify-content:space-between;
    background:#1a2024;border:1px solid #2c343a;border-bottom:none;
    border-radius:8px 8px 0 0;padding:8px 16px;
    font-family:'IBM Plex Mono',Consolas,monospace;font-size:11.5px;
    color:#8b9499;letter-spacing:.03em;
  }}
  .code-head + pre{{margin:0;border-radius:0 0 8px 8px}}
  .copy-btn{{
    background:#2a333a;color:#bcc4c6;border:1px solid #39444b;border-radius:6px;
    padding:3px 10px;font-size:11px;cursor:pointer;font-family:'IBM Plex Mono',Consolas,monospace;
  }}
  .copy-btn:hover{{background:var(--teal);color:#fff;border-color:var(--teal)}}
  .copy-btn.done{{background:var(--ok);color:#fff;border-color:var(--ok)}}
  footer{{
    margin-left:var(--sbw);background:var(--sidebar);color:var(--sidebar-ink-dim);
    padding:30px 60px;font-size:13px;border-top:1px solid #0e1316;
  }}
  footer strong{{color:var(--sidebar-ink)}}
  .mono{{font-family:'IBM Plex Mono',Consolas,monospace}}
  .menu-btn{{
    display:none;position:fixed;top:16px;right:16px;z-index:60;
    background:var(--sidebar);color:#fff;border:none;border-radius:8px;
    width:44px;height:44px;font-size:20px;cursor:pointer;align-items:center;justify-content:center;
    box-shadow:var(--shadow);
  }}
  @media(max-width:1080px){{
    :root{{--sbw:0px}}
    .sidebar{{transform:translateX(-100%);transition:transform .25s}}
    .sidebar.show{{transform:translateX(0);width:300px}}
    main,footer{{margin-left:0}}
    .hero,.content,footer{{padding-left:26px;padding-right:26px}}
    .menu-btn{{display:flex}}
  }}
  @media(max-width:720px){{
    .hero{{padding-top:76px}}
    .hero h2{{font-size:34px}}
    .content{{padding-bottom:70px}}
    table{{display:block;overflow-x:auto}}
  }}
</style>
</head>
<body>

<button class="menu-btn" id="menuBtn" aria-label="Abrir navegação">☰</button>

<aside class="sidebar" id="sidebar">
  <div class="brand">
    <h1>lot-salt-suite<span class="dot">.</span></h1>
    <div class="sub">LOT · APB · Fluência de sal</div>
    <span class="ver">v{version} · atualizado {last_updated}</span>
  </div>
  <div class="search-wrap">
    <input type="text" id="navSearch" placeholder="buscar na navegação..." autocomplete="off">
  </div>
  <nav id="nav">
    {sidebar}
  </nav>
</aside>

<main>
  <div class="hero">
    <div class="eyebrow">Documentação técnica · C++20 / Python</div>
    <h2>Simulador integrado de LOT, APB e fluência de sal</h2>
    <p class="lead">Manual navegável do projeto, com formulações, contratos de entrada, validação, arquitetura, auditorias e riscos conhecidos em um único arquivo HTML gerado a partir dos Markdown versionados.</p>
    {hero}
  </div>
  <div class="content">
    {warning_html}
    {sections}
  </div>
</main>
<footer><strong>lot-salt-suite</strong> v{version} · Gerado em {today} por <span class="mono">generate_docs_index.py</span></footer>
<script>
  const sidebar = document.getElementById('sidebar');
  const menuBtn = document.getElementById('menuBtn');
  const navSearch = document.getElementById('navSearch');
  const navLinks = Array.from(document.querySelectorAll('#nav a'));
  const sectionsForNav = navLinks
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

  menuBtn.addEventListener('click', () => sidebar.classList.toggle('show'));

  navSearch.addEventListener('input', () => {{
    const q = navSearch.value.trim().toLowerCase();
    navLinks.forEach((link) => {{
      link.classList.toggle('nav-hidden', q && !link.textContent.toLowerCase().includes(q));
    }});
    document.querySelectorAll('.nav-group').forEach((group) => {{
      const visible = Array.from(group.querySelectorAll('a')).some((a) => !a.classList.contains('nav-hidden'));
      group.classList.toggle('nav-hidden', !visible);
    }});
  }});

  const activateCurrent = () => {{
    let current = sectionsForNav[0]?.id;
    const offset = 90;
    sectionsForNav.forEach((section) => {{
      if (section.getBoundingClientRect().top <= offset) current = section.id;
    }});
    navLinks.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === '#' + current));
  }};
  document.addEventListener('scroll', activateCurrent, {{passive:true}});
  activateCurrent();

  navLinks.forEach((link) => {{
    link.addEventListener('click', () => {{
      if (window.innerWidth <= 1080) sidebar.classList.remove('show');
    }});
  }});

  document.querySelectorAll('pre').forEach((pre, i) => {{
    const wrap = document.createElement('div');
    wrap.className = 'code-wrap';
    const head = document.createElement('div');
    head.className = 'code-head';
    const label = document.createElement('span');
    label.textContent = 'bloco de codigo ' + String(i + 1).padStart(2, '0');
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = 'copiar';
    head.append(label, btn);
    pre.parentNode.insertBefore(wrap, pre);
    wrap.append(head, pre);
    btn.addEventListener('click', async () => {{
      await navigator.clipboard.writeText(pre.innerText);
      btn.textContent = 'copiado';
      btn.classList.add('done');
      setTimeout(() => {{ btn.textContent = 'copiar'; btn.classList.remove('done'); }}, 1400);
    }});
  }});
</script>
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
