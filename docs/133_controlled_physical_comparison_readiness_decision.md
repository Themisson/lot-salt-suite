# Controlled Physical Comparison Readiness Decision

## Resumo executivo

A fase `PHASE_DECIDE_CONTROLLED_PHYSICAL_COMPARISON_READINESS` decide se a
source `AXISYMMETRIC_ELASTIC_WELLBORE_STATE` pode avançar da referência
analítica para a preparação de um gate BUZ/Legacy.

Decisão:

```text
readiness_status = READY_FOR_BUZ_OR_LEGACY_COMPARISON_GATE
ready_for_buz_or_legacy_gate = true
ready_for_physical_validation = false
ready_for_physical_dispatch = false
legacy_equivalence_allowed = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## O que a decisão permite

A decisão permite apenas preparar um gate de comparação futura. Esse gate deve
definir casos, campos, tolerâncias e caveats antes de qualquer comparação com
BUZ ou legado.

## O que continua bloqueado

| Item | Status |
| --- | --- |
| Validação física | bloqueada |
| Equivalência com LOT_Tese | bloqueada |
| Dispatch físico | bloqueado |
| BUZ29-PENNY | bloqueado |
| Mudança de comportamento PKN | bloqueada |

## Base da decisão

A Fase 5 comparou a source axisimétrica com referência analítica controlada e
registrou:

```text
comparison_status = ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_VALID
within_tolerance = true
max_abs_error_Pa = 0.0
```

As regressões PKN obrigatórias continuam verdes, e nenhuma alteração em
`PknModel`, `PknRunner`, `legacy/`, `legance/` ou `external/saltcreep/` foi
necessária.

## Próxima fase

```text
PHASE_PREPARE_BUZ_OR_LEGACY_COMPARISON_GATE
```

## Primeiro passo executado após o gate

O primeiro passo pós-readiness foi a comparação controlada analítica:

```text
PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON
FIRST_CONTROLLED_REFERENCE_COMPARISON_VALID
ANALYTIC_AXISYMMETRIC_CONTROLLED_REFERENCE
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
BUZ29_PENNY_NOT_EXECUTED
RUNTIME_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

Essa execução mantém a decisão original: BUZ67D/PKN pode ser avaliado apenas
como próxima referência diagnóstica controlada, não como validação física.
