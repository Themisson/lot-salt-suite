# Fonte elástica inicial de sigma_theta na parede

## Resumo executivo

Esta fase implementa uma fonte elástica inicial semi-física para
`sigma_theta` no `PostDrillingSigmaThetaProvider`. A fonte é opt-in e alimenta o
`limited_gate` por meio do `FractureGateDiagnosticPreRunner`, preservando o
fluxo diagnóstico já existente.

Status:

```text
ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED
source = ELASTIC_INITIAL_WELLBORE_STATE
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
```

Esta fase implementa uma fonte elástica inicial semi-física para sigma_theta.
Ela não representa validação física plena, não habilita dispatch físico e não
declara equivalência com legado.

## Formulação diagnóstica

A fonte usa uma aproximação elástica local simplificada em convenção de
compressão positiva:

```text
sigma_theta_initial_compression_positive_Pa =
  far_field_stress_compression_positive_Pa

sigma_theta_current_compression_positive_Pa =
  far_field_stress_compression_positive_Pa - wellbore_pressure_Pa
```

Essa relação permite representar dois regimes diagnósticos:

| Condição | Interpretação no gate |
|---|---|
| `sigma_theta_current_compression_positive_Pa > 0` | parede ainda compressiva; gate não atingido |
| `sigma_theta_current_compression_positive_Pa < 0` | estado trativo na convenção do guard; gate pode ser atingido |

O critério continua usando o guard `PressureSigmaThetaFractureCriterionGuard`.
O provider apenas fornece o estado inicial/current de `sigma_theta`; ele não
executa modelo de fratura.

## YAML

Bloco opt-in:

```yaml
lot:
  fracture:
    fracture_gate_diagnostics:
      enabled: true
      mode: limited_gate
      dispatch_runtime_enabled: false
    sigma_theta_provider:
      enabled: true
      source: ELASTIC_INITIAL_WELLBORE_STATE
      far_field_stress_compression_positive_Pa: 5000000.0
      wellbore_pressure_Pa: 7000000.0
      tensile_strength_Pa: 0.0
      physically_validated: false
      legacy_equivalent: false
```

Regras:

- `source` aceita somente `ELASTIC_INITIAL_WELLBORE_STATE` nesta fase.
- `far_field_stress_compression_positive_Pa` deve ser finito e maior que zero.
- `wellbore_pressure_Pa` deve ser finito e não negativo.
- `physically_validated` deve permanecer `false`.
- `legacy_equivalent` deve permanecer `false`.
- `sigma_theta_provider` e `sigma_theta_diagnostic_input` são mutuamente
  exclusivos quando habilitados.

## Wiring

O `FractureGateDiagnosticPreRunner` passa a aceitar duas fontes mutuamente
exclusivas:

| Fonte | Uso |
|---|---|
| `sigma_theta_provider` | fonte semi-física opt-in |
| `sigma_theta_diagnostic_input` | entrada explícita/fixture diagnóstica |

Quando `sigma_theta_provider.enabled=true`, o pre-runner chama
`evaluate_post_drilling_sigma_theta(...)` e preenche:

```text
SigmaThetaInitialStateGuard
PressureSigmaThetaFractureCriterionGuard
```

O status `PknEligible` ou `PennyDiagnosticEligible` permanece diagnóstico. Ele
não chama `PknModel`, `PknRunner` ou `PennyShapedDiagnosticAdapter`.

## Fixtures e auditoria

Fixtures versionadas:

```text
tests/fixtures/comparison/phase_elastic_sigmatheta_source/
```

Cenários cobertos:

| Fixture | Objetivo |
|---|---|
| `elastic_provider_disabled_default.yaml` | provider/gate ausentes |
| `elastic_provider_ready_not_reached.yaml` | estado ainda compressivo |
| `elastic_provider_reached_pkn.yaml` | gate atingido para PKN diagnóstico |
| `elastic_provider_reached_penny_diagnostic.yaml` | gate atingido para PENNY diagnóstico |
| `elastic_provider_invalid_physically_validated_true.yaml` | rejeição de validação física |
| `elastic_provider_invalid_legacy_equivalent_true.yaml` | rejeição de equivalência legado |
| `elastic_provider_ambiguous_with_diagnostic_input.yaml` | rejeição de ambiguidade |
| `elastic_provider_invalid_missing_far_field_stress.yaml` | campo obrigatório ausente |
| `elastic_provider_invalid_missing_wellbore_pressure.yaml` | campo obrigatório ausente |

Ferramenta:

```text
tools/audit_elastic_initial_wellbore_sigmatheta_source.py
```

Classificação esperada:

```text
ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED
```

## Garantias

```text
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
```

O PKN permanece retrocompatível. BUZ29-PENNY permanece bloqueado. A trilha
`PENNY_SHAPED` continua diagnóstica.

## Limites

Esta fonte é uma aproximação inicial útil para diagnóstico do gate. Ela ainda
não substitui:

- `SaltWallStressDiagnostics` runtime;
- acoplamento APB/sal;
- equivalência com `LOT_Tese`;
- validação física de abertura;
- dispatch físico não-PKN.

## Próxima fase recomendada

```text
PHASE_VALIDATE_ELASTIC_SIGMATHETA_SOURCE_AGAINST_KNOWN_ANALYTIC_CASE
```

A próxima fase deve validar a fonte elástica contra caso analítico controlado
antes de qualquer uso físico mais amplo.

## Validação analítica controlada

A fase seguinte foi executada e confirmou:

```text
ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID
FORMULA_VERIFIED
SIGN_CONVENTION_VERIFIED
THRESHOLD_BEHAVIOR_VERIFIED
```

Essa validação confirma consistência algébrica da fonte e do critério
diagnóstico, mas não constitui validação física plena.
