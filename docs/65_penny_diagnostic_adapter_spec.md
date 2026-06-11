# Fase 11.8C — especificacao do adapter diagnostico PennyShaped

## Resumo executivo

A Fase 11.8C especifica o contrato minimo para um adapter diagnostico opt-in
em torno do nucleo `PennyShapedModel`. A fase nao altera runtime, parser,
schema, CLI, LOT-PKN, C++ ou CMake. O objetivo e preparar uma interface clara
para a Fase 11.8D, mantendo a rota isolada, sintetica e sem validacao BUZ29.

Status da fase:

```text
PENNY_ADAPTER_SPEC_VALID
```

## Escopo

O adapter especificado deve consumir exatamente os campos ja implementados no
kernel `PennyShapedInput`:

| Campo | Unidade | Origem |
|---|---:|---|
| `young_modulus_Pa` | Pa | propriedade elastica |
| `poisson_ratio` | adimensional | propriedade elastica |
| `viscosity_Pa_min` | Pa.min | fluido diagnostico |
| `flow_rate_m3_min` | m3/min | injecao diagnostica |
| `elapsed_since_opening_min` | min | tempo desde abertura |
| `wellbore_pressure_Pa` | Pa | pressao de poco/anular |
| `sigma_theta_compression_positive_Pa` | Pa | criterio sigma-theta externo |
| `volume_multiplier` | adimensional | multiplicador legado explicito |

Saidas esperadas:

```text
plane_strain_modulus_Pa
opening_m
radius_m
pressure_factor
fracture_volume_proxy_m3
```

## Fixture versionada

A fixture versionada esta em:

```text
tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml
```

Ela representa um caso sintetico de contrato, nao um caso BUZ29 e nao uma
entrada oficial do parser `lot-sim`.

## Semantica do adapter futuro

O adapter da Fase 11.8D deve:

1. receber um bloco diagnostico com os campos acima;
2. mapear diretamente para `lss::lot::PennyShapedInput`;
3. chamar `evaluate_penny_shaped_model`;
4. retornar `PennyShapedResult` e metadados de diagnostico;
5. preservar caveats de uso;
6. nao chamar `PknRunner`;
7. nao alterar `lot-sim run --mode lot-pkn`.

## Caveats obrigatorios

```text
Diagnostic adapter only.
Not BUZ29 validation.
Not legacy equivalence.
```

A especificacao 11.8C nao valida BUZ29, nao estabelece equivalencia com o
LOT_Tese e nao transforma o modelo penny-shaped em rota runtime oficial.

## Proxima fase

A proxima fase recomendada e:

```text
PHASE11_8D_PENNY_DIAGNOSTIC_ADAPTER_IMPLEMENTATION
```

Essa fase pode criar o adapter C++ opt-in, com testes Catch2 dedicados, ainda
sem parser, schema ou CLI.
