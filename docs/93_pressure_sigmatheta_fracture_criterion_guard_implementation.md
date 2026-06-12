# Implementacao do guard pressao x sigma_theta (Fase 11.10S)

## Resumo executivo

A 11.10S implementa apenas o guard isolado do criterio pressao x sigma_theta.
Ela nao integra o criterio ao runtime, nao executa dispatch fisico e nao
executa BUZ29-PENNY.

O helper criado avalia de forma explicita a convencao compression-positive para
`sigma_theta_current_compression_positive_Pa`, bloqueia semantica de pressao ou
referencial desconhecido e calcula a margem de fratura sem usar o atalho
historico `pressure > sigma_theta_compression_positive_Pa`.

## Contexto pos-11.10R

A Fase 11.10R especificou que o futuro `fracture_initiation_gate` deve avaliar
o criterio fisico somente depois do `SigmaThetaInitialStateGuard` estar pronto
e depois de resolver:

```text
pressure_semantics
sigma_theta_reference_frame
sigma_theta_sign_convention
tensile_strength_Pa
```

A 11.10S materializa essa especificacao como helper C++ isolado, mas preserva:

```text
dispatch_allowed_next = false
runtime_execution_allowed_next = false
buz29_execution_allowed_next = false
```

## Guard implementado

Arquivos:

```text
include/lot/PressureSigmaThetaFractureCriterionGuard.hpp
src/lot/PressureSigmaThetaFractureCriterionGuard.cpp
tests/cpp/test_pressure_sigma_theta_fracture_criterion_guard.cpp
```

O guard reutiliza os enums ja existentes em
`SigmaThetaInitialStateGuard.hpp`:

```text
PressureSemantics
SigmaThetaReferenceFrame
SigmaThetaSignConvention
```

Isso evita criar uma segunda taxonomia para a mesma fronteira fisica.

## API C++

Entrada:

```text
PressureSigmaThetaCriterionInput
```

Campos principais:

```text
sigma_theta_guard_ready
sigma_theta_current_compression_positive_Pa
tensile_strength_Pa
use_threshold_pressure_form
wellbore_pressure_Pa
fracture_threshold_pressure_Pa
pressure_semantics
sigma_theta_reference_frame
sigma_theta_sign_convention
```

Saida:

```text
PressureSigmaThetaCriterionResult
```

Campos principais:

```text
status
criterion_ready
fracture_initiated
tensile_condition_Pa
fracture_margin_Pa
blocking_reasons
```

Funcao:

```text
evaluate_pressure_sigma_theta_fracture_criterion(...)
```

## Convencao de sinal

Com sigma_theta em convencao compression-positive, o criterio preferencial usa
`tensile_condition_Pa = -sigma_theta_current_compression_positive_Pa`. O atalho
`pressure > sigma_theta_compression_positive_Pa` permanece proibido.

Convenção preservada:

```text
sigma_theta_current_compression_positive_Pa > 0  -> compressao tangencial
sigma_theta_current_compression_positive_Pa = 0  -> tensao tangencial nula
sigma_theta_current_compression_positive_Pa < 0  -> tracao tangencial
```

## Criterio preferencial

O criterio preferencial implementado e:

```text
tensile_condition_Pa = -sigma_theta_current_compression_positive_Pa
fracture_margin_Pa = tensile_condition_Pa - tensile_strength_Pa
fracture_initiated = fracture_margin_Pa >= 0
```

Forma equivalente:

```text
sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa
```

## Forma alternativa por threshold pressure

A forma alternativa fica disponivel apenas quando selecionada explicitamente:

```text
use_threshold_pressure_form = true
fracture_margin_Pa = wellbore_pressure_Pa - fracture_threshold_pressure_Pa
fracture_initiated = fracture_margin_Pa >= 0
```

Essa forma continua exigindo semantica de pressao, referencial de sigma_theta e
convencao de sinal conhecidos. Ela nao autoriza comparar diretamente pressao
com `sigma_theta_compression_positive_Pa`.

## Atalhos proibidos

Continuam proibidos como criterio fisico final:

```text
pressure > sigma_theta_compression_positive_Pa
wellbore_pressure_Pa > sigma_theta_compression_positive_Pa
net_pressure_Pa > sigma_theta_compression_positive_Pa
```

Esses atalhos nao aparecem no guard como criterio de decisao. Qualquer forma
por pressao deve passar por `fracture_threshold_pressure_Pa` documentado.

## Estados e bloqueios

Estados bloqueantes implementados:

```text
FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY
FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN
FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN
FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH
FRACTURE_CRITERION_BLOCKED_INVALID_TENSILE_STRENGTH
FRACTURE_CRITERION_BLOCKED_INVALID_SIGMATHETA
FRACTURE_CRITERION_BLOCKED_INVALID_PRESSURE
```

Estados prontos implementados:

```text
FRACTURE_CRITERION_READY_NOT_INITIATED
FRACTURE_CRITERION_READY_INITIATED
```

## Testes

Os testes C++ cobrem:

- bloqueio por `sigma_theta_guard_ready = false`;
- semantica de pressao desconhecida;
- referencial desconhecido;
- convencao de sinal desconhecida ou nao compression-positive;
- resistencia a tracao negativa;
- `sigma_theta` nao finito;
- criterio preferencial iniciado e nao iniciado;
- margem preferencial;
- forma por threshold iniciada e nao iniciada;
- pressao invalida na forma por threshold;
- acumulacao de `blocking_reasons`.

Os testes Python cobrem a ferramenta de auditoria da implementacao e confirmam
que parser/schema, dispatch runtime, BUZ29 e comportamento `lot-pkn` continuam
inalterados.

## O que nao foi integrado

A fase nao:

- altera parser ou schema;
- altera `PknModel`;
- altera `PknRunner`;
- altera `volumetric_balance`;
- altera `pkn_direct`;
- integra o guard ao runtime;
- executa BUZ29-PENNY;
- declara validacao fisica;
- declara equivalencia com o legado.

## Proxima fase recomendada

```text
PHASE11_10T_SPECIFY_FRACTURE_GATE_RUNTIME_WIRING_WITH_GUARDS
```

Essa fase deve especificar como o futuro runtime chamara, em sequencia, o
`FractureModelSelector`, o `SigmaThetaInitialStateGuard` e o
`PressureSigmaThetaFractureCriterionGuard`, ainda preservando os bloqueios de
dispatch ate que haja wiring testado e explicitamente autorizado.

## Status registrado

```text
PHASE11_10S_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
SIGMATHETA_COMPRESSION_POSITIVE_CRITERION_IMPLEMENTED
PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
```
