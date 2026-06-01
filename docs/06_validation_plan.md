# 06 — Plano de Validação

**Status:** Planejado | **Última atualização:** 2026-06-01

## Sequência V0-V9

| Nível | Teste | Critério |
|-------|-------|----------|
| V0 | Parser YAML: carregar e imprimir caso | Zero erros de parsing |
| V1 | Fluido isolado: PVT analítico | Erro < 0.01% |
| V2 | Elástico isolado: solução de Lamé | Erro L2 < 1e-6 |
| V3 | LOT simples sem sal (LOTTeste) | Curva P×V dentro de 1% do legado |
| V4 | APB simples sem sal (BUZ29-VISCO-DELL) | ΔP máx dentro de 1% |
| V5 | Sal isolado (halita, mecanismo duplo) | Erro < 0.1% vs saltcreep |
| V6 | LOT + sal (8-BUZ-67D elliptical) | Erro < 1% vs LOT_Tese |
| V7 | APB + sal (BUZ29 cenário 1) | Erro < 1% vs LOT_APB_v5 |
| V8 | Caso acoplado completo | Comparação com melhor referência disponível |
| V9 | Regressão automática (suíte completa) | 100% dentro de tolerância |

## Status atual

| Nível | Status | Data | Resultado |
|-------|--------|------|-----------|
| V0-V9 | Não executado | — | — |

> **REGRA:** Nunca atualizar status para "executado" sem resultados reais documentados
> em `docs/12_validation_results.md`.

## Captura de baselines (pré-requisito de V3-V7)

Antes de V3-V7, executar os legados e salvar em `tests/baselines/`:

```bash
# Compilar e executar LOT_APB_v5
cd legance/LOT_APB_v5 && make main
./main SCORE-MRO-28_input.json
# Salvar output como tests/baselines/apbv5_score_mro_28.json
```

## Tolerâncias por nível

| Nível | Métrica | Tolerância |
|-------|---------|-----------|
| V1 | Erro relativo em densidade | < 0.01% |
| V2 | Erro L2 em deslocamento | < 1e-6 |
| V3, V4 | Erro L2 em pressão | < 1% |
| V5 | Erro L2 em deslocamento radial | < 0.1% |
| V6, V7 | Erro L2 em pressão + deslocamento | < 1% |
| V8 | A definir após V6+V7 | TBD |
| V9 | Todos os critérios acima | 100% dentro |
