# Elastic Sigma-Theta Upgrade Source Implementation

## Resumo executivo

A Fase D implementa a fonte diagnóstica
`AXISYMMETRIC_ELASTIC_WELLBORE_STATE` no contrato moderno de sigma-theta
pós-perfuração. A implementação preserva a fonte existente
`ELASTIC_INITIAL_WELLBORE_STATE` e não habilita dispatch físico.

O objetivo é dar identidade explícita à rota axisimétrica escolhida nas Fases A,
B e C. A formulação permanece controlada e diagnóstica:

```text
sigma_theta_initial_compression_positive_Pa =
  far_field_stress_compression_positive_Pa

sigma_theta_current_compression_positive_Pa =
  far_field_stress_compression_positive_Pa - wellbore_pressure_Pa
```

## Fonte adicionada

```text
AXISYMMETRIC_ELASTIC_WELLBORE_STATE
```

Essa fonte usa os mesmos campos mínimos já disponíveis no provider:

| Campo | Uso |
| --- | --- |
| `far_field_stress_compression_positive_Pa` | tensão inicial compressiva positiva |
| `wellbore_pressure_Pa` | pressão absoluta no poço para reduzir sigma-theta compressivo |
| `tensile_strength_Pa` | resistência à tração no critério pressão versus sigma-theta |

## Caveats

A saída do provider registra:

```text
AXISYMMETRIC_ELASTIC_WELLBORE_APPROXIMATION
AXISYMMETRIC_WALL_STRESS_DIAGNOSTIC_SOURCE
SEMI_PHYSICAL_ELASTIC_APPROXIMATION
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
```

## Integração

A nova source foi conectada a:

- `PostDrillingSigmaThetaProvider`;
- `FractureGateDiagnosticPreRunner`;
- `SigmaThetaInitialStateGuard`;
- parser de YAML;
- schema de caso LOT.

O `limited_gate` pode consumir a nova source como diagnóstico opt-in. O status
continua sem dispatch físico.

## Segurança

Esta fase não altera:

- comportamento físico PKN;
- `PknModel`;
- `PknRunner`;
- `volumetric_balance`;
- `legacy/`;
- `legance/`;
- `external/saltcreep/`;
- `tests/baselines/`;
- `postprocess/`.

BUZ29-PENNY permanece bloqueado. `PENNY_SHAPED` permanece metadado
diagnóstico, não runtime físico.

## Status

```text
implementation_status = ELASTIC_SIGMATHETA_UPGRADE_SOURCE_IMPLEMENTED
source = AXISYMMETRIC_ELASTIC_WELLBORE_STATE
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
physically_validated = false
legacy_equivalent = false
```

## Próxima fase

`PHASE_VALIDATE_ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES`.
