# Implementacao do FractureGateRuntimeWiring (Fase 11.10W)

## Resumo executivo

A 11.10W implementa apenas o componente isolado
`FractureGateRuntimeWiring`. Ele retorna elegibilidade de dispatch, mas não
chama PknModel, PknRunner, PennyShapedDiagnosticAdapter ou qualquer runtime
físico.

PENNY_SHAPED permanece diagnóstico. BUZ29-PENNY não é executado nesta fase.

## Contexto pos-11.10V

A Fase 11.10V especificou a composicao futura:

```text
FractureModelSelector
-> SigmaThetaInitialStateGuard
-> PressureSigmaThetaFractureCriterionGuard
-> dispatch status
```

A 11.10W materializa essa composicao como helper C++ isolado e testavel, sem
conectar o helper ao parser, schema, CLI ou runtime `lot-pkn`.

## Componente implementado

Arquivos:

```text
include/lot/FractureGateRuntimeWiring.hpp
src/lot/FractureGateRuntimeWiring.cpp
tests/cpp/test_fracture_gate_runtime_wiring.cpp
```

O componente chama:

1. `select_fracture_model(...)`;
2. `validate_sigma_theta_initial_state(...)`;
3. `evaluate_pressure_sigma_theta_fracture_criterion(...)`.

Ele nao chama:

```text
PknModel
PknRunner
PennyShapedDiagnosticAdapter
PennyShapedDiagnosticWriter
```

## API C++

```cpp
namespace lss::lot {

enum class FractureGateStatus {
  NotEvaluated,
  BlockedSigmaThetaInitialState,
  BlockedPressureSigmaThetaCriterion,
  ReadyNotReached,
  Reached,
};

enum class FractureDispatchStatus {
  NotAllowed,
  NotExecuted,
  PknEligible,
  PennyDiagnosticEligible,
};

struct FractureGateRuntimeInput {
  FractureModelSelectionInput model_selection;
  SigmaThetaInitialStateInput sigma_theta_initial_state;
  PressureSigmaThetaCriterionInput pressure_sigma_theta_criterion;
};

struct FractureGateRuntimeResult {
  FractureGateStatus gate_status;
  FractureDispatchStatus dispatch_status;
  std::string selected_fracture_model;
  bool fracture_initiated;
  double fracture_margin_Pa;
  std::vector<std::string> blocking_reasons;
};

FractureGateRuntimeResult evaluate_fracture_gate_runtime(
    const FractureGateRuntimeInput& input);

}  // namespace lss::lot
```

## Sequencia dos guards

O helper executa o selector primeiro. Se o selector rejeitar o modelo, o gate
nao e avaliado:

```text
FRACTURE_GATE_NOT_EVALUATED
FRACTURE_DISPATCH_NOT_ALLOWED
```

Se o selector aceitar o modelo, o helper avalia o estado inicial sigma-theta.
Falha nesse guard produz:

```text
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
FRACTURE_DISPATCH_NOT_ALLOWED
```

Somente depois disso o helper avalia o criterio pressao x sigma-theta. Falha
nesse criterio produz:

```text
FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION
FRACTURE_DISPATCH_NOT_ALLOWED
```

## Estados de gate

```text
FRACTURE_GATE_NOT_EVALUATED
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION
FRACTURE_GATE_READY_NOT_REACHED
FRACTURE_GATE_REACHED
```

## Estados de dispatch

```text
FRACTURE_DISPATCH_NOT_ALLOWED
FRACTURE_DISPATCH_NOT_EXECUTED
FRACTURE_DISPATCH_PKN_ELIGIBLE
FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE
```

`PknEligible` significa apenas elegibilidade. Nao chama `PknModel`.
`PennyDiagnosticEligible` significa apenas elegibilidade diagnostica. Nao chama
`PennyShapedDiagnosticAdapter`.

## Cobertura dos 7 cenarios

| Cenario 11.10U | Status coberto |
|---|---|
| `missing_model_defaults_pkn_not_reached` | `FRACTURE_GATE_READY_NOT_REACHED` + `FRACTURE_DISPATCH_NOT_EXECUTED` |
| `explicit_pkn_initiated_dispatch_eligible` | `FRACTURE_GATE_REACHED` + `FRACTURE_DISPATCH_PKN_ELIGIBLE` |
| `explicit_penny_initiated_diagnostic_eligible` | `FRACTURE_GATE_REACHED` + `FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` |
| `sigmatheta_guard_blocks_dispatch` | `FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE` + `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `pressure_sigmatheta_criterion_blocks_dispatch` | `FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION` + `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `unsupported_kgd_model_blocked` | `FRACTURE_GATE_NOT_EVALUATED` + `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `explicit_empty_model_blocked` | `FRACTURE_GATE_NOT_EVALUATED` + `FRACTURE_DISPATCH_NOT_ALLOWED` |

## O que nao foi executado

A fase nao executa:

- dispatch fisico;
- BUZ29-PENNY;
- validacao fisica BUZ29;
- equivalencia com legado;
- parser/schema/CLI;
- alteracao de comportamento `lot-pkn`.

## Status registrado

```text
PHASE11_10W_FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
RUNTIME_EXECUTION_NOT_ENABLED
PKN_MODEL_NOT_CALLED
PENNY_ADAPTER_NOT_CALLED
BUZ29_EXECUTION_BLOCKED
```

## Proxima fase recomendada

```text
PHASE11_10X_SPECIFY_RUNTIME_INTEGRATION_GATE
```

Essa fase deve decidir se, quando e onde esse wiring pode ser conectado ao
runtime real.
