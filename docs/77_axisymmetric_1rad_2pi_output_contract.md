# Fase 11.10D — contrato de saída axissimétrico 1 rad ↔ 2π

## Resumo executivo

A Fase 11.10D define o contrato explícito de saída para grandezas calculadas
na formulação axissimétrica interna de 1 rad da trilha `PENNY_SHAPED`.

Status:

```text
PHASE11_10D_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
IMPLEMENTATION_NOT_ALLOWED_IN_11_10D
```

A 11.10D não implementa writer, runner ou alteração C++. Ela apenas define o
contrato de saída para que futuras implementações possam expor corretamente
grandezas internas em 1 rad e volumes totais equivalentes em 2π.

## Contexto pós-11.10C

A Fase 11.10C auditou o `PennyShapedModel` e concluiu:

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
tertiary_classification = PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL
pressure_semantics = PRESSURE_SEMANTICS_CLEAR
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
math_audit_passed = true
requires_code_correction = false
requires_output_contract = true
```

Portanto, a próxima ação segura é especificar os nomes, unidades, base angular,
fontes e caveats dos campos de saída, sem executar BUZ29-PENNY e sem declarar
validação física.

## Problema: 1 rad interno versus 2π físico

O modelo atual expõe `fracture_volume_proxy_m3`. Esse campo é
dimensionalmente compatível com volume, mas ainda mistura:

- geometria interna de 1 rad;
- multiplicador empírico `volume_multiplier`;
- razão diagnóstica de pressão;
- ausência de contrato para total equivalente em 2π.

Por isso, o campo não deve ser lido automaticamente como volume físico total
da fratura circular completa.

## Semântica de volume_multiplier

```text
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
```

volume_multiplier permanece classificado como VOLUME_MULTIPLIER_EMPIRICAL e
não deve ser reutilizado como fator geométrico 2π.

Regras:

- `volume_multiplier` é adimensional.
- `volume_multiplier` é empírico/diagnóstico.
- `volume_multiplier` não é `angular_multiplier_rad`.
- `volume_multiplier` não substitui `volume_conversion_factor_1rad_to_2pi`.
- qualquer futura redefinição deve renomear ou documentar explicitamente o
  campo para evitar dupla contagem.

## Campos de saída propostos

| Campo | Unidade | Base angular | Obrigatório | Source obrigatório | Significado |
|---|---:|---|---:|---:|---|
| `axisymmetric_angle_rad` | rad | metadata | sim | não | Base angular interna da formulação; valor inicial esperado `1.0`. |
| `axisymmetric_basis` | texto | metadata | sim | não | Nome da base angular; valor esperado `axisymmetric_1rad`. |
| `volume_multiplier` | adimensional | empírico | sim | não | Multiplicador diagnóstico herdado do adapter. |
| `volume_multiplier_semantics` | texto | metadata | sim | não | Deve registrar `VOLUME_MULTIPLIER_EMPIRICAL`. |
| `fracture_volume_proxy_1rad_m3` | m³ | `axisymmetric_1rad_internal` | sim | não | Proxy diagnóstico de volume de fratura na base interna de 1 rad. |
| `fracture_volume_equivalent_2pi_m3` | m³ | `axisymmetric_2pi_equivalent` | opcional | sim | Equivalente 2π somente quando o proxy for declarado geometricamente integrável. |
| `fracture_volume_equivalent_2pi_source` | texto | metadata | sim | não | Fonte/caveat do equivalente 2π. |
| `solid_volume_1rad_m3` | m³ | `axisymmetric_1rad_internal` | opcional | não | Volume do domínio sólido em 1 rad, quando aplicável. |
| `solid_volume_equivalent_2pi_m3` | m³ | `axisymmetric_2pi_equivalent` | opcional | sim | Volume sólido total equivalente em 2π, quando aplicável. |
| `volume_conversion_factor_1rad_to_2pi` | adimensional | conversão geométrica | sim | não | Fator geométrico `2π`. |
| `volume_interpretation` | texto | metadata | sim | não | Interpretação dos campos volumétricos. |
| `physically_validated` | boolean | metadata | sim | não | Deve permanecer `false` neste contrato. |
| `legacy_equivalent` | boolean | metadata | sim | não | Deve permanecer `false` até prova específica. |
| `diagnostic_only` | boolean | metadata | sim | não | Deve permanecer `true` para a rota diagnóstica. |

## Valores permitidos

`fracture_volume_equivalent_2pi_source`:

```text
computed_from_1rad_proxy
not_applicable
blocked_proxy_only
future_runtime_field
```

`volume_interpretation`:

```text
axisymmetric_1rad_internal
axisymmetric_1rad_with_2pi_equivalent
proxy_only_not_total_volume
empirical_multiplier_applied
not_physically_validated
```

## Regras de conversão

Regra 1:

```text
Se uma grandeza volumétrica for declarada como *_1rad_m3 e for
geometricamente integrável:
  *_equivalent_2pi_m3 = *_1rad_m3 * 2π
```

Regra 2:

```text
Se uma grandeza for proxy empírico:
  não gerar automaticamente equivalente 2π sem campo source/caveat.
```

Regra 3:

```text
volume_multiplier não é igual a 2π, salvo se futura fase renomear e redefinir
semanticamente o campo.
```

Regra 4:

```text
campos equivalentes 2π devem sempre informar source.
```

Regra 5:

```text
qualquer saída com volume total equivalente deve preservar também o valor 1rad
de origem.
```

Regra 6:

```text
relatórios devem declarar:
  axisymmetric_angle_rad
  volume_conversion_factor_1rad_to_2pi
  volume_interpretation
```

Toda saída física volumétrica deverá preservar a grandeza de origem em 1 rad
e, quando aplicável, reportar separadamente o equivalente total em 2π com
campo source/caveat.

## Campos proibidos ou ambíguos

Interpretações proibidas nesta etapa:

- tratar `volume_multiplier` como `2π`;
- tratar `fracture_volume_proxy_1rad_m3` como volume físico total validado;
- reportar `fracture_volume_equivalent_2pi_m3` sem `source`;
- descartar o campo de origem `*_1rad_m3`;
- declarar validação física BUZ29-PENNY;
- declarar equivalência com o legado.

## Caveats obrigatórios

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
IMPLEMENTATION_NOT_ALLOWED_IN_11_10D
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
DIAGNOSTIC_ONLY
```

## Contrato recomendado para CSV/JSON futuros

CSV/JSON futuros da trilha PennyShaped diagnóstica devem incluir, no mínimo:

```text
axisymmetric_angle_rad
axisymmetric_basis
volume_conversion_factor_1rad_to_2pi
volume_multiplier
volume_multiplier_semantics
fracture_volume_proxy_1rad_m3
fracture_volume_equivalent_2pi_m3
fracture_volume_equivalent_2pi_source
volume_interpretation
physically_validated
legacy_equivalent
diagnostic_only
```

Se houver saída de domínio sólido, adicionar:

```text
solid_volume_1rad_m3
solid_volume_equivalent_2pi_m3
solid_volume_equivalent_2pi_source
```

## Testes futuros

A próxima implementação deve testar:

- presença dos campos de metadado angular;
- `volume_conversion_factor_1rad_to_2pi == 2π`;
- preservação do campo de origem `*_1rad_m3`;
- rejeição de equivalente 2π sem `source`;
- separação entre `volume_multiplier` e fator geométrico 2π;
- `physically_validated == false` e `legacy_equivalent == false` enquanto a rota
  seguir diagnóstica.

## Próxima fase recomendada

```text
PHASE11_10E_DEFINE_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES
```

Essa próxima fase deve criar fixtures de saída diagnóstica PennyShaped com o
contrato aqui definido, ainda sem writer/runtime C++.

## Resultado da Fase 11.10E

A Fase 11.10E criou fixtures pequenos e versionados que materializam este
contrato:

```text
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.json
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.csv
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_metadata.json
```

O status registrado é:

```text
PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID
FIXTURE_ONLY_NO_RUNTIME_WRITER
IMPLEMENTATION_NOT_ALLOWED_IN_11_10E
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_MATERIALIZED_AS_FIXTURE
```

Esses fixtures preservam o campo interno `fracture_volume_proxy_1rad_m3`,
reportam um equivalente `2π` separado com `source` e mantêm `volume_multiplier`
como empírico, não como conversão geométrica. A fase não implementa writer e
não valida BUZ29-PENNY.

## Resultado da Fase 11.10F

A Fase 11.10F especificou o writer diagnóstico futuro que deverá consumir este
contrato em uma implementação opt-in:

```text
PENNY_DIAGNOSTIC_WRITER_SPECIFIED
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_READY_FOR_WRITER_IMPLEMENTATION
FIXTURES_READY_FOR_WRITER_IMPLEMENTATION
IMPLEMENTATION_NOT_ALLOWED_IN_11_10F
```

A especificação exige que o writer preserve simultaneamente os campos de origem
em 1 rad e os equivalentes 2π com `source`. O campo `volume_multiplier` continua
empírico e fora da conversão geométrica.
