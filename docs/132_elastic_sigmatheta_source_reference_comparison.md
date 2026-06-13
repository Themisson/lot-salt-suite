# Elastic Sigma-Theta Source Reference Comparison

## Resumo executivo

A fase `PHASE_COMPARE_ELASTIC_SIGMATHETA_SOURCE_WITH_REFERENCE` compara a fonte
`AXISYMMETRIC_ELASTIC_WELLBORE_STATE` contra uma referência analítica
controlada.

Resultado esperado:

```text
comparison_status = ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_VALID
reference_type = ANALYTIC_CONTROLLED_REFERENCE
max_abs_error_Pa = 0.0
within_tolerance = true
physically_validated = false
legacy_equivalent = false
legacy_trace_used_as_physical_validation = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## Referência usada

A referência versionada fica em:

```text
tests/fixtures/comparison/phase_elastic_sigmatheta_reference/axisymmetric_reference_cases.json
```

Ela verifica a álgebra:

```text
sigma_theta_initial_compression_positive_Pa =
  far_field_stress_compression_positive_Pa

sigma_theta_current_compression_positive_Pa =
  far_field_stress_compression_positive_Pa - wellbore_pressure_Pa

tensile_condition_Pa =
  -sigma_theta_current_compression_positive_Pa

margin_Pa =
  tensile_condition_Pa - tensile_strength_Pa

reached =
  margin_Pa >= 0
```

## Casos controlados

| Caso | Objetivo |
| --- | --- |
| `compressive_not_reached` | Estado compressivo não inicia fratura diagnóstica. |
| `zero_threshold_reached` | Threshold exato é classificado como atingido. |
| `tension_below_strength_not_reached` | Tração abaixo da resistência não atinge o gate. |
| `tension_above_strength_reached` | Tração acima da resistência atinge o gate. |

## Limites

Esta fase não é validação física plena. Ela não compara BUZ29-PENNY, não usa
trace legado como referência física, não declara equivalência com o LOT_Tese e
não habilita dispatch físico.

## Próxima fase

Com `within_tolerance = true`, o próximo gate permitido é:

```text
PHASE_DECIDE_CONTROLLED_PHYSICAL_COMPARISON_READINESS
```
