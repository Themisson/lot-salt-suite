# Gate de integracao runtime do FractureGateRuntimeWiring (Fase 11.10X)

## Resumo executivo

A 11.10X nao integra FractureGateRuntimeWiring ao runtime. Ela apenas
especifica o gate de integracao futura.

A decisao da fase e selecionar uma rota futura de integracao diagnostica
pre-runner, opt-in, sem dispatch fisico e sem mudanca do comportamento historico
de PKN.

```text
selected_integration_option = DIAGNOSTIC_PRE_RUNNER_OPT_IN
implementation_allowed_next = true
runtime_physical_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

## Contexto pos-11.10W

A Fase 11.10W implementou `FractureGateRuntimeWiring` como helper C++ isolado.
Ele compoe:

```text
FractureModelSelector
-> SigmaThetaInitialStateGuard
-> PressureSigmaThetaFractureCriterionGuard
-> dispatch status
```

O helper retorna elegibilidade de dispatch, mas nao chama `PknModel`,
`PknRunner`, `PennyShapedDiagnosticAdapter` ou runtime fisico.

## Estado do runtime atual

O caminho atual `lot-pkn` e:

```text
apps/lot-sim.cpp::run_case
-> lss::io::parse_yaml(case_arg)
-> lss::lot::run_pkn_case(data)
-> PknModel{}.simulate(run.input)
-> lss::io::write_pkn_result(...)
```

O parser ja armazena `CaseData.lot.fracture_model` e metadados associados:

```text
fracture_model
fracture_model_selection_source
fracture_model_route
fracture_model_diagnostic_only
fracture_model_runtime_dispatch_enabled
fracture_model_requires_fracture_initiation_gate
```

Hoje `FractureGateRuntimeWiring` nao e chamado por `lot-sim`, `PknRunner` ou
`PknModel`.

## Opcoes de integracao avaliadas

| Opcao | Descricao | Risco | Decisao |
|---|---|---|---|
| A | Integracao diagnostica pos-parser, pre-runner | Baixo | Selecionada |
| B | Integracao dentro do `PknRunner` | Alto | Nao recomendada agora |
| C | Ferramenta/CLI diagnostica separada | Baixo | Fallback seguro |
| D | Integracao completa com dispatch fisico | Bloqueada | Fora de escopo |

## Opcao selecionada

A opcao selecionada e:

```text
DIAGNOSTIC_PRE_RUNNER_OPT_IN
```

Essa opcao permitiria, em fase futura, chamar `FractureGateRuntimeWiring` apos
parse/validacao do caso e antes de `run_pkn_case(data)`, somente para gerar um
diagnostico de gate.

O resultado PKN fisico nao deve ser alterado. O diagnostico deve ser escrito em
saida separada dos arquivos fisicos `result.json` e `timeseries.csv`.

## Gates de seguranca

Qualquer integracao futura deve ser opt-in, diagnostica, sem dispatch fisico e
sem alteracao do comportamento historico de PKN.

Gates obrigatorios:

1. feature flag explicita habilitada;
2. modo diagnostico;
3. PKN continua default;
4. `PENNY_SHAPED` continua `diagnostic_only`;
5. dispatch fisico runtime continua desabilitado;
6. BUZ29-PENNY continua bloqueado;
7. regressoes PKN passam;
8. outputs diagnosticos ficam separados dos outputs fisicos.

## Feature flags futuras

Formato conceitual, ainda nao implementado:

```yaml
lot:
  fracture:
    fracture_model: PKN
    fracture_gate_diagnostics:
      enabled: true
      mode: pre_runner
      dispatch_runtime_enabled: false
```

ou:

```yaml
lot:
  fracture:
    fracture_model: PENNY_SHAPED
    fracture_gate_diagnostics:
      enabled: true
      mode: diagnostic_only
      dispatch_runtime_enabled: false
```

Essa fase nao altera schema, parser ou YAMLs.

## Saidas diagnosticas

A fase futura deve produzir saida separada, por exemplo:

```text
fracture_gate_diagnostics.json
```

Campos recomendados:

```text
fracture_gate_status
fracture_dispatch_status
selected_fracture_model
fracture_initiated
fracture_margin_Pa
blocking_reasons
runtime_physical_dispatch_enabled = false
```

## Riscos de regressao PKN

Risco baixo se a integracao for pre-runner e opt-in. Risco alto se o helper for
chamado dentro de `PknRunner` ou `PknModel`, pois isso poderia alterar a
cronologia de fratura, a pressao, o sink timing ou a semantica dos criterios
existentes.

Por isso, a 11.10X proibe integracao dentro do `PknRunner` nesta etapa.

## O que permanece bloqueado

BUZ29-PENNY permanece bloqueado e PENNY_SHAPED permanece diagnostic_only.

Tambem permanecem bloqueados:

- dispatch fisico;
- alteracao de `lot-pkn`;
- chamada a `PknModel` via wiring;
- chamada a `PennyShapedDiagnosticAdapter` via wiring;
- validacao fisica BUZ29;
- declaracao de equivalencia com legado.

## Status registrado

```text
PHASE11_10X_RUNTIME_INTEGRATION_GATE_SPECIFIED
RUNTIME_INTEGRATION_GATE_SPECIFIED
DIAGNOSTIC_PRE_RUNNER_OPT_IN_SELECTED
RUNTIME_PHYSICAL_DISPATCH_NOT_ALLOWED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

## Proxima fase recomendada

```text
PHASE11_10Y_IMPLEMENT_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE
```

Essa proxima fase deve implementar, se autorizada, somente a integracao
diagnostica opt-in pre-runner, com outputs isolados e regressoes PKN passando.

## Atualizacao 11.10Y — gate pre-runner implementado

A Fase 11.10Y implementa a opcao selecionada pela 11.10X:

```text
DIAGNOSTIC_PRE_RUNNER_OPT_IN_IMPLEMENTED
```

O diagnostico roda somente quando `lot.fracture.fracture_gate_diagnostics`
declara `enabled: true`. O arquivo produzido e isolado:

```text
diagnostic_fracture_gate.json
```

A fase nao habilita dispatch fisico, nao chama `PknModel`, nao chama
`PennyShapedDiagnosticAdapter` e nao executa BUZ29-PENNY. Com sigma_theta
inicial ausente, o bloqueio esperado e
`FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE`.
