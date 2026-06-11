# Phase 10.28B additional well or sensitivity gate

## Resumo executivo

A Fase 10.28B executa o gate duplo definido na Fase 10.28A:

```text
Rota A: procurar BUZ-29D ou outro caso adicional pronto.
Rota B: se o caso adicional não estiver pronto, preparar matriz de sensibilidade BUZ-67D modern-refined.
```

Resultado:

```text
route_decision = ADDITIONAL_WELL_BLOCKED_SENSITIVITY_SELECTED
buz29d_status = BUZ29D_NOT_PKN
sensitivity_matrix_status = SENSITIVITY_MATRIX_READY
recommendation_for_10_28C = RUN_BUZ67D_MODERN_REFINED_SENSITIVITY_MATRIX_IN_10_28C
```

O material BUZ-29D existe no legado, mas os fontes encontrados no gate rápido
não formam ainda um caso PKN moderno rastreável. Há artefatos de saída com PKN
no nome, mas saída legada não basta para criar YAML moderno sem auditar campos
críticos e sem risco de inventar parâmetros.

## Objetivo

O objetivo é decidir se a Fase 10.28C deve executar um poço adicional ou uma
matriz de sensibilidade. Esta fase não altera solver, não altera casos
protegidos, não modifica `legance/` e não tenta validar fratura física.

## Resultado da busca por BUZ-29D

A busca read-only em `legance/LOT_Tese/` encontrou fontes e artefatos BUZ-29D.
Os principais candidatos são:

| Candidato | Tipo | Modelo observado | Status | Observação |
|---|---|---|---|---|
| `legance/LOT_Tese/BUZ29-VISCO-first-well.cpp` | fonte | `penny-shaped` ativo | `NOT_READY_NON_PKN_OR_ALTERNATIVE_MODEL` | Linha PKN aparece comentada. |
| `legance/LOT_Tese/BUZ29-CENÁRIO1 -PRESC.cpp` | fonte | `penny-shaped` ativo | `NOT_READY_NON_PKN_OR_ALTERNATIVE_MODEL` | Não é PKN pronto para o runner moderno atual. |
| `legance/LOT_Tese/BUZ29-CENÁRIO1 -ZAMORA.cpp` | fonte | `circular`/Zamora | `NOT_READY_NON_PKN_OR_ALTERNATIVE_MODEL` | Zamora não deve ser implementado nesta rota. |
| `legance/LOT_Tese/BUZ29-CENÁRIO2-PRESC.cpp` | fonte | `circular` | `NOT_READY_NON_PKN_OR_ALTERNATIVE_MODEL` | Não é PKN pronto. |
| `legance/LOT_Tese/BUZ29-VISCO-DELL_PC_APTO.cpp` | fonte | indefinido no gate rápido | `NEEDS_MORE_AUDIT` | Não há evidência PKN ativa suficiente. |
| `legance/LOT_Tese/results/7-BUZ-29D-RJS10_PKN.dat` | saída | PKN no nome | `OUTPUT_ONLY` | Útil para auditoria futura, não suficiente para YAML moderno. |

## Status do BUZ-29D

```text
BUZ29D_NOT_PKN
```

Interpretação: há material BUZ-29D, mas nenhum candidato ficou pronto como
`BUZ29D_MODERN_REFINED_READY`. O bloqueio é metodológico: criar um YAML moderno
a partir de saídas ou fontes não-PKN violaria o contrato de não inventar dados.

## Gate de rota

| Rota | Status | Decisão |
|---|---|---|
| Additional well | blocked | BUZ-29D requer auditoria adicional antes de virar caso moderno. |
| Sensitivity matrix | ready | Usar BUZ-67D modern-refined com matriz pequena e rastreável. |
| Blocked/no action | no | Há uma rota segura para 10.28C. |

Decisão final:

```text
ADDITIONAL_WELL_BLOCKED_SENSITIVITY_SELECTED
SENSITIVITY_MATRIX_READY_FOR_10_28C
```

## Matriz de sensibilidade planejada

A matriz 10.28C deve usar o melhor caso BUZ-67D modern-refined já validado com
`constant_geometric`, `sink_timing` e série `sigmaTheta` refinada, sem alterar
os casos originais.

| Cenário | C_geom | sink_timing | sigmaTheta | Objetivo |
|---|---:|---|---|---|
| S0 baseline | `1.0x` | `next_step` | `refined_time_series` | Referência modern-refined. |
| S1 lower compliance | `0.75x` | `next_step` | `refined_time_series` | Avaliar pressão com menor compliance. |
| S2 higher compliance | `1.25x` | `next_step` | `refined_time_series` | Avaliar pressão com maior compliance. |
| S3 same_step | `1.0x` | `same_step` | `refined_time_series` | Isolar efeito do timing de sink. |

O eixo APBSalt1D permanece metadata-only e não deve ser tratado como variável
efetiva nesta matriz.

## Riscos

- BUZ-29D pode ser recuperável em fase futura, mas exige auditoria própria.
- Saídas PKN legadas sem fonte/parametrização completa não definem caso moderno.
- A matriz BUZ-67D é sensibilidade diagnóstica, não validação física.
- `legacy-equivalence` continua separada de `modern-refined`.

## Próxima fase

Executar a Fase 10.28C pela Rota B:

```text
PHASE10_28C_SENSITIVITY_MATRIX_EXECUTED
```

## Resultado da Fase 10.28C

A Fase 10.28C executou a rota B e criou:

```text
docs/35_phase10_28c_modern_refined_diagnostic.md
```

Classificação:

```text
PHASE10_28C_SENSITIVITY_MATRIX_RUN_OK
```

O gate da 10.28B permanece válido: nenhum caso adicional foi promovido a YAML
moderno, e a sensibilidade BUZ-67D foi tratada como diagnóstico
`modern-refined`.

## Atualização 10.29C

A Fase 10.29C aprofundou a auditoria BUZ-29D em:

```text
docs/38_buz29d_legacy_audit.md
```

Classificação:

```text
BUZ29D_LEGACY_AUDIT_RECORDED
BUZ29D_MODERN_YAML_NOT_READY
```

A decisão da 10.28B não mudou: BUZ-29D não deve ser promovido a YAML
`modern-refined` enquanto não houver fonte PKN ativo completo ou auditoria de
proveniência das saídas PKN existentes.
