# 12 — Resultados de Validação

**Status:** BASELINES CAPTURADOS | **Última atualização:** 2026-06-01

---

> ## AVISO
>
> Nenhuma validação numérica de regressão contra legado foi executada no
> **código novo** do `lot-salt-suite`.
> Os baselines abaixo são saídas do **legado LOT_APB_v5** compilado e executado
> em 2026-06-01 com g++ 16.1.0 + flags `-w -fpermissive`. As validações de
> contrato/sintéticas executadas no código novo ficam registradas por fase
> neste documento e não substituem regressão legado × moderno.
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

## Fase 6.3 — Auditoria documental R09

**Data:** 2026-06-01

**Executado nesta fase:**

- Inspecao somente leitura de `legance/LOT_Tese/`.
- Inspecao somente leitura de `legance/LOT_APB_v5/`.
- Relatorio tecnico em `docs/audits/R09_pkn_mpi22_audit.md`.

**Resultado:** auditoria concluida, sem validacao numerica. A expressao
`/ M_PI / 22` foi localizada em `Conv_bbmin_m3h`, ramo `idQ == 4`; os casos PKN
auditados usam `idQ == 6`, que chama outra conversao. R09 permanece blocker para
regressao PKN legado x moderno ate ensaio numerico comparativo ou documentacao
fisica adicional.

## Fase 6.4 — PknModel fisico minimo em SI

**Data:** 2026-06-01

**Executado nesta fase:**

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build -j`
- `ctest --test-dir build --output-on-failure`
- `.\build\lot-sim.exe validate --case cases\validation\lot_pkn_minimal.yaml`
- `.\build\lot-sim.exe validate --case cases\validation\lot_pkn_with_leakoff.yaml`
- `.\build\lot-sim.exe validate --case cases\lot_tese_migrated\buz67d_pkn.yaml`

**Resultado CTest:** 30 testes Catch2 executados, 30 passaram.

**Resultado CLI:**

| Caso | Resultado |
|------|-----------|
| `cases/validation/lot_pkn_minimal.yaml` | `OK: lot_pkn_minimal_validation` |
| `cases/validation/lot_pkn_with_leakoff.yaml` | `OK: lot_pkn_with_leakoff_validation` |
| `cases/lot_tese_migrated/buz67d_pkn.yaml` | `OK: buz67d_pkn_migrated_contract` |

**Modelo coberto por teste:** `lot::PknModel` gera resultados escalares e
series temporais em SI com largura, comprimento, volume injetado, volume de
fratura, volume de leakoff e pressao liquida finitos e nao negativos. Os testes
cobrem monotonicidade basica, caso fechado sem leakoff, leakoff simplificado,
determinismo e rejeicao de entradas invalidas.

**Importante:** esta fase nao executou regressao contra `legance/LOT_Tese` nem
contra `legance/LOT_APB_v5`. O caso `buz67d_pkn.yaml` continua sendo contrato
sintatico/migratorio. R09 continua bloqueando validacao numerica legado x
moderno.

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
