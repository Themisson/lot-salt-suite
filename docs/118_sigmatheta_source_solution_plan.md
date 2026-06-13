# Fase B — plano de solucao da fonte sigma_theta

## Resumo executivo

A Fase B transforma o diagnostico da causa raiz em plano de implementacao. A
rota escolhida e:

```text
SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE
```

O componente proposto e:

```text
PostDrillingSigmaThetaProvider
```

Esse provider deve centralizar a normalizacao dos valores
`sigma_theta_initial_compression_positive_Pa` e
`sigma_theta_current_compression_positive_Pa`, mantendo semantica explicita e
sem habilitar dispatch fisico.

## Contrato planejado

O provider deve produzir:

```text
state_time = POST_DRILLING_BEFORE_LOT
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
physically_validated = false
legacy_equivalent = false
```

Fontes permitidas:

| Fonte | Status |
|---|---|
| `ExplicitDiagnosticInput` | diagnostica |
| `SyntheticFixture` | diagnostica |
| `ElasticInitialWellboreState` | semi-fisica com caveat |
| `Unknown` | rejeitada |

## Regras de bloqueio

- Rejeitar valores nao finitos ou nao positivos.
- Rejeitar `physically_validated=true`.
- Rejeitar `legacy_equivalent=true`.
- Rejeitar fonte desconhecida.
- Nao habilitar dispatch fisico.
- Nao alterar comportamento fisico do PKN.

## Gate

```text
solution_plan_status = SIGMATHETA_SOURCE_SOLUTION_PLAN_READY
implementation_allowed_next = true
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

## Proxima fase

```text
MASTER_PHASE_C_IMPLEMENT_POST_DRILLING_SIGMATHETA_PROVIDER
```
