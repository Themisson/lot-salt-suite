#!/usr/bin/env python3
"""
update_devlog.py — Atualiza docs/dev-log.md após git commit ou git push.

Uso:
    python tools/update_devlog.py           # entrada automática (último commit)
    python tools/update_devlog.py --dry-run # imprime sem salvar
    python tools/update_devlog.py --status  # atualiza apenas o bloco "Estado atual"

Acionado automaticamente via hook em .claude/settings.json após git commit/push.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEVLOG = ROOT / "docs" / "dev-log.md"
SKIP_MARKER = "[skip-devlog]"
SALTCREEP_PREFIX = "external/saltcreep/"
BASELINES_PREFIX = "tests/baselines/"


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], *, cwd: Path = ROOT) -> str:
    try:
        return subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.DEVNULL,
                                       text=True, encoding="utf-8").strip()
    except subprocess.CalledProcessError:
        return ""


def get_last_commit() -> dict:
    raw = _run(["git", "log", "-1",
                "--pretty=format:%H|%h|%an|%ad|%s",
                "--date=format:%Y-%m-%d %H:%M"])
    if not raw:
        return {}
    parts = raw.split("|", 4)
    if len(parts) < 5:
        return {}
    return {"hash": parts[0], "short": parts[1], "author": parts[2],
            "date": parts[3], "subject": parts[4]}


def get_changed_files(hash_: str) -> list[str]:
    return _run(["git", "diff", "--name-only",
                 f"{hash_}~1", hash_]).splitlines()


def get_test_summary() -> str:
    """Tenta ler o último resultado de ctest."""
    ctest_log = ROOT / "build" / "Testing" / "Temporary" / "LastTest.log"
    if not ctest_log.exists():
        return "nenhum (módulos ainda não implementados)"
    lines = ctest_log.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in reversed(lines):
        if "tests passed" in line.lower() or "failed" in line.lower():
            return line.strip()
    return "ver build/Testing/Temporary/LastTest.log"


def get_current_phase() -> str:
    """Infere fase atual pelo último commit e estado de arquivos."""
    subject = get_last_commit().get("subject", "")
    for fase, keyword in [
        ("5 — CLI + CaseParser", "case_parser"),
        ("5 — CLI + CaseParser", "units"),
        ("5 — CLI + CaseParser", "lot-sim"),
        ("4 — Baselines", "baseline"),
        ("3 — Agentes/Skills + Auditoria", "audit"),
        ("2 — Documentação", "docs"),
        ("1 — Estrutura", "structure"),
    ]:
        if keyword in subject.lower():
            return fase
    return "ver commits recentes"


def count_tests() -> tuple[int, int]:
    """Conta arquivos de teste existentes."""
    cpp_tests = list((ROOT / "tests" / "cpp").glob("test_*.cpp"))
    py_tests  = list((ROOT / "tests" / "python").glob("test_*.py"))
    return len(cpp_tests), len(py_tests)


# ---------------------------------------------------------------------------
# Entry builder
# ---------------------------------------------------------------------------

def build_entry(commit: dict, files: list[str], dry_run: bool = False) -> str:
    saltcreep_files = [f for f in files if f.startswith(SALTCREEP_PREFIX)]
    baseline_files  = [f for f in files if f.startswith(BASELINES_PREFIX)]
    other_files     = [f for f in files
                       if not f.startswith(SALTCREEP_PREFIX)
                       and not f.startswith(BASELINES_PREFIX)
                       and f != "docs/dev-log.md"]

    tests = get_test_summary()
    cpp_n, py_n = count_tests()

    lines = [
        f"### [{commit['date']}] `{commit['short']}` — {commit['author']}",
        f"**Commit:** `{commit['subject']}`",
        f"**Testes C++:** {cpp_n} arquivos | **Testes Python:** {py_n} arquivos",
        f"**Último resultado ctest:** {tests}",
    ]

    if other_files:
        lines.append("**Arquivos alterados:**")
        for f in other_files[:12]:
            lines.append(f"- `{f}`")
        if len(other_files) > 12:
            lines.append(f"- … e mais {len(other_files) - 12} arquivos")

    if baseline_files:
        lines.append("**Baselines atualizados:**")
        for f in baseline_files:
            lines.append(f"- `{f}`")

    if saltcreep_files:
        lines.append("")
        lines.append("**⚠ Modificações em external/saltcreep/:**")
        for f in saltcreep_files[:8]:
            lines.append(f"- `{f}`")
        if len(saltcreep_files) > 8:
            lines.append(f"- … e mais {len(saltcreep_files) - 8} arquivos")
        lines.append("> Atualizar a seção 'Modificações em andamento no saltcreep' abaixo.")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Status block updater
# ---------------------------------------------------------------------------

def update_status_block(content: str) -> str:
    """Substitui o bloco '## Estado atual' com dados frescos do git."""
    commit  = get_last_commit()
    cpp_n, py_n = count_tests()
    baselines = list((ROOT / "tests" / "baselines").glob("*.json"))

    new_block = (
        "## Estado atual do projeto\n\n"
        "```\n"
        f"Fase ativa  : {get_current_phase()}\n"
        f"Branch      : main\n"
        f"Repositório : https://github.com/Themisson/lot-salt-suite\n"
        f"Último push : {commit.get('date', '—')[:10]}\n"
        f"Testes C++  : {cpp_n}\n"
        f"Testes Py   : {py_n}\n"
        f"Baselines   : {len(baselines)} capturados\n"
        "Saltcreep   : verificar seção abaixo\n"
        "```"
    )
    return re.sub(
        r"## Estado atual do projeto\n```.*?```",
        new_block,
        content,
        flags=re.DOTALL,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza docs/dev-log.md")
    parser.add_argument("--dry-run", action="store_true",
                        help="Imprime a entrada sem salvar")
    parser.add_argument("--status", action="store_true",
                        help="Atualiza apenas o bloco de estado atual")
    args = parser.parse_args()

    commit = get_last_commit()
    if not commit:
        print("update_devlog: nenhum commit encontrado. Abortando.")
        sys.exit(0)

    # Evitar loop infinito: não processar commits do próprio devlog
    if SKIP_MARKER in commit.get("subject", ""):
        print(f"update_devlog: commit marcado com {SKIP_MARKER}. Ignorando.")
        sys.exit(0)

    # Evitar duplicatas: verificar se o hash já está no devlog
    if DEVLOG.exists():
        existing = DEVLOG.read_text(encoding="utf-8")
        if commit["short"] in existing:
            if args.status:
                pass  # status sempre atualiza
            else:
                print(f"update_devlog: `{commit['short']}` já registrado. Ignorando.")
                sys.exit(0)
    else:
        existing = ""

    if args.status:
        if not existing:
            print("update_devlog: dev-log.md não encontrado.")
            sys.exit(1)
        updated = update_status_block(existing)
        if not args.dry_run:
            DEVLOG.write_text(updated, encoding="utf-8")
            print("update_devlog: bloco de estado atualizado.")
        else:
            print(updated[:800])
        sys.exit(0)

    files   = get_changed_files(commit["hash"])
    entry   = build_entry(commit, files, dry_run=args.dry_run)

    if args.dry_run:
        print("=== DRY RUN — entrada que seria adicionada ===")
        print(entry)
        sys.exit(0)

    # Inserir nova entrada logo após o marcador "## Entradas de sessão"
    marker = "## Entradas de sessão"
    separator = "\n---\n\n"

    if marker in existing:
        updated = existing.replace(
            marker + "\n\n---",
            marker + "\n\n---\n\n" + entry + "\n---",
            1,
        )
    else:
        updated = existing + "\n\n---\n\n" + entry

    # Atualizar bloco de estado atual
    updated = update_status_block(updated)

    DEVLOG.write_text(updated, encoding="utf-8")
    print(f"update_devlog: entrada `{commit['short']}` adicionada a docs/dev-log.md")

    # Commitar o dev-log automaticamente (commit silencioso)
    subprocess.run(
        ["git", "add", "docs/dev-log.md"],
        cwd=ROOT, check=False
    )
    subprocess.run(
        ["git", "commit", "-m",
         f"chore: auto-update dev-log for {commit['short']} {SKIP_MARKER}"],
        cwd=ROOT, check=False
    )
    print("update_devlog: dev-log.md commitado automaticamente.")


if __name__ == "__main__":
    main()
