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
