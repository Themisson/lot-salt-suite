# Fase 11.11P — decisão de readiness do gate sigma_theta diagnostico

## Resumo executivo

A 11.11P decide a prontidão diagnóstica do `limited_gate` quando alimentado por
`sigma_theta_diagnostic_input`. A decisão consolida as evidências da 11.11N e da
11.11O: a fonte diagnóstica explícita existe, os casos controlados cobrem
`ReadyNotReached`, `Reached`, bloqueios e rejeições de flags físicas, e os
outputs físicos PKN permanecem isolados.

Status:

```text
PHASE11_11P_DIAGNOSTIC_SIGMATHETA_GATE_READINESS_DECIDED
DIAGNOSTIC_SIGMATHETA_GATE_READY
READY_FOR_DIAGNOSTIC_USE
NOT_READY_FOR_PHYSICAL_VALIDATION
NOT_READY_FOR_PHYSICAL_DISPATCH
REAL_SIGMATHETA_SOURCE_INTEGRATION_SPEC_REQUIRED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

A 11.11P decide apenas a prontidão diagnóstica do gate alimentado por
sigma_theta_diagnostic_input. Ela não habilita validação física, não habilita
dispatch físico e não declara equivalência com legado.

## Evidência usada

| Evidência | Status |
|---|---|
| Fonte `sigma_theta_diagnostic_input` implementada | `SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED` |
| Casos controlados validam `ReadyNotReached` e `Reached` | `SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID` |
| Gate pode ser alimentado diagnosticamente | `LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY` |
| Saída diagnóstica isolada | `DIAGNOSTIC_OUTPUT_ISOLATED` |
| Outputs PKN preservados | `PKN_BEHAVIOR_NOT_CHANGED` |
| Dispatch runtime físico | `RUNTIME_DISPATCH_NOT_ENABLED` |
| BUZ29-PENNY | `BUZ29_EXECUTION_BLOCKED` |
| PENNY_SHAPED runtime | `PENNY_SHAPED_RUNTIME_NOT_ENABLED` |

## Decisão

O gate está pronto para uso diagnóstico controlado:

```text
readiness_status = DIAGNOSTIC_SIGMATHETA_GATE_READY
ready_for_diagnostic_use = true
ready_for_real_source_integration_spec = true
```

Ele não está pronto para validação física nem para dispatch físico:

```text
ready_for_physical_validation = false
ready_for_physical_dispatch = false
runtime_dispatch_enabled = false
```

## Interpretação do estado Reached

O estado Reached continua significando elegibilidade diagnóstica do gate, não
execução física de fratura.

Isso vale tanto para PKN quanto para PENNY_SHAPED. `PENNY_SHAPED` permanece uma
rota diagnóstica sem runtime físico.

## Limites

- Não há validação física de BUZ29.
- Não há execução de BUZ29-PENNY.
- Não há equivalência com LOT_Tese.
- Não há fonte física real de sigma-theta integrada.
- `diagnostic_fracture_gate.json` continua isolado de `result.json` e
  `timeseries.csv`.

## Próxima fase recomendada

```text
PHASE11_11Q_SPECIFY_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH
```

Essa próxima fase deve especificar como uma fonte real de sigma-theta poderia ser
integrada sem confundir o estado diagnóstico atual com validação física.
