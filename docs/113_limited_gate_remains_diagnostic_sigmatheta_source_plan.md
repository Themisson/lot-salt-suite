# Fase 11.11M — plano da fonte sigma-theta para limited_gate diagnostico

## Resumo executivo

A Fase 11.11M registra a decisao conservadora apos a 11.11L:

```text
LIMITED_GATE_REMAINS_DIAGNOSTIC_SIGMATHETA_SOURCE_PLAN_RECORDED
```

Nenhuma implementacao C++ foi realizada nesta fase. O `limited_gate` permanece
diagnostico porque a fonte runtime real de sigma-theta inicial/current ainda nao
existe com semantica, sinal e referencial resolvidos.

## Status operacional

```text
implementation_performed = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
```

## Bloqueios preservados

```text
MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE
MISSING_RUNTIME_SIGMATHETA_CURRENT_SOURCE
PRESSURE_SEMANTICS_NOT_RESOLVED_FOR_REAL_GATE
SIGMATHETA_SIGN_CONVENTION_NOT_RUNTIME_RESOLVED
SIGMATHETA_REFERENCE_FRAME_NOT_RUNTIME_RESOLVED
```

## Plano para completar a fonte sigma-theta

| Etapa | Status | Saida esperada |
|---|---|---|
| Definir fonte runtime pos-perfuracao de sigma-theta | required | `post_drilling_sigma_theta_initial_state` |
| Resolver semantica de pressao | required | `wellbore_pressure_reference_for_gate` |
| Resolver convencao de sinal | required | `compression_positive_sigma_theta_contract` |
| Resolver referencial | required | `wellbore_wall_total_stress_or_documented_alternative` |
| Criar fixtures controladas de runtime | future | fixtures que nao alteram a fisica PKN |

## Guardas obrigatorios para a proxima fase

```text
PKN_DEFAULT_RETROCOMPATIBLE
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
RESULT_JSON_PHYSICAL_OUTPUT_UNCHANGED
TIMESERIES_CSV_PHYSICAL_OUTPUT_UNCHANGED
```

## Proxima fase recomendada

```text
PHASE11_11N_IMPLEMENT_OR_CONNECT_SIGMATHETA_SOURCE
```

A proxima fase deve implementar ou conectar uma fonte real de sigma-theta apenas
se conseguir preservar os guardas acima. Caso contrario, o `limited_gate` deve
continuar diagnostico.

## Implementação diagnóstica da 11.11N

A Fase 11.11N implementou a alternativa segura prevista por este plano: uma
fonte explicita, diagnostica e opt-in de sigma-theta. Ela permite alimentar o
`limited_gate` para exercitar guards e dispatch status diagnostico, mas ainda
nao e a fonte fisica definitiva.

```text
SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```
