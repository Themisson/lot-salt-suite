# Especificacao do wiring runtime do fracture gate (Fase 11.10T)

## Resumo executivo

A Fase 11.10T especifica o encadeamento futuro do `fracture_initiation_gate`
com os guards ja disponiveis, mas nao implementa runtime wiring, nao executa
dispatch fisico e nao executa BUZ29-PENNY.

A 11.10T nao implementa runtime wiring nem executa dispatch fisico. Ela apenas
especifica a sequencia futura que devera encadear `FractureModelSelector`,
`SigmaThetaInitialStateGuard` e
`PressureSigmaThetaFractureCriterionGuard` antes de qualquer dispatch para PKN
ou PENNY_SHAPED.

## Pre-condicao

A especificacao parte do estado pos-11.10S:

```text
FractureModelSelector: implementado como helper isolado
SigmaThetaInitialStateGuard: implementado como helper isolado
PressureSigmaThetaFractureCriterionGuard: implementado como helper isolado
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
```

Esses componentes existem, mas ainda nao estao conectados ao runtime.

## Componentes auditados

| Componente | Status atual | Papel no wiring futuro |
|---|---|---|
| `FractureModelSelector` | helper isolado | resolver `PKN` ou `PENNY_SHAPED` antes do gate |
| `SigmaThetaInitialStateGuard` | helper isolado | bloquear gate sem estado inicial de sigma-theta coerente |
| `PressureSigmaThetaFractureCriterionGuard` | helper isolado | avaliar criterio apenas apos o guard inicial passar |
| `PknModel` | rota runtime default | permanecer retrocompativel |
| `PennyShapedDiagnosticAdapter` | diagnostico | permanecer bloqueado para execucao fisica |
| `PennyShapedDiagnosticWriter` | diagnostico | escrever resultados opt-in quando houver rota autorizada |

## Sequencia runtime futura

```text
CaseData/parser defaults
-> FractureModelSelector
-> coleta de campos de pressao e sigma-theta
-> SigmaThetaInitialStateGuard
-> PressureSigmaThetaFractureCriterionGuard
-> fracture_initiation_gate_status
-> fracture_dispatch_status
-> dispatch PKN existente ou PENNY_SHAPED diagnostico futuro
```

O dispatch so pode ocorrer se todos os guards anteriores estiverem prontos e se
a fase futura autorizar explicitamente a rota.

## Estados do fracture gate

Estados minimos especificados:

```text
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION
FRACTURE_GATE_READY_NOT_REACHED
FRACTURE_GATE_REACHED
FRACTURE_DISPATCH_NOT_ALLOWED
FRACTURE_DISPATCH_NOT_EXECUTED
FRACTURE_DISPATCH_PKN_ELIGIBLE
FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE
```

## Campos minimos

O wiring futuro deve propagar pelo menos:

```text
selected_fracture_model
fracture_model_selection_source
wellbore_pressure_Pa
pressure_semantics
sigma_theta_initial_compression_positive_Pa
sigma_theta_current_compression_positive_Pa
sigma_theta_source
sigma_theta_state_time
sigma_theta_reference_frame
sigma_theta_sign_convention
tensile_strength_Pa
sigma_theta_guard_status
pressure_sigmatheta_criterion_status
fracture_initiation_gate_status
fracture_dispatch_status
fracture_initiated
fracture_margin_Pa
blocking_reasons
```

## Regras de bloqueio

- `FractureModelSelector` deve resolver o modelo antes de qualquer dispatch.
- `SigmaThetaInitialStateGuard` deve passar antes do criterio pressao x
  sigma-theta.
- `PressureSigmaThetaFractureCriterionGuard` deve passar antes do dispatch.
- Semantica de pressao desconhecida bloqueia o criterio.
- Referencial de `sigma_theta` desconhecido bloqueia o criterio.
- Convencao de sinal desconhecida ou nao compression-positive bloqueia o
  criterio.
- `PENNY_SHAPED` permanece diagnostico.
- BUZ29-PENNY permanece bloqueado.
- O default PKN deve preservar comportamento existente.
- O runtime wiring permanece bloqueado ate testes futuros provarem ausencia de
  regressao PKN.

## Status PKN

`PKN` permanece o default retrocompativel. A especificacao 11.10T nao altera
`PknModel`, `PknRunner`, parser, schema, CLI, casos ou resultados historicos.

```text
PKN_STATUS = DEFAULT_RETROCOMPATIBLE_NO_BEHAVIOR_CHANGE
```

## Status PENNY_SHAPED

`PENNY_SHAPED` permanece diagnostico, nao fisicamente validado e nao
equivalente ao legado. BUZ29-PENNY permanece bloqueado.

```text
PENNY_SHAPED_STATUS = DIAGNOSTIC_ONLY_NOT_PHYSICALLY_VALIDATED_NOT_LEGACY_EQUIVALENT
```

## O que nao foi implementado

A fase nao:

- altera C++;
- altera parser/schema;
- altera runtime;
- altera `PknModel`;
- altera `volumetric_balance`;
- altera `pkn_direct`;
- executa BUZ29-PENNY;
- declara validacao fisica;
- declara equivalencia com o legado.

## Proxima fase recomendada

```text
PHASE11_10U_SPECIFY_RUNTIME_WIRING_TEST_FIXTURES
```

A proxima fase deve especificar fixtures e testes de integracao antes de
qualquer wiring runtime real.

## Status registrado

```text
PHASE11_10T_FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
FRACTURE_MODEL_SELECTOR_REQUIRED
SIGMATHETA_INITIAL_STATE_GUARD_REQUIRED
PRESSURE_SIGMATHETA_CRITERION_GUARD_REQUIRED
RUNTIME_WIRING_NOT_IMPLEMENTED
DISPATCH_REMAINS_BLOCKED
```

## Atualizacao 11.10U — fixtures do contrato

A fase seguinte criou fixtures versionadas em:

```text
tests/fixtures/comparison/phase11_10u/
```

Elas cobrem sete cenarios minimos do futuro wiring, incluindo default PKN,
PKN explicito, `PENNY_SHAPED` diagnostico e bloqueios por guards. O status
registrado e:

```text
FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID
RUNTIME_WIRING_NOT_IMPLEMENTED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```
