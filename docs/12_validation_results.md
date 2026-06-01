# 12 — Resultados de Validação

**Status:** NÃO INICIADO | **Última atualização:** 2026-06-01

---

> ## AVISO CRÍTICO
>
> **Este arquivo não contém nenhum resultado real de execução.**
>
> Nenhuma validação foi executada no código novo do `lot-salt-suite`.
> Nenhum baseline foi capturado dos legados ainda.
>
> **Não alterar** este arquivo sem executar os testes descritos em
> `docs/06_validation_plan.md` e registrar os outputs reais aqui.

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
