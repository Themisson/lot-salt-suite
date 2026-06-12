# Fase 11.11K — especificacao de integracao do estado inicial pos-perfuracao

## Resumo executivo

A Fase 11.11K especifica o contrato `PostDrillingInitialState` que devera
alimentar o `SigmaThetaInitialStateGuard` em uma futura integracao real do
`limited_gate`.

Classificacao:

```text
POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED_BUT_SOURCE_MISSING
```

Como a 11.11J nao encontrou fonte runtime real de sigma-theta inicial/current,
esta fase nao autoriza implementacao C++.

## Contexto pos-11.11J

Resultado herdado:

```text
sigma_theta_initial_runtime_available = false
sigma_theta_current_runtime_available = false
wellbore_pressure_runtime_available = true
runtime_real_wiring_allowed_next = false
```

## Contrato PostDrillingInitialState

Campos requeridos:

```text
sigma_theta_initial_compression_positive_Pa
sigma_theta_current_compression_positive_Pa
source
state_time = POST_DRILLING_BEFORE_LOT
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
pressure_reference = WELLBORE_PRESSURE
is_total_stress = true
physically_validated = false
```

## Convencao de sinal

O contrato usa compressao positiva:

```text
COMPRESSION_POSITIVE
```

## Referencial

O referencial esperado e tensao total na parede do poco:

```text
WELLBORE_WALL_TOTAL_STRESS
```

## Fonte

Status atual:

```text
source_status = MISSING_RUNTIME_SIGMATHETA_SOURCE
```

## Integração com SigmaThetaInitialStateGuard

O estado inicial pós-perfuração deve representar a condição antes do início do
LOT, não um estado nulo criado no primeiro passo do ensaio.

Quando a fonte existir, o `SigmaThetaInitialStateGuard` devera receber esse
contrato antes de qualquer avaliacao do criterio pressao x sigma-theta.

## Bloqueios

```text
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

## Proxima fase recomendada

```text
PHASE11_11L_DECIDE_LIMITED_GATE_REAL_SIGMATHETA_READINESS
```

A 11.11L deve decidir formalmente se o gate continua diagnostico ou se ha
evidencia suficiente para wiring real. Com o estado atual, a expectativa tecnica
e manter o gate diagnostico por falta de fonte sigma-theta real.

## Decisao 11.11L

A Fase 11.11L confirmou:

```text
LIMITED_GATE_REMAINS_DIAGNOSTIC_BLOCKED_BY_REAL_SOURCE
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

Portanto, a fase 11.11M deve registrar plano de fonte sigma-theta, sem
implementacao C++.
