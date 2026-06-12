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

## Atualizacao 11.10Q — uso futuro pelo fracture gate

A Fase 11.10Q especifica que este helper deve ser chamado antes de qualquer
criterio fisico:

```text
validate_sigma_theta_initial_state(...)
```

Se `gate_ready = false`, o futuro `fracture_initiation_gate` deve registrar:

```text
FRACTURE_GATE_BLOCKED_BY_SIGMATHETA_GUARD
FRACTURE_MODEL_DISPATCH_NOT_ALLOWED
```

Se `gate_ready = true`, o gate pode apenas avancar para a avaliacao futura do
criterio pressao x sigma-theta. A 11.10Q nao libera dispatch fisico.
## Atualização 11.10R — guard inicial antes do critério físico

O `SigmaThetaInitialStateGuard` permanece uma precondição, não o critério de
fratura. A 11.10R especifica que o futuro guard de critério deve aceitar apenas
estado inicial pronto, semântica de pressão conhecida, referencial de
`sigma_theta` conhecido e sinal `COMPRESSION_POSITIVE`.

O próximo guard deve bloquear:

```text
FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY
FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN
FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN
FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH
```

## Atualizacao 11.10S — guard do criterio pressao x sigma-theta

A Fase 11.10S adiciona o helper isolado
`PressureSigmaThetaFractureCriterionGuard`, que deve ser chamado apenas depois
de `SigmaThetaInitialStateGuard` retornar estado pronto. Essa fase nao conecta
os dois helpers ao runtime; ela apenas deixa o criterio algébrico testado e
disponivel para especificacao de wiring futura.

## Atualizacao 11.10T — posicao do guard inicial no wiring

A 11.10T fixa `SigmaThetaInitialStateGuard` como segundo passo obrigatorio do
futuro `fracture_initiation_gate`, depois de `FractureModelSelector` e antes do
criterio pressao x sigma-theta. Se esse guard falhar, o gate deve registrar:

```text
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
FRACTURE_DISPATCH_NOT_ALLOWED
```

Nenhum runtime wiring foi implementado nesta fase.

## Atualizacao 11.10U — fixture de bloqueio por sigma-theta

A 11.10U adiciona o cenario sintetico
`sigmatheta_guard_blocks_dispatch`, no qual `sigma_theta_guard_ready = false`
deve produzir:

```text
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
FRACTURE_DISPATCH_NOT_ALLOWED
```

Esse cenario valida o contrato de bloqueio, nao uma chamada runtime real.
