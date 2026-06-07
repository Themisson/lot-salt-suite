# 15 — Changelog

**Última atualização:** 2026-06-01

## [Unreleased]

### Fase 10.16 — Volume anular com drill pipe (2026-06-07)

- Adicionado suporte diagnostico para `wellbore.drill_pipe` no caso BUZ67D
  controlado.
- Registrada a convencao legado/moderno `V_rad = 0.5*(R_outer^2-R_inner^2)*L`
  e `V_total = 2*pi*V_rad`.
- Exportados campos modernos de volume anular em `result.json` sem alterar a
  formulacao PKN.

### Fase 1 — Estrutura do repositório (2026-06-01)

- Criados diretórios: src/, include/, apps/, cases/, schemas/, tests/, postprocess/, tools/, docs/
- Criados: CLAUDE.md, AGENTS.md, README.md, .gitignore, CMakeLists.txt, pyproject.toml
- Criados: legacy/README.md, 11 × AGENTS.md por diretório
- Criados: 6 skills em .claude/skills/ e .agents/skills/
- Criados: 5 subagentes em .claude/agents/
- Criados: .claude/settings.json com permissões Allow/Deny
- Criados: 16 arquivos docs/*.md com estrutura inicial

### Fase 0 — Inventário (anterior)

- Analisado: legance/LOT_Tese/ (17 arquivos main identificados)
- Analisado: legance/LOT_APB_v5/ (10 JSONs identificados)
- Analisado: external/saltcreep/ (120 testes C++ + 21 Python)
- Criados: ANALISE_INICIAL.md, NOVA_ESTRUTURA_REPOSITORIO.md (em versão anterior)
- Criados: target_repo/ com rascunhos de AGENTS.md, CLAUDE.md, docs/, skills/
