# 01 — Inventário do Repositório

**Status:** Planejado | **Última atualização:** 2026-06-01

## Nota sobre nomenclatura

> O diretório físico legado se chama `legance/` (herança histórica).
> Toda documentação usa `legacy/` como convenção. O diretório `legacy/` na raiz
> contém apenas `README.md` organizacional.

## Estrutura atual

| Diretório | Status | Descrição |
|-----------|--------|-----------|
| `legance/LOT_Tese/` | Congelado | 17 arquivos main C++ da tese |
| `legance/LOT_APB_v5/` | Congelado | main.cpp + 10 JSONs de caso |
| `external/saltcreep/` | Referência | Solver FEM moderno de sal |
| `docs/` | Em criação | Documentação técnica |
| `target_repo/` | Template | Rascunhos a mover para raiz |
| `prompts/` | Metadoc | Prompts sequenciais |
| `.agents/skills/` | Criado | 6 skills de agentes |
| `.claude/skills/` | Criado | 6 skills Claude Code |

## Inventário de arquivos main (LOT_Tese)

| Arquivo | Tipo | Modelo de sal | LOT |
|---------|------|--------------|-----|
| `LOTTeste.cpp` | LOT simples | Viscoelástico | Padrão |
| `8-BUZ-67D-RJS-VISCO.cpp` | LOT+APB+Sal | Duplo mecanismo | Elliptical |
| `8-BUZ-67D-RJS-VISCO-FULL-3rd-well.cpp` | LOT+APB+Sal completo | Duplo mecanismo | Múltiplas |
| `9-BUZ-39DA-RJS-VISCO.cpp` | LOT+APB+Sal | Duplo mecanismo | — |
| `9-BUZ-39DA-RJS-VISCO-2.cpp` | LOT+APB+Sal variação | Duplo mecanismo | — |
| `7-BUZ-60D-RJS-VISCO-2nd-Well.cpp` | LOT+APB | Viscoelástico | — |
| `BUZ29-VISCO-DELL_PC_APTO.cpp` | APB+Sal validação | Duplo mecanismo | — |
| `BUZ29-VISCO-ZAMORA.cpp` | APB+Sal+Stress | Duplo mecanismo | — |
| `BUZ29-VISCO-first-well.cpp` | APB+Sal | Duplo mecanismo | — |
| `BUZ29-CENÁRIO1-PRESC.cpp` | APB+Sal cenário 1 | Prescrito | — |
| `BUZ29-CENÁRIO1-ZAMORA.cpp` | APB+Sal cenário 1 | Zamora | — |
| `BUZ29-CENÁRIO2-PRESC.cpp` | APB+Sal cenário 2 | Prescrito | — |
| `BUZ29-CENÁRIO2-ZAMORA.cpp` | APB+Sal cenário 2 | Zamora | — |
| `main/8-BUZ-67D-*-circular.cpp` | LOT | Duplo mecanismo | Circular |
| `main/8-BUZ-67D-*-elliptical.cpp` | LOT | Duplo mecanismo | Elliptical |
| `main/8-BUZ-67D-*-penny-shaped.cpp` | LOT | Duplo mecanismo | Penny-shaped |
| `main/8-BUZ-67D-*-pkn.cpp` | LOT | Duplo mecanismo | PKN |

## Inventário de casos JSON (LOT_APB_v5)

| Arquivo | Duração | Tipo |
|---------|---------|------|
| `SCORE-MRO-28_input.json` | ~33000 min | Caso completo |
| `SCORE-MRO-28_output.json` | — | Resultado correspondente |
| `SCORE-MRO-28_original_input.json` | — | Versão original |
| `SCORE-MRO-28_elastic_input.json` | — | Sem sal (elástico) |
| `SCORE-MRO-28_Ev_temp_input.json` | — | Com evolução térmica |
| `MRO-28_min_times_input.json` | 300 min | Versão reduzida |
