# Fixtures do wiring runtime do fracture gate (Fase 11.10U)

## Resumo executivo

A Fase 11.10U cria fixtures sinteticas e versionaveis para testar o contrato
do futuro wiring runtime do `fracture_initiation_gate`. Ela nao implementa o
runtime, nao altera C++, nao altera parser/schema e nao executa BUZ29-PENNY.

A 11.10U não implementa runtime wiring. Ela apenas materializa fixtures
sintéticas para validar o contrato do futuro fluxo FractureModelSelector →
SigmaThetaInitialStateGuard → PressureSigmaThetaFractureCriterionGuard →
dispatch.

As fixtures não representam execução BUZ29, validação física nem equivalência
com legado.

## Contexto pos-11.10T

A Fase 11.10T especificou o fluxo futuro:

```text
FractureModelSelector
-> SigmaThetaInitialStateGuard
-> PressureSigmaThetaFractureCriterionGuard
-> dispatch
```

e registrou:

```text
FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
RUNTIME_WIRING_NOT_IMPLEMENTED
DISPATCH_REMAINS_BLOCKED
```

## Objetivo das fixtures

As fixtures definem os cenarios minimos que uma fase futura de wiring devera
provar antes de conectar o gate ao runtime. Elas servem como contrato de teste,
nao como implementacao.

Arquivos:

```text
tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_scenarios.json
tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_metadata.json
```

## Cenarios cobertos

| ID | Objetivo | Dispatch esperado |
|---|---|---|
| `missing_model_defaults_pkn_not_reached` | campo ausente defaulta para PKN e gate nao e atingido | `FRACTURE_DISPATCH_NOT_EXECUTED` |
| `explicit_pkn_initiated_dispatch_eligible` | PKN explicito com criterio iniciado | `FRACTURE_DISPATCH_PKN_ELIGIBLE` |
| `explicit_penny_initiated_diagnostic_eligible` | PENNY_SHAPED explicito como diagnostico | `FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` |
| `sigmatheta_guard_blocks_dispatch` | guard inicial bloqueia | `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `pressure_sigmatheta_criterion_blocks_dispatch` | criterio pressao x sigma-theta bloqueia | `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `unsupported_kgd_model_blocked` | modelo KGD nao suportado | `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `explicit_empty_model_blocked` | valor vazio explicito bloqueado | `FRACTURE_DISPATCH_NOT_ALLOWED` |

## Metadata e caveats

O metadata registra:

```text
runtime_wiring_implemented = false
runtime_execution_allowed = false
buz29_execution_allowed = false
physically_validated = false
legacy_equivalent = false
```

Caveats obrigatorios:

```text
PKN_DEFAULT_RETROCOMPATIBLE
PENNY_SHAPED_DIAGNOSTIC_ONLY
SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH
PRESSURE_SIGMATHETA_CRITERION_REQUIRED_BEFORE_DISPATCH
BUZ29_EXECUTION_BLOCKED
```

## Regras de validacao

O validador:

```text
tools/validate_phase11_10u_fracture_gate_runtime_wiring_fixtures.py
```

confirma a presenca dos sete cenarios, valida os flags de bloqueio e garante
que `PENNY_SHAPED` continue sem validacao fisica e sem equivalencia com legado.

## O que ainda nao foi implementado

A fase nao:

- implementa runtime wiring;
- altera C++;
- altera parser/schema;
- altera `PknModel` ou `PknRunner`;
- altera `lot-pkn`;
- executa BUZ29-PENNY;
- declara validacao fisica;
- declara equivalencia com legado.

## Proxima fase recomendada

```text
PHASE11_10V_SPECIFY_RUNTIME_WIRING_IMPLEMENTATION_PLAN
```

Se o validador futuro indicar lacunas, a alternativa e:

```text
PHASE11_10V_COMPLETE_RUNTIME_WIRING_FIXTURES
```

## Status registrado

```text
PHASE11_10U_FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_DEFINED
FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID
RUNTIME_WIRING_NOT_IMPLEMENTED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```

## Fase 11.10V — plano de implementacao

A Fase 11.10V consome estas fixtures como contrato de teste para a futura
implementacao isolada de `FractureGateRuntimeWiring`.

Cada um dos sete cenarios acima deve virar um teste Catch2 futuro. A 11.10V
mantem:

```text
RUNTIME_EXECUTION_STILL_BLOCKED
BUZ29_EXECUTION_STILL_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

O plano de implementacao esta registrado em:

```text
docs/96_fracture_gate_runtime_wiring_implementation_plan.md
```

## Fase 11.10W — fixtures consumidas em C++

A Fase 11.10W cobre os sete cenarios sinteticos em testes Catch2 do helper
isolado `FractureGateRuntimeWiring`.

O resultado continua sem execucao fisica:

```text
RUNTIME_EXECUTION_NOT_ENABLED
PKN_MODEL_NOT_CALLED
PENNY_ADAPTER_NOT_CALLED
BUZ29_EXECUTION_BLOCKED
```

## Fase 11.10X — uso futuro das fixtures no gate de integracao

A Fase 11.10X mantem as fixtures da 11.10U como cobertura obrigatoria para
qualquer integracao futura. A opcao selecionada, `DIAGNOSTIC_PRE_RUNNER_OPT_IN`,
nao altera os cenarios: eles continuam contrato de status, nao execucao fisica.
