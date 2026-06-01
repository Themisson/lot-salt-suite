# Plano de Commits Git — lot-salt-suite

Este arquivo documenta os comandos Git a executar para versionar a estrutura inicial.
**Executar somente após aprovação explícita do usuário.**

## Pré-requisitos

- Git instalado
- Diretório `c:\Users\themi\Desktop\lot-salt-suite` é o repositório raiz
- Ter definido `git config user.name` e `git config user.email`

## Sequência de comandos

```bash
# 1. Inicializar repositório Git
git init

# 2. Verificar status
git status

# 3. Adicionar arquivos de configuração do projeto
git add .gitignore README.md CLAUDE.md AGENTS.md CMakeLists.txt pyproject.toml

# 4. Commit inicial — metadados e configuração
git commit -m "chore: initialize lot-salt-suite project structure

- Add CLAUDE.md with project rules and architecture
- Add AGENTS.md with agent guidance
- Add .gitignore with policies for results/, baselines/, credentials
- Add CMakeLists.txt stub (C++20, yaml-cpp, Catch2, Eigen from saltcreep)
- Add pyproject.toml for lotsaltpost Python package"

# 5. Adicionar estrutura de diretórios
git add legacy/ src/ include/ apps/ cases/ schemas/ tests/ postprocess/ tools/

# 6. Commit — estrutura de diretórios
git commit -m "chore: add module directory structure with .gitkeep files

Modules: core, io, units, wellbore, fluids, thermal, rocks, salt,
lot, apb, geomechanics, coupling, validation, cli
Cases: lot_tese_migrated, lot_apb_v5_migrated, validation, coupled
Tests: cpp, python, regression, baselines (frozen)"

# 7. Adicionar agentes e skills
git add .claude/ .agents/

# 8. Commit — agentes e skills
git commit -m "feat: add Claude Code agents and skills configuration

Agents: cpp-pro, verifier, legacy-explorer, docs-sync, salt-adapter
Skills (x2): formulation-audit, cpp-refactor, validation-benchmark,
             postprocess-report, docs-html-report, lot-salt-integration
Settings: Allow/Deny permissions preventing legance/ and external/ edits"

# 9. Adicionar AGENTS.md por diretório
git add legacy/AGENTS.md external/AGENTS.md src/AGENTS.md include/AGENTS.md
git add apps/AGENTS.md cases/AGENTS.md schemas/AGENTS.md tests/AGENTS.md
git add postprocess/AGENTS.md tools/AGENTS.md docs/AGENTS.md legacy/README.md

# 10. Commit — AGENTS.md por diretório
git commit -m "docs: add per-directory AGENTS.md guardrails

Each directory gets rules: legacy/ is read-only, external/ is reference-only,
src/ requires C++20 + tests, cases/ requires schema validation, etc."

# 11. Adicionar documentação técnica
git add docs/

# 12. Commit — documentação e index.html
git commit -m "docs: add 16 technical docs and interactive docs/index.html

docs/00-15: project overview, inventory, LOT/APB/salt formulation,
input formats, validation plan, architecture, known issues,
migration plan, postprocessing, CLI usage, validation results (empty),
coupling algorithm, developer guide, changelog

docs/index.html: offline-first interactive manual with dark sidebar,
hero stats, status badges (planned/in_progress/not_started),
validation warning banner (no results executed yet)

tools/docs_status.yaml: single source of truth for section status
tools/generate_docs_index.py: HTML generator from Markdown files"

# 13. Definir branch principal
git branch -M main

# 14. Verificar estado final
git log --oneline
git status

# ============================================================
# PARA PUBLICAR NO GITHUB (somente com URL e autorização):
# ============================================================
# git remote add origin <URL_DO_REPOSITORIO>
# git push -u origin main
```

## Resultado esperado

```
$ git log --oneline
<hash> docs: add 16 technical docs and interactive docs/index.html
<hash> docs: add per-directory AGENTS.md guardrails
<hash> feat: add Claude Code agents and skills configuration
<hash> chore: add module directory structure with .gitkeep files
<hash> chore: initialize lot-salt-suite project structure
```

## O que NÃO versionar ainda

- `legance/` — código legado; pode ser submodule no futuro ou mantido localmente
- `external/saltcreep/` — referência externa; usar como submodule Git no futuro
- `build/` — artefatos de build (no .gitignore)
- `results/` — saídas pesadas de simulação (no .gitignore)
- `tests/baselines/` — baselines gerados (a versionar com Git LFS ou separadamente)
