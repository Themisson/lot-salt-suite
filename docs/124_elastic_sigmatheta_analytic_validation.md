# Validação analítica da fonte elástica sigma_theta

## Resumo executivo

Esta fase verifica analiticamente a fórmula implementada para
`ELASTIC_INITIAL_WELLBORE_STATE`. A verificação confirma consistência algébrica
e de sinal, mas não constitui validação física plena.

Status:

```text
PHASE_ELASTIC_SIGMATHETA_ANALYTIC_VALIDATION
ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID
FORMULA_VERIFIED
SIGN_CONVENTION_VERIFIED
THRESHOLD_BEHAVIOR_VERIFIED
PHYSICALLY_VALIDATED_FALSE
LEGACY_EQUIVALENT_FALSE
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

## Fórmula verificada

A fonte elástica inicial usa:

```text
sigma_theta_initial_compression_positive_Pa =
  far_field_stress_compression_positive_Pa

sigma_theta_current_compression_positive_Pa =
  far_field_stress_compression_positive_Pa - wellbore_pressure_Pa
```

O critério diagnóstico usa:

```text
tensile_condition_Pa = -sigma_theta_current_compression_positive_Pa
fracture_margin_Pa = tensile_condition_Pa - tensile_strength_Pa
fracture_initiated = fracture_margin_Pa >= 0
```

## Convenção de sinal

A verificação preserva a convenção do projeto:

```text
compressão positiva
tensão tangencial trativa => sigma_theta_current_compression_positive_Pa < 0
```

Assim, quanto mais negativa a tensão tangencial na convenção
compressão-positiva, maior o `tensile_condition_Pa` usado pelo guard.

## Casos analíticos

Fixture versionada:

```text
tests/fixtures/comparison/phase_elastic_sigmatheta_analytic/elastic_sigmatheta_analytic_cases.json
```

| Caso | Far-field Pa | Pressão poço Pa | Resistência Pa | sigma_theta current Pa | Margem Pa | Status |
|---|---:|---:|---:|---:|---:|---|
| `compressive_not_reached` | 10000000 | 6000000 | 1000000 | 4000000 | -5000000 | ReadyNotReached |
| `zero_hoop_not_reached` | 8000000 | 8000000 | 1000000 | 0 | -1000000 | ReadyNotReached |
| `tension_below_strength_not_reached` | 8000000 | 8500000 | 1000000 | -500000 | -500000 | ReadyNotReached |
| `tension_above_strength_reached` | 8000000 | 9500000 | 1000000 | -1500000 | 500000 | Reached |
| `exact_threshold_reached` | 8000000 | 9000000 | 1000000 | -1000000 | 0 | Reached |

## Threshold

O threshold exato é classificado como `Reached` porque o contrato do guard usa:

```text
fracture_margin_Pa >= 0
```

Essa escolha foi verificada em C++ e na ferramenta Python de validação
analítica.

## Ferramenta

Ferramenta criada:

```text
tools/validate_elastic_sigmatheta_analytic_cases.py
```

Saída esperada:

```text
validation_status = ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID
formula_verified = true
sign_convention_verified = true
threshold_behavior_verified = true
case_count = 5
```

## Limites

O estado `Reached` continua sendo elegibilidade diagnóstica do gate, não
execução física de fratura.

A fase não:

- implementa Kirsch completo;
- valida equivalência com `LOT_Tese`;
- habilita dispatch físico;
- executa BUZ29-PENNY;
- transforma `PENNY_SHAPED` em runtime físico;
- altera PKN.

## Próxima fase recomendada

```text
PHASE_DECIDE_ELASTIC_SIGMATHETA_SOURCE_READINESS
```

## Decisão posterior

A fase de readiness decidiu:

```text
ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE
ready_for_diagnostic_semiphysical_use = true
ready_for_physical_validation = false
ready_for_physical_dispatch = false
ready_for_kirsch_upgrade_spec = true
```

A validação analítica permanece evidência de consistência algébrica e de sinal,
não validação física plena. O próximo salto técnico recomendado é:

```text
PHASE_SPECIFY_KIRSCH_OR_AXISYMMETRIC_ELASTIC_SIGMATHETA_UPGRADE
```
