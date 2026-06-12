# Fase 11.10C — auditoria matemática PennyShaped em 1 rad

## Resumo executivo

A 11.10C não corrige o PennyShapedModel e não executa BUZ29-PENNY. Ela apenas audita a formulação matemática implementada e decide se a próxima fase deve corrigir código, documentar a formulação ou definir contrato de saída.

Resultado:

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
tertiary_classification = PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL
math_audit_passed = true
requires_code_correction = false
requires_documentation_update = true
requires_output_contract = true
recommended_next_phase = PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT
```

O modelo é dimensionalmente consistente para abertura, raio e volume proxy, mas
continua diagnóstico: `fracture_volume_proxy_m3` deve ser tratado como proxy
em base axissimétrica de 1 rad até que exista contrato explícito para saídas
1rad e 2π equivalente.

## Contexto pós-11.10B

A 11.10B classificou as entradas BUZ29-PENNY como parciais:

```text
classification = BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
adapter_ready = false
partial_adapter_ready = true
recommended_next_phase = PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD
```

Assim, a 11.10C audita a matemática existente antes de qualquer execução
diagnóstica.

## Arquivos auditados

- `include/lot/PennyShapedModel.hpp`
- `src/lot/PennyShapedModel.cpp`
- `include/lot/PennyShapedDiagnosticAdapter.hpp`
- `src/lot/PennyShapedDiagnosticAdapter.cpp`
- `tests/cpp/test_penny_shaped_model.cpp`
- `tests/cpp/test_penny_shaped_diagnostic_adapter.cpp`
- `docs/63_selected_non_pkn_model_minimal_implementation.md`
- `docs/65_penny_diagnostic_adapter_spec.md`
- `docs/66_penny_diagnostic_adapter_implementation.md`
- `docs/75_buz29_penny_adapter_ready_inputs.md`

Nenhum desses arquivos C++ foi alterado.

## API real do adapter

O `PennyShapedDiagnosticAdapter` consome:

| Campo | Unidade |
|---|---:|
| `young_modulus_Pa` | Pa |
| `poisson_ratio` | adimensional |
| `viscosity_Pa_min` | Pa.min |
| `flow_rate_m3_min` | m3/min |
| `elapsed_since_opening_min` | min |
| `wellbore_pressure_Pa` | Pa |
| `sigma_theta_compression_positive_Pa` | Pa |
| `volume_multiplier` | adimensional |

Saídas:

- `plane_strain_modulus_Pa`;
- `opening_m`;
- `radius_m`;
- `pressure_factor`;
- `fracture_volume_proxy_m3`.

## Equações implementadas

```text
E' = E / (1 - nu^2)
w0 = 3.65 * ((mu^2 * Q^3) / E'^2)^(1/9) * t^(1/9)
R = 0.572 * ((E' * Q^3) / mu)^(1/9) * t^(4/9)
pressure_factor = wellbore_pressure_Pa / sigma_theta_compression_positive_Pa
fracture_volume_proxy_m3 =
  volume_multiplier * (w0/2)^2 * R * pi * pressure_factor
```

## Auditoria dimensional

| Campo | Status | Nota |
|---|---|---|
| `young_modulus_Pa` | `DIMENSION_OK` | Pressão. |
| `poisson_ratio` | `DIMENSION_OK` | Adimensional. |
| `viscosity_Pa_min` | `DIMENSION_OK` | Coerente com `flow_rate_m3_min` e tempo em minutos. |
| `flow_rate_m3_min` | `DIMENSION_OK` | Usado como `Q^3`. |
| `elapsed_since_opening_min` | `DIMENSION_OK` | Expoentes cancelam a dimensão temporal. |
| `wellbore_pressure_Pa` | `DIMENSION_REQUIRES_SEMANTIC_REVIEW` | Usada apenas em razão de pressão. |
| `sigma_theta_compression_positive_Pa` | `DIMENSION_REQUIRES_SEMANTIC_REVIEW` | Compressão positiva; usada no denominador da razão. |
| `volume_multiplier` | `DIMENSION_PROXY_ONLY` | Adimensional e legado/empírico. |
| `plane_strain_modulus_Pa` | `DIMENSION_OK` | Pressão. |
| `opening_m` | `DIMENSION_OK` | Resultado em metro. |
| `radius_m` | `DIMENSION_OK` | Resultado em metro. |
| `pressure_factor` | `DIMENSION_REQUIRES_SEMANTIC_REVIEW` | Razão, não pressão líquida. |
| `fracture_volume_proxy_m3` | `DIMENSION_PROXY_ONLY` | Dimensionalmente volume, semanticamente proxy. |

## Semântica de pressão e sigmaTheta

Classificação:

```text
PRESSURE_SEMANTICS_CLEAR
```

O código não calcula `net_pressure_Pa`, `effective_pressure_Pa`,
`fracture_driving_pressure_Pa` ou `breakdown_margin`. Ele calcula apenas:

```text
pressure_factor = wellbore_pressure_Pa / sigma_theta_compression_positive_Pa
```

Isso é claro dimensionalmente e operacionalmente, mas permanece diagnóstico.
Não deve ser interpretado como critério completo de fratura BUZ29.

## Semântica de volume_multiplier

Classificação:

```text
VOLUME_MULTIPLIER_EMPIRICAL
```

O multiplicador é aplicado uma única vez:

```text
volume_multiplier * (w0/2)^2 * R * pi * pressure_factor
```

O valor default `10.0` é legado/empírico. Ele não deve ser reutilizado como
fator angular 2π nem combinado com uma futura conversão 1rad/2π sem contrato
explícito, para evitar dupla contagem.

## Formulação axissimétrica 1 rad

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

Como o projeto utiliza formulação axissimétrica em 1 rad, qualquer volume/proxy interno deve ser distinguido de volume total equivalente em 2π. As saídas futuras deverão declarar explicitamente a base angular e, quando aplicável, reportar também o volume total equivalente do sólido/fratura.

## Requisito futuro de saída

```text
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
```

A próxima fase deve definir um contrato de saída que separe, sem mudar ainda o
solver:

- `axisymmetric_angle_rad`;
- `fracture_volume_proxy_1rad_m3`;
- `fracture_volume_equivalent_2pi_m3`;
- `solid_volume_1rad_m3`;
- `solid_volume_equivalent_2pi_m3`;
- `volume_multiplier`.

## Classificação matemática

Primária:

```text
PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
```

Secundária:

```text
PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
```

Terciária:

```text
PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL
```

## Correções recomendadas

Nenhuma correção C++ é recomendada nesta fase. A formulação atual passa na
auditoria dimensional, mas exige contrato de saída antes de qualquer execução
diagnóstica BUZ29.

## Próxima fase recomendada

```text
PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT
```
