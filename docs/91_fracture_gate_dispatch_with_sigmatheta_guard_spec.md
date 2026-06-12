# Fase 11.10Q — especificacao do dispatch do fracture gate com sigma-theta guard

## Resumo executivo

A 11.10Q não integra o guard ao runtime e não executa dispatch físico. Ela
apenas especifica como o `fracture_initiation_gate` deverá consultar
`SigmaThetaInitialStateGuard` antes de qualquer dispatch futuro.

Mesmo com `SigmaThetaInitialStateGuard` implementado, o dispatch físico
continua bloqueado até especificar o critério pressão × sigma_theta e a
convenção de sinal associada.

`PENNY_SHAPED` continua diagnóstico, não validado fisicamente e não equivalente
ao legado.

## Contexto pós-11.10P

A Fase 11.10P implementou o helper C++ isolado:

```text
SigmaThetaInitialStateGuard
```

O estado registrado foi:

```text
SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
RUNTIME_DISPATCH_NOT_CHANGED
PARSER_SCHEMA_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
```

Portanto, a 11.10Q parte de uma peça validada, mas ainda não consumida pelo
runtime.

## Auditoria do estado atual

Não existe uma função concentrada chamada `fracture_initiation_gate` no runtime
atual. A lógica está distribuída:

| Responsabilidade | Local atual | Observação |
|---|---|---|
| Seleção de modelo | `FractureModelSelector` | Resolve `PKN` ou `PENNY_SHAPED`; não despacha runtime. |
| Critérios PKN/sigma-theta diagnósticos | `PknModel` | Avalia `sigma_theta_static` e provider diagnóstico, sem estado inicial pós-perfuração. |
| Guard de estado inicial | `SigmaThetaInitialStateGuard` | Helper isolado, ainda não chamado pelo runtime. |
| Adapter/Writer Penny | `PennyShapedDiagnosticAdapter` e `PennyShapedDiagnosticWriter` | Diagnóstico, sem execução BUZ29-PENNY. |

O ponto futuro seguro de integração é uma fronteira explícita de
`fracture_initiation_gate`, depois do `FractureModelSelector` e antes de
qualquer critério físico ou dispatch de modelo.

## Papel do FractureModelSelector

O `FractureModelSelector` deve resolver:

```text
selected_fracture_model
fracture_model_selection_source
diagnostic_only
runtime_supported_now
requires_fracture_initiation_gate
```

Ele não deve autorizar dispatch sozinho. A seleção de `PENNY_SHAPED` continua
opt-in, diagnóstica e bloqueada para runtime físico.

## Papel do SigmaThetaInitialStateGuard

O `SigmaThetaInitialStateGuard` deve ser consultado antes de qualquer avaliação
de critério de fratura. Ele valida:

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

Se o guard retornar `gate_ready = false`, o futuro
`fracture_initiation_gate` deve registrar:

```text
FRACTURE_GATE_BLOCKED_BY_SIGMATHETA_GUARD
FRACTURE_MODEL_DISPATCH_NOT_ALLOWED
```

## Sequência futura de dispatch

Fluxo especificado:

```text
1. Parser lê lot.fracture.fracture_model.
2. FractureModelSelector resolve selected_fracture_model.
3. Simulação LOT calcula ou recebe estado inicial sigma_theta.
4. SigmaThetaInitialStateGuard valida o estado inicial e a semântica de pressão.
5. Se o guard bloquear:
   fracture_initiation_gate = BLOCKED
   dispatch = NOT_ALLOWED
   blocking_reasons = guard.blocking_reasons
6. Se o guard passar:
   fracture_initiation_gate pode avaliar o critério pressão × sigma_theta.
7. Se o critério físico não for atingido:
   dispatch = NOT_REACHED
8. Se o critério físico for atingido:
   dispatch seleciona o fracture_model somente em fase futura autorizada.
```

## Estados do fracture gate

Estados especificados:

```text
FRACTURE_GATE_BLOCKED_BY_SIGMATHETA_GUARD
FRACTURE_GATE_READY_FOR_CRITERION_EVALUATION
FRACTURE_GATE_NOT_REACHED
FRACTURE_GATE_REACHED
FRACTURE_MODEL_DISPATCH_NOT_ALLOWED
FRACTURE_MODEL_DISPATCH_ALLOWED
```

Na 11.10Q:

```text
dispatch_allowed_next = false
runtime_execution_allowed_next = false
buz29_execution_allowed_next = false
```

## Campos obrigatórios

Campos conceituais para o gate futuro:

```text
selected_fracture_model
fracture_model_selection_source
wellbore_pressure_Pa
pressure_semantics
sigma_theta_initial_compression_positive_Pa
sigma_theta_current_compression_positive_Pa
sigma_theta_source
sigma_theta_state_time
sigma_theta_reference_frame
sigma_theta_sign_convention
sigma_theta_guard_status
fracture_initiation_gate_status
fracture_dispatch_status
blocking_reasons
```

## Regras de bloqueio

O futuro gate deve bloquear dispatch quando:

```text
sigma_theta_guard_status != SIGMATHETA_INITIAL_STATE_READY
pressure_semantics = UNKNOWN
sigma_theta_sign_convention = UNKNOWN
pressure × sigma_theta criterion ainda não especificado
selected_fracture_model não foi resolvido
PENNY_SHAPED permanece diagnostic_only = true
BUZ29-PENNY permanece sem autorização runtime
```

Estados registrados:

```text
SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH
FRACTURE_MODEL_SELECTOR_REQUIRED_BEFORE_DISPATCH
PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED
SIGN_CONVENTION_RESOLUTION_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

## O que ainda falta para dispatch físico

Antes de qualquer dispatch físico, ainda é necessário especificar:

1. O critério pressão × sigma_theta.
2. Qual pressão entra no critério: absoluta, incremento ou net pressure.
3. Qual referencial de sigma_theta é aceito: total, efetivo ou incremental.
4. Como a convenção de sinal será garantida no ponto de chamada.
5. Como os motivos de bloqueio serão propagados para resultado e logs.
6. Se e quando `PENNY_SHAPED` pode deixar de ser apenas diagnóstico.

## Próxima fase recomendada

```text
PHASE11_10R_SPECIFY_PRESSURE_SIGMATHETA_FRACTURE_CRITERION
```

Essa fase deve especificar o critério de comparação entre pressão e
`sigma_theta` antes de qualquer integração do guard ao runtime.

## Status registrado

```text
PHASE11_10Q_FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH
FRACTURE_MODEL_SELECTOR_REQUIRED_BEFORE_DISPATCH
PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED
SIGN_CONVENTION_RESOLUTION_REQUIRED
DISPATCH_REMAINS_BLOCKED
```
