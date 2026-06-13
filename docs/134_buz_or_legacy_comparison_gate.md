# BUZ or Legacy Comparison Gate

## Resumo executivo

A fase `PHASE_PREPARE_BUZ_OR_LEGACY_COMPARISON_GATE` prepara o gate para uma
comparação futura envolvendo referência analítica, BUZ67D/PKN diagnóstico ou
legado auditado.

Status:

```text
gate_status = BUZ_OR_LEGACY_COMPARISON_GATE_PREPARED
recommended_first_comparison = ANALYTIC_OR_BUZ67D_PKN_DIAGNOSTIC
buz29_penny_execution_allowed = false
legacy_equivalence_allowed = false
physical_validation_allowed = false
runtime_dispatch_enabled = false
pkn_behavior_change_allowed = false
```

## Casos candidatos

| Caso | Rota | Permitido? | Uso |
| --- | --- | --- | --- |
| `axisymmetric_analytic_reference` | analítica | sim | manter a álgebra da source fixada antes de comparações externas |
| `buz67d_pkn_diagnostic` | PKN moderno diagnóstico | sim | comparação controlada futura, sem validação física |
| `buz29_penny` | não-PKN legado | não | bloqueado até gate não-PKN físico/runtime próprio |

## Campos a alinhar antes de comparar

```text
wellbore_pressure_Pa
far_field_stress_compression_positive_Pa
tensile_strength_Pa
sigma_theta_current_compression_positive_Pa
fracture_gate_reached
time_s
pressure_semantics
stress_reference_frame
sign_convention
```

## Tolerâncias iniciais

| Métrica | Status |
| --- | --- |
| Erro absoluto da referência analítica | `1.0e-9 Pa` |
| Erro relativo de pressão diagnóstica | requer gate futuro |
| Erro de tempo de abertura | requer gate futuro |

## Bloqueios preservados

Esta fase não executa BUZ29-PENNY, não valida fisicamente a source, não declara
equivalência com o LOT_Tese, não habilita dispatch runtime e não altera o
comportamento PKN.

## Próxima fase

```text
PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON
```

## Comparação controlada executada

`PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON` foi executada contra uma
referência `ANALYTIC_AXISYMMETRIC_CONTROLLED_REFERENCE`, sem BUZ29-PENNY e sem
dispatch físico.

```text
comparison_status = FIRST_CONTROLLED_REFERENCE_COMPARISON_VALID
max_abs_error_Pa = 0.0
within_tolerance = true
physical_validation_claimed = false
legacy_equivalence_claimed = false
runtime_dispatch_enabled = false
buz29_penny_executed = false
pkn_behavior_changed = false
```

## BUZ29/PENNY Diagnostic Execution Gate

The execution gate was decided for a future diagnostic-only step:

```text
BUZ29_PENNY_DIAGNOSTIC_EXECUTION_ALLOWED_NEXT
execution_allowed_next = true
buz29_penny_executed_now = false
runtime_dispatch_enabled = false
physically_validated = false
legacy_equivalent = false
```

The authorization is progressive and scoped: it permits only the next
diagnostic-comparison phase. It does not enable runtime dispatch, does not
execute BUZ29/PENNY in this phase, and does not claim physical validation or
legacy equivalence.

## BUZ29/PENNY Inputs Prepared

The BUZ29/PENNY diagnostic input manifest was prepared without execution:

```text
BUZ29_PENNY_DIAGNOSTIC_INPUTS_PREPARED
execution_allowed = false
diagnostic_only = true
physically_validated = false
legacy_equivalent = false
runtime_dispatch_enabled = false
```

O próximo gate progressivo é
`PHASE_DECIDE_BUZ67D_PKN_REFERENCE_READINESS`.

## Readiness BUZ67D/PKN

A fase `PHASE_DECIDE_BUZ67D_PKN_REFERENCE_READINESS` decidiu que BUZ67D/PKN
está pronto apenas como referência diagnóstica controlada:

```text
BUZ67D_PKN_READY_FOR_DIAGNOSTIC_REFERENCE
physical_validation_claimed = false
legacy_equivalence_claimed = false
buz29_penny_executed = false
runtime_dispatch_enabled = false
pkn_behavior_changed = false
```
