# Fase 11.10E — fixtures de saída diagnóstica PennyShaped

## Resumo executivo

A Fase 11.10E materializa o contrato de saída axissimétrico de 1 rad definido
na Fase 11.10D em fixtures pequenos, versionados e verificáveis.

Status:

```text
PHASE11_10E_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_DEFINED
PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID
FIXTURE_ONLY_NO_RUNTIME_WRITER
IMPLEMENTATION_NOT_ALLOWED_IN_11_10E
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_MATERIALIZED_AS_FIXTURE
```

Esta fase não implementa writer C++, não altera runtime, não executa
BUZ29-PENNY e não declara validação física. Ela apenas define o formato
esperado para uma futura saída diagnóstica PennyShaped.

## Fixtures criados

```text
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.json
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.csv
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_metadata.json
```

Os arquivos representam uma saída mínima com:

- base interna `axisymmetric_1rad`;
- fator geométrico explícito `2π`;
- `volume_multiplier` preservado como empírico;
- proxy de volume de fratura em 1 rad;
- equivalente 2π separado e rastreado por campo `source`;
- volume sólido em 1 rad e equivalente 2π;
- flags explícitas de não validação física, não equivalência legada e uso
  apenas diagnóstico.

## Contrato materializado

| Campo | Valor |
|---|---:|
| `axisymmetric_angle_rad` | `1.0` |
| `volume_conversion_factor_1rad_to_2pi` | `6.283185307179586` |
| `volume_multiplier` | `10.0` |
| `volume_multiplier_is_2pi` | `false` |
| `fracture_volume_proxy_1rad_m3` | `0.5` |
| `fracture_volume_equivalent_2pi_m3` | `3.141592653589793` |
| `solid_volume_1rad_m3` | `10.0` |
| `solid_volume_equivalent_2pi_m3` | `62.83185307179586` |

As conversões verificadas são:

```text
fracture_volume_equivalent_2pi_m3 =
  fracture_volume_proxy_1rad_m3 * 2π

solid_volume_equivalent_2pi_m3 =
  solid_volume_1rad_m3 * 2π
```

O campo `volume_multiplier = 10.0` não participa dessas conversões e permanece
classificado como:

```text
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
```

## Validador

A fase adiciona:

```text
tools/validate_phase11_10e_penny_output_fixtures.py
```

O validador confere:

- presença dos campos obrigatórios em JSON e CSV;
- `axisymmetric_angle_rad == 1.0`;
- `volume_conversion_factor_1rad_to_2pi == 2π`;
- consistência numérica entre JSON e CSV;
- fontes obrigatórias para equivalentes 2π;
- `volume_multiplier_is_2pi == false`;
- `physically_validated == false`;
- `legacy_equivalent == false`;
- `active_simulation_case == false`;
- presença dos caveats obrigatórios.

## Caveats obrigatórios

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
IMPLEMENTATION_NOT_ALLOWED_IN_11_10E
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
DIAGNOSTIC_ONLY
```

## O que a fase não faz

A Fase 11.10E não:

- implementa writer C++;
- altera `PennyShapedModel`;
- altera `PennyShapedDiagnosticAdapter`;
- altera parser, schema, CLI ou `lot-sim`;
- executa BUZ29-PENNY;
- transforma o fixture em caso ativo;
- declara equivalência com o LOT_Tese;
- valida fisicamente volume, pressão, abertura ou ruptura.

## Próxima fase recomendada

```text
PHASE11_10F_SPECIFY_PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION
```

A próxima fase pode especificar como um writer diagnóstico opt-in consumiria
esse contrato. A implementação ainda deve permanecer separada do fluxo LOT/PKN
padrão e preservar as flags de diagnóstico até existir validação física
dedicada.

## Resultado da Fase 11.10F

A Fase 11.10F consumiu estas fixtures como contrato de entrada para a
especificação do writer futuro:

```text
PENNY_DIAGNOSTIC_WRITER_SPECIFIED
FIXTURES_READY_FOR_WRITER_IMPLEMENTATION
IMPLEMENTATION_NOT_ALLOWED_IN_11_10F
RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F
```

A especificação resultante está em
`docs/80_penny_diagnostic_writer_spec.md` e define a próxima etapa provável:

```text
PHASE11_10G_IMPLEMENT_PENNY_DIAGNOSTIC_WRITER_OPT_IN
```
