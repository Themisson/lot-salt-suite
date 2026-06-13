# Fase F — decisao de readiness do sigma-theta provider

## Resumo executivo

A Fase F consolida as fases mestre A–E e decide que o
`PostDrillingSigmaThetaProvider` esta pronto para uso diagnostico runtime no
`limited_gate`, mas ainda nao esta pronto para dispatch fisico ou validacao
fisica.

Decisao:

```text
SIGMATHETA_PROVIDER_READY_FOR_DIAGNOSTIC_RUNTIME_USE
ready_for_diagnostic_runtime_use = true
ready_for_physical_dispatch = false
ready_for_physical_validation = false
ready_for_real_source_extension = true
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
```

## Evidencia consolidada

| Fase | Evidencia |
|---|---|
| Master A | causa raiz isolada como falta de fonte sigma-theta runtime |
| Master B | plano de solucao selecionou `PostDrillingSigmaThetaProvider` |
| Master C | provider C++ diagnostico implementado |
| Master D | provider conectado ao diagnostic pre-runner |
| Master E | fixtures controladas validaram ready/reached/rejeicoes |

## Limites

O provider permanece uma rota diagnostica. Ele nao habilita dispatch fisico,
nao executa BUZ29-PENNY, nao chama runtime fisico de PENNY_SHAPED e nao declara
equivalencia com legado.

`PknEligible` e `PennyDiagnosticEligible` continuam sendo estados de
elegibilidade diagnostica, nao execucao fisica.

## Proxima fase recomendada

```text
PHASE_IMPLEMENT_ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE
```

Essa proxima fase deve implementar uma fonte semi-fisica elastica inicial para
sigma-theta, ainda opt-in e sem habilitar dispatch fisico.

## Atualizacao pos-implementacao

A fonte `ELASTIC_INITIAL_WELLBORE_STATE` foi implementada como rota opt-in
diagnostica do `PostDrillingSigmaThetaProvider`. Ela calcula
`sigma_theta_current` por uma aproximacao elastica inicial simplificada e passa
a alimentar o `limited_gate` quando `sigma_theta_provider.enabled=true`.

O status da fase seguinte e:

```text
ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED
```

O resultado nao altera a decisao de readiness fisica: dispatch fisico,
BUZ29-PENNY e validacao fisica permanecem bloqueados.
