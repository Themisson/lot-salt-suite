# Decisão de readiness da fonte elástica sigma_theta

## Resumo executivo

A fonte `ELASTIC_INITIAL_WELLBORE_STATE` está pronta para uso diagnóstico
semi-físico no `limited_gate`, com a restrição explícita de que ela não é
validação física plena, não é equivalente ao legado e não habilita dispatch
físico.

Status:

```text
PHASE_ELASTIC_SIGMATHETA_SOURCE_READINESS_DECIDED
ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE
READY_FOR_KIRSCH_OR_AXISYMMETRIC_UPGRADE_SPEC
PHYSICALLY_VALIDATED_FALSE
LEGACY_EQUIVALENT_FALSE
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

A fonte ELASTIC_INITIAL_WELLBORE_STATE está pronta para uso diagnóstico
semi-físico, mas não para validação física plena nem para dispatch físico.

## Contexto

A fase anterior validou analiticamente a fonte elástica inicial com cinco casos
controlados. A validação confirmou a fórmula, a convenção de sinal e o
comportamento do threshold exato.

## Evidências consideradas

Fontes auditadas:

- `docs/123_elastic_initial_wellbore_sigmatheta_source.md`
- `docs/124_elastic_sigmatheta_analytic_validation.md`
- `tools/validate_elastic_sigmatheta_analytic_cases.py`
- `tests/fixtures/comparison/phase_elastic_sigmatheta_analytic/elastic_sigmatheta_analytic_cases.json`
- `include/lot/PostDrillingSigmaThetaProvider.hpp`
- `src/lot/PostDrillingSigmaThetaProvider.cpp`

Evidência consolidada:

```text
ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID
FORMULA_VERIFIED
SIGN_CONVENTION_VERIFIED
THRESHOLD_BEHAVIOR_VERIFIED
semi_physical = true
physically_validated = false
legacy_equivalent = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
```

## Fórmula atual

A fonte usa a aproximação:

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

## Readiness

Decisão:

```text
readiness_status =
  ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE

ready_for_diagnostic_semiphysical_use = true
ready_for_physical_validation = false
ready_for_physical_dispatch = false
ready_for_kirsch_upgrade_spec = true
```

Essa decisão permite usar a fonte em diagnósticos controlados do gate. Ela não
permite promover o resultado para validação física de fratura, equivalência com
`LOT_Tese`, execução `BUZ29-PENNY` ou runtime físico `PENNY_SHAPED`.

## Limites

A fórmula atual é uma aproximação elástica simplificada. O próximo salto
técnico deve especificar uma formulação Kirsch/hoop stress ou uma formulação
elástica axisimétrica mais alinhada ao runtime.

Limites principais:

- não usa tensões horizontais orientadas;
- não modela anisotropia ou orientação angular;
- não calcula estado multicamada;
- não consome estado APB/sal acoplado;
- não substitui `SaltWallStressDiagnostics`;
- não estabelece equivalência com APBSalt1D/LOT_Tese.

## Alternativas futuras

| Alternativa | Uso | Status |
|---|---|---|
| Kirsch/hoop stress simplificado | tensão tangencial na parede com tensões horizontais e pressão interna | pronta para especificação |
| Elástico axisimétrico/multicamada | fonte alinhada ao runtime 1 rad/axisimétrico atual | preferida para próxima especificação |
| Estado APB/sal acoplado | fonte mais física e finalista | futuro, maior risco |

Como o runtime atual é predominantemente axisimétrico e não possui orientação de
poço explícita para uma formulação Kirsch completa, a próxima especificação deve
priorizar a rota elástica axisimétrica, mantendo a opção Kirsch como alternativa
ou caso reduzido.

## Próximo salto recomendado

```text
PHASE_SPECIFY_KIRSCH_OR_AXISYMMETRIC_ELASTIC_SIGMATHETA_UPGRADE
```

Essa próxima fase deve especificar a evolução sem habilitar dispatch físico e
sem executar BUZ29-PENNY.

## Bloqueios preservados

```text
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
penny_shaped_runtime_enabled = false
physically_validated = false
legacy_equivalent = false
```
