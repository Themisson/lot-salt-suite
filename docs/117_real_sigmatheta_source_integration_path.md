# Fase 11.11Q — caminho de integração da fonte real de sigma_theta

## Resumo executivo

A 11.11Q especifica o caminho técnico para evoluir de
`sigma_theta_diagnostic_input` para uma fonte real de `sigma_theta` capaz de
alimentar o `limited_gate` no futuro. A fase é exclusivamente de especificação:
não implementa provider real, não altera parser/schema/runtime e não habilita
dispatch físico.

Status:

```text
PHASE11_11Q_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED
REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED
PRIMARY_REAL_SOURCE_ELASTIC_INITIAL_WELLBORE_STATE
POST_DRILLING_SIGMATHETA_PROVIDER_REQUIRED
IMPLEMENTATION_NOT_ALLOWED_NEXT
RUNTIME_DISPATCH_NOT_ALLOWED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

A 11.11Q especifica apenas o caminho de integração da fonte real de
sigma_theta. A fase posterior implementou a primeira fonte elastica inicial
semi-fisica, ainda opt-in e diagnostica; isso nao habilita dispatch físico e
nao valida BUZ29-PENNY.

## Contexto pós-11.11P

A 11.11P decidiu que o gate alimentado por `sigma_theta_diagnostic_input` está
pronto para uso diagnóstico:

```text
DIAGNOSTIC_SIGMATHETA_GATE_READY
ready_for_diagnostic_use = true
ready_for_physical_validation = false
ready_for_physical_dispatch = false
```

Essa prontidão permite planejar a fonte real, mas não autoriza execução física.

## Estado atual do diagnostic sigma_theta gate

O fluxo moderno já possui:

```text
FractureModelSelector
SigmaThetaInitialStateGuard
PressureSigmaThetaFractureCriterionGuard
FractureGateRuntimeWiring
FractureGateDiagnosticPreRunner
limited_gate
sigma_theta_diagnostic_input
```

O caminho diagnóstico está testado e isolado. O runtime real ainda não possui
`sigma_theta_initial` e `sigma_theta_current` com semântica física suficiente.

## Fontes reais candidatas

| Fonte | Classificação | Uso recomendado |
|---|---|---|
| `ELASTIC_INITIAL_WELLBORE_STATE` | fonte real primária | primeira fonte real a especificar e implementar futuramente |
| `APB_SALT_COUPLED_STATE` | fonte real secundária | rota acoplada futura, após contrato APB/sal |
| `SALT_CREEP_PRE_LOT_STATE` | fonte real futura | depende de estado de sal pré-LOT e mapeamento de parede |
| `POST_DRILLING_GEOMECHANICAL_STATE_PROVIDER` | categoria arquitetural | pode agrupar fontes reais pós-perfuração |
| `LEGACY_DIAGNOSTIC_TRACE` | não é validação física | apenas referência auditada/diagnóstica |
| `EXPLICIT_DIAGNOSTIC_INPUT` | diagnóstico | já disponível para fixtures e testes controlados |
| `SYNTHETIC_FIXTURE` | diagnóstico | já disponível para fixtures sintéticas |

Fonte primária recomendada:

```text
primary_real_source = ELASTIC_INITIAL_WELLBORE_STATE
```

Status posterior:

```text
ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED
```

A fonte implementada permanece semi-fisica, nao fisicamente validada e nao
equivalente ao legado.

Validacao analitica posterior:

```text
ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID
```

Essa validacao confirma a formula especificada e a convencao de sinal em casos
controlados, sem declarar equivalencia fisica plena.

Decisao de readiness posterior:

```text
ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE
READY_FOR_KIRSCH_OR_AXISYMMETRIC_UPGRADE_SPEC
PHYSICALLY_VALIDATED_FALSE
LEGACY_EQUIVALENT_FALSE
RUNTIME_DISPATCH_NOT_ENABLED
```

A fonte elastica inicial pode ser usada em diagnostico semi-fisico, mas ainda
nao deve ser tratada como validacao fisica plena nem como dispatch fisico.

Fonte secundária:

```text
secondary_real_source = APB_SALT_COUPLED_STATE
```

Fonte futura:

```text
future_real_source = SALT_CREEP_PRE_LOT_STATE
```

EXPLICIT_DIAGNOSTIC_INPUT e SYNTHETIC_FIXTURE permanecem fontes diagnósticas,
não fontes de validação física.

## Tempo, sinal e referencial

O estado inicial de sigma_theta deve representar a condição pós-perfuração antes
do início do LOT. O t = 0 do LOT não deve ser tratado como estado nulo de
perfuração.

O provider futuro deve produzir:

```text
state_time = POST_DRILLING_BEFORE_LOT
reference_frame = WELLBORE_WALL_TOTAL_STRESS
sign_convention = COMPRESSION_POSITIVE
```

## Contrato do PostDrillingSigmaThetaProvider

Componente futuro especificado:

```text
PostDrillingSigmaThetaProvider
```

API conceitual:

```cpp
namespace lot {

enum class SigmaThetaProviderSource {
    ElasticInitialWellboreState,
    ApbSaltCoupledState,
    SaltCreepPreLotState,
    ExplicitDiagnosticInput,
    SyntheticFixture,
    Unknown
};

struct PostDrillingSigmaThetaProviderInput {
    // geometry, material, pressure, depth, layer, case context
};

struct PostDrillingSigmaThetaProviderResult {
    bool available;
    double sigma_theta_initial_compression_positive_Pa;
    double sigma_theta_current_compression_positive_Pa;
    std::string source;
    std::string state_time;
    std::string sign_convention;
    std::string reference_frame;
    bool physically_validated;
    bool legacy_equivalent;
    std::vector<std::string> caveats;
};

}
```

Regras obrigatórias:

```text
valores finitos
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
state_time = POST_DRILLING_BEFORE_LOT
physically_validated = false até validação futura específica
legacy_equivalent = false até comparação futura específica
provider real não altera PKN
```

## Caminho de integração futuro

Sequência recomendada:

| Fase | Objetivo | Gate |
|---|---|---|
| 11.11R | criar fixtures do `PostDrillingSigmaThetaProvider` | contrato antes de C++ |
| 11.11S | implementar provider sintético/diagnóstico isolado | sem fonte física |
| 11.11T | especificar provider elástico inicial real | fórmula/semântica |
| 11.11U | implementar provider elástico inicial real | C++ isolado |
| 11.11V | validar provider elástico inicial em casos controlados | sem dispatch físico |
| 11.11W | decidir readiness para alimentar `limited_gate` com provider real | gate formal |

A 11.11Q não deve pular diretamente para implementação física.

## O que permanece bloqueado

```text
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

Permanecem bloqueados:

- dispatch físico;
- BUZ29-PENNY;
- validação física;
- equivalência com legado;
- promoção de `PENNY_SHAPED` para runtime físico;
- alteração de comportamento físico PKN.

## Próxima fase recomendada

```text
PHASE11_11R_CREATE_POST_DRILLING_SIGMATHETA_PROVIDER_FIXTURES
```
