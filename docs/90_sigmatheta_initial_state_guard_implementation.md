# Fase 11.10P — implementacao do guard de estado inicial sigma-theta

## Resumo executivo

A Fase 11.10P implementa apenas o guard isolado de estado inicial
`sigma_theta`. Ela nao integra o guard ao runtime, nao altera o
`fracture_initiation_gate` e nao executa BUZ29-PENNY.

O guard existe para impedir que o `fracture_initiation_gate` seja avaliado com
`sigma_theta` nulo, nao inicializado, com referencial desconhecido ou
semanticamente incompativel com a pressao.

## Estado herdado da 11.10O

A Fase 11.10O especificou que a fonte preferencial futura para o estado inicial
e:

```text
ELASTIC_INITIAL_WELLBORE_STATE
```

Essa fonte representa o estado geomecanico pos-perfuracao e pre-LOT. A 11.10O
tambem manteve:

```text
dispatch_allowed_next = false
runtime_execution_allowed_next = false
buz29_execution_allowed_next = false
```

A 11.10P preserva esses bloqueios.

## API implementada

Arquivos:

```text
include/lot/SigmaThetaInitialStateGuard.hpp
src/lot/SigmaThetaInitialStateGuard.cpp
tests/cpp/test_sigma_theta_initial_state_guard.cpp
```

Entrada principal:

```text
SigmaThetaInitialStateInput
```

Campos essenciais:

```text
sigma_theta_initialized
sigma_theta_initial_state_valid
sigma_theta_initial_compression_positive_Pa
sigma_theta_source
sigma_theta_state_time
sigma_theta_reference_frame
sigma_theta_sign_convention
pressure_semantics
```

Saida principal:

```text
SigmaThetaInitialStateGuardResult
```

Campos:

```text
gate_ready
status
blocking_reasons
```

## Regras de bloqueio

O guard bloqueia o gate quando:

```text
FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA
FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA
FRACTURE_GATE_BLOCKED_UNKNOWN_SOURCE
FRACTURE_GATE_BLOCKED_WRONG_STATE_TIME
FRACTURE_GATE_BLOCKED_UNKNOWN_REFERENCE_FRAME
FRACTURE_GATE_BLOCKED_UNKNOWN_SIGN_CONVENTION
FRACTURE_GATE_BLOCKED_UNKNOWN_PRESSURE_SEMANTICS
FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH
```

O estado positivo e:

```text
SIGMATHETA_INITIAL_STATE_READY
```

Esse status significa apenas que o estado informado ao helper e internamente
coerente. Ele nao libera dispatch fisico.

## Compatibilidade pressao x sigma-theta

| Pressao | Referencial de sigma-theta | Status |
|---|---|---|
| `WellborePressureAbsolute` | `TotalStress` | Aceito |
| `WellborePressureAbsolute` | `EffectiveStress` | Aceito como contrato explicito |
| `PressureIncrement` | `IncrementalStress` | Aceito |
| `PressureIncrement` | `TotalStress` | Bloqueado |
| `NetPressure` | `EffectiveStress` | Aceito como rota diagnostica explicita |
| `NetPressure` | `TotalStress` | Bloqueado |
| `Unknown` | qualquer | Bloqueado |

## Convencao de sinal

O contrato implementado consome:

```text
sigma_theta_initial_compression_positive_Pa
```

Portanto, o valor deve chegar ao guard ja em convencao de compressao positiva.
Se uma fonte futura fornecer tensao com tracao positiva, a conversao de sinal
deve ocorrer antes do guard, com `source` e `reference_frame` rastreaveis.

## O que a 11.10P nao faz

A fase nao:

- altera parser ou schema;
- altera `PknModel`;
- altera `PknRunner`;
- altera `volumetric_balance`;
- altera `pkn_direct`;
- conecta o guard ao runtime;
- executa BUZ29-PENNY;
- declara validacao fisica;
- declara equivalencia com o legado.

## Status registrado

```text
PHASE11_10P_SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
RUNTIME_DISPATCH_NOT_CHANGED
PARSER_SCHEMA_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
DISPATCH_REMAINS_BLOCKED
```

## Proxima fase recomendada

```text
PHASE11_10Q_SPECIFY_FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD
```

Essa proxima fase deve especificar como o guard sera chamado pelo futuro
`fracture_initiation_gate`, ainda sem liberar execucao BUZ29-PENNY ate existir
estado inicial de tensao, semantica de pressao e dispatch explicitamente
testados.
