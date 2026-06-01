# 11 — Uso da CLI lot-sim

**Status:** Planejado | **Última atualização:** 2026-06-01

## Subcomandos

### run

`ash
lot-sim run --case <arquivo.yaml> --mode <modo> [--output <dir>] [--verbose]
`

Modos disponíveis:

| Modo | Descrição | Fase |
|------|-----------|------|
| `lot` | LOT isolado | 5-6 |
| `apb` | APB isolado | 5-6 |
| `salt` | Sal isolado | 8 |
| `lot-salt` | LOT acoplado ao sal | 8 |
| `apb-salt` | APB acoplado ao sal | 8 |
| `coupled` | Acoplamento completo | 8-10 |

### inspect

`ash
lot-sim inspect --case <arquivo.yaml>
lot-sim inspect --case <arquivo.json> --format json
`

Valida o arquivo de caso contra o schema e imprime resumo.

### validate

`ash
lot-sim validate --suite regression
lot-sim validate --case <arquivo.yaml> --baseline <baseline.json>
`

### migrate

`ash
lot-sim migrate --from-json <arquivo.json> --to-yaml <saida.yaml>
`

Converte JSON legado para YAML.

### list

`ash
lot-sim list --dir cases/
`

## Exemplos

`ash
# Inspecionar caso migrado
lot-sim inspect --case cases/lot_apb_v5_migrated/score_mro_28.yaml

# Executar APB com caso migrado
lot-sim run --case cases/lot_apb_v5_migrated/score_mro_28.yaml --mode apb

# Migrar JSON legado
lot-sim migrate --from-json legance/LOT_APB_v5/SCORE-MRO-28_input.json \
                --to-yaml cases/lot_apb_v5_migrated/score_mro_28.yaml

# Validar regressão
lot-sim validate --suite regression
`
"@

System.Collections.Hashtable["12_validation_results.md"] = @"
# 12 — Resultados de Validação

**Status:** NÃO INICIADO | **Última atualização:** 2026-06-01

> ## AVISO CRÍTICO
>
> Este arquivo não contém nenhum resultado real de execução ainda.
> Nenhuma validação foi executada no código novo.
> Não alterar este arquivo sem rodar os testes documentados em docs/06_validation_plan.md.

## Status da suíte V0-V9

| Nível | Status | Data | Resultado |
|-------|--------|------|-----------|
| V0 | Não executado | — | — |
| V1 | Não executado | — | — |
| V2 | Não executado | — | — |
| V3 | Não executado | — | — |
| V4 | Não executado | — | — |
| V5 | Não executado | — | — |
| V6 | Não executado | — | — |
| V7 | Não executado | — | — |
| V8 | Não executado | — | — |
| V9 | Não executado | — | — |

## Como atualizar este arquivo

Somente após executar os testes:

`ash
# Exemplo: executar V0 (parser)
./build/lot-sim inspect --case cases/validation/lot_simple.yaml
# Se saiu sem erro: V0 = PASSOU

# Atualizar a linha correspondente neste arquivo com:
# - Status: PASSOU / FALHOU
# - Data de execução
# - Erro obtido (se V2+)
# - Tempo de execução
`
"@

System.Collections.Hashtable["13_coupling_lot_apb_salt.md"] = @"
# 13 — Acoplamento LOT–APB–Sal

**Status:** Planejado | **Última atualização:** 2026-06-01

## Algoritmo de acoplamento (a implementar na Fase 8)

O módulo `include/coupling/` orquestra a sequência:

`
Para cada passo de tempo dt:
1. Atualizar campo térmico T(z, t)
2. Calcular estado geostático atualizado σ₀(t)
3. LOT: calcular pressão de fratura e leakoff
4. Sal: calcular deformação viscosa da parede do poço
5. APB: calcular pressurização do anular com novo volume
6. Verificar convergência (δP < tolP)
7. Avançar t → t + dt
`

## Interface de acoplamento

O acoplamento entre LOT e sal ocorre via:
- Tensão na parede do poço → `SaltCreepInterface::evaluate()`
- Retorno: taxa de deformação → variação de volume anular
- Variação de volume anular → correção de pressão APB

## Convenção de sinais (a verificar)

> PENDENTE — verificar com `/formulation-audit` antes de implementar.
>
> Questão crítica: tensão compressiva é positiva ou negativa na interface LOT-sal?
