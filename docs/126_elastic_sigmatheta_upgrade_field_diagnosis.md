# Diagnóstico de campos para upgrade elástico sigma_theta

## Resumo executivo

A fase diagnostica os campos disponíveis para decidir se o próximo provider
elástico de `sigma_theta` deve seguir uma formulação Kirsch, axisimétrica ou
manter a fonte simplificada.

Status:

```text
ELASTIC_SIGMATHETA_UPGRADE_FIELDS_DIAGNOSED
has_kirsch_required_fields = false
has_axisymmetric_required_fields = true
has_simplified_required_fields = true
recommended_formula_path = AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE
implementation_allowed_next = true
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## Campos auditados

| Campo | Disponível | Observação |
|---|---:|---|
| `wellbore_pressure_Pa` | sim | já usado pelo provider elástico atual |
| `far_field_stress_compression_positive_Pa` | sim | já usado pelo provider elástico atual |
| `far_field_min_horizontal_stress_Pa` | não | necessário para Kirsch completo |
| `far_field_max_horizontal_stress_Pa` | não | necessário para Kirsch completo |
| `vertical_stress_Pa` | não | não exposto no contrato atual do provider |
| `azimuth_angle_rad` | não | necessário para Kirsch orientado |
| `wellbore_radius_m` | não | pode entrar em evolução posterior |
| `casing_radius_m` | não | pode entrar em evolução posterior |
| `poisson_ratio` | não | existe em rocha/casing, mas não no provider |
| `young_modulus_Pa` | não | existe em rocha/casing, mas não no provider |
| `tensile_strength_Pa` | sim | já usado pelo critério diagnóstico |
| `axisymmetric_angle_rad` | não | não necessário para a primeira rota axisimétrica |
| propriedades de camada/material | parcial | existem no `CaseData`, mas não estão ligadas ao provider |

## Decisão de campos

A formulação Kirsch completa exige ao menos tensões horizontais mínima/máxima,
pressão de poço e orientação angular. Esses campos não estão expostos no
contrato atual.

A rota axisimétrica pode usar os mesmos campos já controlados pela fonte
elástica atual:

```text
far_field_stress_compression_positive_Pa
wellbore_pressure_Pa
tensile_strength_Pa
```

Isso permite uma primeira fonte `AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE`
diagnóstica, opt-in e sem dispatch físico.

## Gate

```text
implementation_allowed_next = true
```

O gate permite seguir para a decisão da formulação. A implementação futura deve
continuar mantendo:

```text
physically_validated = false
legacy_equivalent = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## Limites

Este diagnóstico não implementa a fórmula, não altera C++ e não habilita
execução física. Ele apenas registra que Kirsch completo está bloqueado pelos
campos atuais e que a rota axisimétrica é a menor evolução segura.
