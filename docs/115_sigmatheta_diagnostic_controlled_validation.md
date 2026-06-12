# Fase 11.11O — validacao controlada da fonte diagnostica sigma_theta

## Resumo executivo

A 11.11O valida `sigma_theta_diagnostic_input` em fixtures controladas do
`limited_gate`. A fase confirma que o gate pode receber valores diagnosticos
explicitos de sigma-theta inicial e corrente e produzir estados esperados sem
habilitar dispatch fisico.

Status:

```text
PHASE11_11O_SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALIDATED
SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

A 11.11O valida apenas a fonte diagnóstica de sigma_theta em casos controlados.
Ela não valida fisicamente BUZ29, não habilita dispatch físico e não transforma
PENNY_SHAPED em runtime físico.

## Contexto pos-11.11N

A 11.11N adicionou o bloco opcional:

```yaml
lot:
  fracture:
    sigma_theta_diagnostic_input:
      enabled: true
      source: EXPLICIT_DIAGNOSTIC_INPUT
      sigma_theta_initial_compression_positive_Pa: 5000000.0
      sigma_theta_current_compression_positive_Pa: -2000000.0
      sign_convention: COMPRESSION_POSITIVE
      reference_frame: WELLBORE_WALL_TOTAL_STRESS
      state_time: POST_DRILLING_BEFORE_LOT
      physically_validated: false
      legacy_equivalent: false
```

A 11.11O cria fixtures especificas para validar os estados do gate e as
rejeicoes de flags fisicas indevidas.

## Casos controlados

| Fixture | Objetivo | Estado esperado |
|---|---|---|
| `controlled_pkn_ready_not_reached.yaml` | sigma-theta corrente compressivo | `FRACTURE_GATE_READY_NOT_REACHED` |
| `controlled_pkn_reached.yaml` | sigma-theta corrente trativo suficiente | `FRACTURE_GATE_REACHED`, `FRACTURE_DISPATCH_PKN_ELIGIBLE` |
| `controlled_penny_reached_diagnostic.yaml` | PENNY_SHAPED atingido | `FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` |
| `controlled_missing_sigmatheta_blocks.yaml` | fonte ausente | `FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE` |
| `controlled_invalid_physically_validated_true.yaml` | flag fisica indevida | rejeicao esperada |
| `controlled_invalid_legacy_equivalent_true.yaml` | equivalencia legado indevida | rejeicao esperada |

## Caso ReadyNotReached

O caso `controlled_pkn_ready_not_reached.yaml` usa:

```text
sigma_theta_current_compression_positive_Pa = 5000000.0
```

Como a tensao permanece compressiva, o gate fica pronto, mas nao atingido. O
resultado esperado e diagnostico e nao executa fratura fisica.

## Caso Reached PKN

O caso `controlled_pkn_reached.yaml` usa:

```text
sigma_theta_current_compression_positive_Pa = -2000000.0
```

Esse valor e trativo suficiente para a fixture controlada. O status esperado e
`FRACTURE_GATE_REACHED` e `FRACTURE_DISPATCH_PKN_ELIGIBLE`, mantendo
`runtime_dispatch_enabled = false`.

## Caso Reached PENNY_SHAPED diagnostico

O caso `controlled_penny_reached_diagnostic.yaml` confirma que
`PENNY_SHAPED` pode ficar elegivel diagnosticamente sem virar runtime fisico.
`physically_validated` e `legacy_equivalent` permanecem `false`.

## Rejeicoes esperadas

As fixtures invalidas confirmam que a fonte diagnostica nao pode declarar:

```text
physically_validated = true
legacy_equivalent = true
```

Essas flags continuam bloqueadas enquanto a fonte for diagnostica.

## Comparacao PKN

A comparacao fisica permanece definida por `result.json` e `timeseries.csv`.
Nesta fase, `physical_outputs_identical = true` e
`diagnostic_output_isolated = true` sao mantidos como requisitos de aceite.

## Saida diagnostica isolada

Quando opt-in, o diagnostico continua isolado em
`diagnostic_fracture_gate.json`. Essa saida nao altera `result.json` nem
`timeseries.csv`.

## Limites fisicos

O estado Reached indica elegibilidade diagnóstica do gate, não execução física
de fratura.

Nao ha validacao de BUZ29, nao ha equivalencia com legado e nao ha promocao de
`PENNY_SHAPED` para runtime.

## Proxima fase recomendada

```text
PHASE11_11P_DECIDE_DIAGNOSTIC_SIGMATHETA_GATE_READINESS
```

## Resultado da decisao 11.11P

A 11.11P confirmou que a validacao controlada da 11.11O e suficiente para uso
diagnostico do gate:

```text
DIAGNOSTIC_SIGMATHETA_GATE_READY
ready_for_diagnostic_use = true
ready_for_physical_validation = false
ready_for_physical_dispatch = false
```

O estado `Reached` continua significando elegibilidade diagnostica do gate, nao
execucao fisica de fratura.
