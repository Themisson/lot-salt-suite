# Plano de implementacao do wiring runtime do fracture gate (Fase 11.10V)

## Resumo executivo

A 11.10V nao implementa runtime wiring. Ela apenas especifica o plano de
implementacao para uma fase futura.

O objetivo e transformar o contrato ja criado nas Fases 11.10T e 11.10U em um
plano de implementacao C++ rastreavel. A proxima fase pode criar um helper
isolado para compor:

```text
FractureModelSelector
-> SigmaThetaInitialStateGuard
-> PressureSigmaThetaFractureCriterionGuard
-> dispatch status
```

Essa composicao deve produzir status de gate e de dispatch, mas ainda nao deve
executar `PknModel`, `PennyShapedDiagnosticAdapter` ou BUZ29-PENNY.

## Contexto pos-11.10U

A 11.10U materializou sete fixtures sinteticas para o futuro wiring runtime do
`fracture_initiation_gate`:

```text
missing_model_defaults_pkn_not_reached
explicit_pkn_initiated_dispatch_eligible
explicit_penny_initiated_diagnostic_eligible
sigmatheta_guard_blocks_dispatch
pressure_sigmatheta_criterion_blocks_dispatch
unsupported_kgd_model_blocked
explicit_empty_model_blocked
```

Essas fixtures sao contrato de teste, nao execucao fisica. Elas registram:

```text
runtime_wiring_implemented = false
runtime_execution_allowed = false
buz29_execution_allowed = false
physically_validated = false
legacy_equivalent = false
```

## Componentes disponiveis

| Componente | Status | Papel futuro |
|---|---|---|
| `FractureModelSelector` | helper C++ isolado | Resolver `PKN` ou `PENNY_SHAPED` e bloquear modelos nao suportados. |
| `SigmaThetaInitialStateGuard` | helper C++ isolado | Bloquear gate sem estado inicial sigma-theta coerente. |
| `PressureSigmaThetaFractureCriterionGuard` | helper C++ isolado | Avaliar criterio pressao x sigma-theta depois do guard inicial. |
| `PennyShapedDiagnosticAdapter` | diagnostico | Nao deve ser chamado pela primeira implementacao de wiring. |
| `PennyShapedDiagnosticWriter` | diagnostico | Continua disponivel apenas para saida diagnostica opt-in. |

## Fixtures disponiveis

As fixtures versionadas ficam em:

```text
tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_scenarios.json
tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_metadata.json
```

Elas devem ser usadas como base para os testes C++ da proxima fase.

## Arquivos C++ futuros

A implementacao futura recomendada deve criar:

```text
include/lot/FractureGateRuntimeWiring.hpp
src/lot/FractureGateRuntimeWiring.cpp
tests/cpp/test_fracture_gate_runtime_wiring.cpp
```

O helper deve permanecer isolado. Ele nao deve alterar parser, schema, CLI,
`PknModel`, `PknRunner`, `volumetric_balance` ou `pkn_direct`.

## API proposta

API conceitual recomendada, usando o namespace do projeto:

```cpp
namespace lss::lot {

enum class FractureGateStatus {
  BlockedSigmaThetaInitialState,
  BlockedPressureSigmaThetaCriterion,
  ReadyNotReached,
  Reached
};

enum class FractureDispatchStatus {
  NotAllowed,
  NotExecuted,
  PknEligible,
  PennyDiagnosticEligible
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
  bool fracture_initiated = false;
  double fracture_margin_Pa = 0.0;
  std::vector<std::string> blocking_reasons;
};

[[nodiscard]] FractureGateRuntimeResult evaluate_fracture_gate_runtime(
    const FractureGateRuntimeInput& input);

}  // namespace lss::lot
```

A nomenclatura final pode seguir o estilo local do modulo `lot`, mas o contrato
deve preservar os estados acima.

## Regras de implementacao futura

A futura implementacao do wiring deve compor FractureModelSelector,
SigmaThetaInitialStateGuard e PressureSigmaThetaFractureCriterionGuard, mas nao
deve chamar PknModel nem PennyShapedAdapter sem gate posterior.

Regras obrigatorias:

1. Executar `FractureModelSelector` primeiro.
2. Se a selecao falhar, nao avaliar o gate.
3. Executar `SigmaThetaInitialStateGuard`.
4. Se o guard sigma-theta falhar, retornar
   `BlockedSigmaThetaInitialState` e `NotAllowed`.
5. Executar `PressureSigmaThetaFractureCriterionGuard`.
6. Se o criterio bloquear, retornar
   `BlockedPressureSigmaThetaCriterion` e `NotAllowed`.
7. Se o criterio estiver pronto, mas sem fratura, retornar
   `ReadyNotReached` e `NotExecuted`.
8. Se a fratura for atingida, retornar `Reached` e status de dispatch
   conforme o modelo selecionado.
9. `PKN` pode retornar `PknEligible`, mas a fase inicial nao deve alterar o
   comportamento atual de `lot-pkn`.
10. `PENNY_SHAPED` pode retornar `PennyDiagnosticEligible`, mas isso nao
    libera execucao BUZ29-PENNY.

PENNY_SHAPED permanece diagnostico e BUZ29-PENNY permanece bloqueado.

## Mapeamento fixture -> teste C++

| Fixture | Teste C++ futuro | Gate esperado | Dispatch esperado |
|---|---|---|---|
| `missing_model_defaults_pkn_not_reached` | default PKN sem fratura nao despacha | `FRACTURE_GATE_READY_NOT_REACHED` | `FRACTURE_DISPATCH_NOT_EXECUTED` |
| `explicit_pkn_initiated_dispatch_eligible` | PKN explicito com gate atingido fica elegivel | `FRACTURE_GATE_REACHED` | `FRACTURE_DISPATCH_PKN_ELIGIBLE` |
| `explicit_penny_initiated_diagnostic_eligible` | PENNY explicito com gate atingido fica diagnostico elegivel | `FRACTURE_GATE_REACHED` | `FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` |
| `sigmatheta_guard_blocks_dispatch` | guard inicial bloqueia dispatch | `FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE` | `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `pressure_sigmatheta_criterion_blocks_dispatch` | criterio pressao x sigma-theta bloqueia dispatch | `FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION` | `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `unsupported_kgd_model_blocked` | seletor bloqueia KGD antes do gate | `FRACTURE_GATE_NOT_EVALUATED` | `FRACTURE_DISPATCH_NOT_ALLOWED` |
| `explicit_empty_model_blocked` | seletor bloqueia valor vazio explicito antes do gate | `FRACTURE_GATE_NOT_EVALUATED` | `FRACTURE_DISPATCH_NOT_ALLOWED` |

## Restricoes

```text
RUNTIME_EXECUTION_STILL_BLOCKED
BUZ29_EXECUTION_STILL_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

A proxima fase pode implementar o helper isolado de wiring. Ela nao deve
conectar esse helper ao parser/schema/CLI nem ao runtime fisico sem novo gate.

## Proxima fase recomendada

```text
PHASE11_10W_IMPLEMENT_FRACTURE_GATE_RUNTIME_WIRING
```

Status da 11.10V:

```text
PHASE11_10V_RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_ALLOWED_NEXT
RUNTIME_EXECUTION_STILL_BLOCKED
BUZ29_EXECUTION_STILL_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

## Fase 11.10W — implementacao realizada

A Fase 11.10W implementa o helper isolado planejado neste documento:

```text
include/lot/FractureGateRuntimeWiring.hpp
src/lot/FractureGateRuntimeWiring.cpp
tests/cpp/test_fracture_gate_runtime_wiring.cpp
```

O status registrado passa a ser:

```text
PHASE11_10W_FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
RUNTIME_EXECUTION_NOT_ENABLED
PKN_MODEL_NOT_CALLED
PENNY_ADAPTER_NOT_CALLED
BUZ29_EXECUTION_BLOCKED
```

A implementacao retorna elegibilidade de dispatch, nao execucao fisica.
