# 12 — Resultados de Validação

**Status:** BASELINES CAPTURADOS | **Última atualização:** 2026-06-01

---

> ## AVISO
>
> Nenhuma validação foi executada no **código novo** do `lot-salt-suite`.
> Os baselines abaixo são saídas do **legado LOT_APB_v5** compilado e executado
> em 2026-06-01 com g++ 16.1.0 + flags `-w -fpermissive`.
>
> Compilação: `cmake -G "MinGW Makefiles" -DCMAKE_CXX_FLAGS="-w -fpermissive"`

---

## Baselines LOT_APB_v5 capturados (2026-06-01)

| Baseline | Arquivo | Tamanho | Execução | Status |
|---------|---------|---------|---------|--------|
| SCORE-MRO-28 completo (output) | `apbv5_SCORE-MRO-28_output.json` | 47 KB | 0.3 s | **Capturado** |
| SCORE-MRO-28 original (output) | `apbv5_SCORE-MRO-28_original_output.json` | 27 KB | pré-existente | **Capturado** |
| SCORE-MRO-28 Ev_temp (output) | `apbv5_SCORE-MRO-28_Ev_temp_output.json` | 47 KB | pré-existente | **Capturado** |
| MRO-28 reduzido (input ref) | `apbv5_MRO-28_min_times_input.json` | 189 KB | ref de entrada | **Capturado** |

> Arquivos de entrada completos (57 MB) e output detalhado (29 MB) mantidos
> apenas localmente — excluídos do git por `.gitignore`.

## Nota de compilação do legado

```
Compilador : g++ 16.1.0 (MSYS2/UCRT64)
Flags      : -w -fpermissive (necessário por incompatibilidade Eigen antigo × GCC 16)
Eigen      : versão bundled dentro de legance/LOT_APB_v5/include/Eigen/
Data       : 2026-06-01
Executável : legance/LOT_APB_v5/bin/apb.exe
```

**Risco registrado:** o uso de `-fpermissive` pode ocultar divergências de comportamento
em relação ao compilador original. Documentado em `docs/08_known_issues.md`.

---

## Status da suíte V0-V9

| Nível | Descrição | Status | Data | Resultado |
|-------|-----------|--------|------|-----------|
| V0 | Parser YAML | Não executado | — | — |
| V1 | Fluido isolado analítico | Não executado | — | — |
| V2 | Solução de Lamé (elástico) | Não executado | — | — |
| V3 | LOT simples sem sal | Não executado | — | — |
| V4 | APB simples sem sal | Não executado | — | — |
| V5 | Sal isolado (halita) | Não executado | — | — |
| V6 | LOT + sal | Não executado | — | — |
| V7 | APB + sal | Não executado | — | — |
| V8 | Caso acoplado completo | Não executado | — | — |
| V9 | Regressão automática | Não executado | — | — |

## Fase 6.2 — Testes sintéticos LOT/PKN

**Data:** 2026-06-01

**Executado nesta fase:**

- Testes Catch2 do parser para os YAMLs `lot-pkn`.
- Testes Catch2 do `BreakdownDetector` com series sintéticas.
- Testes Catch2 do esqueleto sintético de `PknModel`.
- Validação via CLI dos casos:
  - `cases/validation/lot_pkn_minimal.yaml`
  - `cases/validation/lot_pkn_with_leakoff.yaml`
  - `cases/lot_tese_migrated/buz67d_pkn.yaml`

**Importante:** nao houve validacao numerica contra `legance/LOT_Tese` ou
`legance/LOT_APB_v5`. R09 (`/ M_PI / 22`) permanece blocker para regressao
PKN legado x moderno. O caso `buz67d_pkn.yaml` e contrato sintatico/migratorio,
nao baseline numerico.

## Baselines capturados

| Baseline | Arquivo | Status | Data |
|---------|---------|--------|------|
| LOT_Tese / LOTTeste | `tests/baselines/lot_tese_lotsimples.json` | Não capturado | — |
| LOT_Tese / 8-BUZ-67D elliptical | `tests/baselines/lot_tese_buz67d_ell.json` | Não capturado | — |
| LOT_APB_v5 / SCORE-MRO-28 | `tests/baselines/apbv5_score_mro_28.json` | Não capturado | — |
| LOT_APB_v5 / SCORE-MRO-28 elastic | `tests/baselines/apbv5_score_mro_28_elastic.json` | Não capturado | — |
| saltcreep / halita DM | `tests/baselines/saltcreep_halita_dm.csv` | Não capturado | — |

## Como atualizar este arquivo

Somente após executar os testes:

```bash
# Exemplo: executar V0 (parser)
./build/lot-sim inspect --case cases/validation/lot_simple.yaml
# Se saiu sem erro → atualizar tabela V0 com status=PASSOU e data

# Exemplo: executar V3 (LOT sem sal)
./build/lot-sim run --case cases/lot_tese_migrated/lotsimples.yaml --mode lot
# Comparar com baseline:
python tools/compare_results.py \
    results/lotsimples/lot_curve.csv \
    tests/baselines/lot_tese_lotsimples.json \
    --tolerance 0.01
# Registrar: data, erro L2 obtido, erro L∞ obtido, tempo de execução
```
