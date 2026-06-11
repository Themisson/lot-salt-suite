# Phase 11.7C selected non-PKN model YAML/IO specification

## Resumo executivo

A Fase 11.7C especifica o contrato YAML/IO preliminar para o modelo
`penny_shaped`, selecionado na Fase 11.7A e auditado matematicamente na Fase
11.7B.

Esta fase nao altera parser, schema oficial, runtime C++ ou casos de validacao.
Ela cria uma fixture versionada e um validador externo para congelar o contrato
minimo antes de qualquer implementacao.

```text
status = SELECTED_MODEL_YAML_IO_SPECIFIED
selected_track = PENNY_SHAPED
schema_status = SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA
recommended_next_phase = PHASE11_8A_MINIMAL_SELECTED_NON_PKN_MODEL
```

## Escopo

O contrato cobre apenas o nucleo isolado diagnosticado na 11.7B:

- abertura maxima penny-shaped `opening_m`;
- raio de fratura `radius_m`;
- `pressure_factor = pw / sigmaTheta`;
- `fracture_volume_proxy_m3`.

Ele nao cobre APB completo, sal, Zamora, runtime BUZ29, equivalencia legado ou
validacao fisica.

## Estrutura YAML proposta

```yaml
phase: 11.7C
selected_track: PENNY_SHAPED
fracture_model:
  type: penny_shaped
  status: SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA
  units: SI_with_minutes_for_legacy_formula
  elasticity:
    young_modulus:
      value: 5.71e6
      unit: Pa
    poisson_ratio:
      value: 0.36
      unit: dimensionless
  fluid:
    viscosity:
      value: 180.0
      unit: Pa_min
  injection:
    flow_rate:
      value: 0.05
      unit: m3_min
  initiation:
    elapsed_since_opening:
      value: 1.0
      unit: min
    wellbore_pressure:
      value: 6.7e7
      unit: Pa
    sigma_theta_compression_positive:
      value: 6.6e7
      unit: Pa
  legacy_options:
    volume_multiplier: 10.0
    pressure_factor: pw_over_sigma_theta
  expected_outputs:
    - opening_m
    - radius_m
    - pressure_factor
    - fracture_volume_proxy_m3
```

## Entradas obrigatorias

| Campo | Unidade | Origem | Observacao |
|---|---|---|---|
| `young_modulus` | Pa | rocha ativa | Equivale a `E`. |
| `poisson_ratio` | dimensionless | rocha ativa | Equivale a `nu`. |
| `viscosity` | Pa_min | fluido LOT | Mantem unidade temporal legada em minutos. |
| `flow_rate` | m3_min | injecao | Equivale a `Qinj`. |
| `elapsed_since_opening` | min | criterio de abertura | Equivale a `t - firstTimePwExceedsSigmaMin`. |
| `wellbore_pressure` | Pa | pressao de poco/anular | Equivale a `pw`. |
| `sigma_theta_compression_positive` | Pa | criterio sigmaTheta | Compressao positiva. |
| `volume_multiplier` | - | legado | Fator `10` explicito, nao implicito. |

## Saidas obrigatorias

| Saida | Unidade | Formula auditada |
|---|---|---|
| `opening_m` | m | `3.65 * ((mu^2 * Qinj^3) / E'^2)^(1/9) * time^(1/9)` |
| `radius_m` | m | `0.572 * ((E' * Qinj^3) / mu)^(1/9) * time^(4/9)` |
| `pressure_factor` | - | `pw / sigmaTheta` |
| `fracture_volume_proxy_m3` | m3 | `volume_multiplier * (opening_m/2)^2 * radius_m * pi * pressure_factor` |

## Regras de validacao da fixture

O validador da 11.7C exige:

- `selected_track = PENNY_SHAPED`;
- `fracture_model.type = penny_shaped`;
- unidades explicitas para todos os campos dimensionais;
- `legacy_options.volume_multiplier` explicito;
- todas as saidas obrigatorias presentes.

Classificacoes:

```text
SELECTED_MODEL_YAML_SPEC_VALID
SELECTED_MODEL_YAML_SPEC_PARTIAL
SELECTED_MODEL_YAML_SPEC_INVALID
SELECTED_MODEL_YAML_SPEC_INCONCLUSIVE
```

## Status de runtime

```text
SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA
```

Esta especificacao ainda nao e aceita pelo parser principal. A proxima fase pode
implementar um nucleo C++ isolado usando os mesmos nomes conceituais, sem
conectar automaticamente ao LOT/PKN ou ao CLI.

## Caveats

- Nao ha validacao BUZ29 nesta fase.
- Nao ha equivalencia fisica com LOT_Tese.
- Nao ha schema oficial alterado.
- A unidade `Pa_min` e deliberada para preservar a forma legada auditada.
- O fator `10` continua explicito e diagnostico.
