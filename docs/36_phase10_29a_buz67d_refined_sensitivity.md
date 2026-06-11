# Phase 10.29A BUZ-67D refined modern-refined sensitivity

## Resumo executivo

A Fase 10.29A refinou a matriz BUZ-67D `modern-refined` ao redor do achado da
10.28C: `C_geom = 0.75x` aproximou a abertura legada de `510 s` mantendo
pressão máxima próxima. A nova matriz variou `constant_geometric` entre `0.60x`
e `1.00x`, preservando `sink_timing = next_step` e a série refinada de
`sigmaTheta`.

Classificações:

```text
REFINED_SENSITIVITY_COMPLETED
REFINED_SENSITIVITY_BEST_DIAGNOSTIC_FACTOR_FOUND
REFINED_SENSITIVITY_OPENING_DOMINATED_BY_COMPLIANCE
```

## Objetivo

Medir a sensibilidade diagnóstica da cronologia de abertura e da escala de
pressão em relação a `C_geom`, sem promover o melhor fator a calibração
automática, sem alterar solver e sem misturar `modern-refined` com
`legacy-equivalence`.

## Cenários executados

| Cenário | C_geom factor | C_geom 1/Pa | sink_timing |
|---|---:|---:|---|
| cgeom_060 | `0.60x` | `1.1143180163166003e-8` | `next_step` |
| cgeom_065 | `0.65x` | `1.2071778510096503e-8` | `next_step` |
| cgeom_070 | `0.70x` | `1.3000376857027003e-8` | `next_step` |
| cgeom_075 | `0.75x` | `1.3928975203957504e-8` | `next_step` |
| cgeom_080 | `0.80x` | `1.4857573550888005e-8` | `next_step` |
| cgeom_085 | `0.85x` | `1.5786171897818503e-8` | `next_step` |
| cgeom_090 | `0.90x` | `1.6714770244749006e-8` | `next_step` |
| baseline | `1.00x` | `1.8571966938610005e-8` | `next_step` |

## Métricas principais

Referências diagnósticas usadas:

```text
legacy_opening_time_s = 510.0
legacy_max_pressure_Pa = 69035836.1743195
```

| C_geom factor | max_pressure_Pa | rel. error max pressure | opening_s | opening error_s | sink_delay_s | combined_score |
|---:|---:|---:|---:|---:|---:|---:|
| `0.60` | `68856439.09995255` | `-0.002598607973892992` | `420.0` | `-90.0` | `30.0` | `0.62598607973893` |
| `0.65` | `68568329.10555169` | `-0.006771947653206275` | `450.0` | `-60.0` | `30.0` | `0.46771947653206275` |
| `0.70` | `68319446.54120484` | `-0.010377068966119861` | `480.0` | `-30.0` | `30.0` | `0.30377068966119863` |
| `0.75` | `68102290.56498069` | `-0.013522623336980564` | `510.0` | `0.0` | `30.0` | `0.13522623336980563` |
| `0.80` | `67911158.10526186` | `-0.01629122107274497` | `540.0` | `30.0` | `30.0` | `0.3629122107274497` |
| `0.85` | `67741635.70627344` | `-0.018746792097630825` | `570.0` | `60.0` | `30.0` | `0.5874679209763083` |
| `0.90` | `67590254.51195076` | `-0.02093958359131867` | `600.0` | `90.0` | `30.0` | `0.8093958359131866` |
| `1.00` | `67331393.612597` | `-0.02468924338685035` | `660.0` | `150.0` | `30.0` | `1.2468924338685035` |

## Melhores fatores diagnósticos

| Critério | Fator | Interpretação |
|---|---:|---|
| abertura | `0.75x` | Reproduz abertura diagnóstica em `510 s`. |
| pressão máxima | `0.60x` | Aproxima melhor a pressão máxima legada isoladamente. |
| score combinado | `0.75x` | Melhor compromisso pela métrica diagnóstica adotada. |

O `combined_score` usado nesta fase é:

```text
combined_score = abs(opening_time_error_s) / 150
               + abs(relative_error_max_pressure) / 0.10
```

## Interpretação técnica

A cronologia de abertura é fortemente controlada pela compliance equivalente
diagnóstica. Na matriz refinada, reduzir `C_geom` antecipa a abertura em
degraus de `30 s`, enquanto aumentar `C_geom` atrasa a abertura e reduz a
pressão máxima.

O fator de compliance que melhor aproxima a abertura legada é um resultado de
sensibilidade diagnóstica. Ele não deve ser promovido automaticamente a
parâmetro calibrado nem usado como validação física sem critérios adicionais.

## Limitações

- `constant_geometric` permanece modelo diagnóstico equivalente.
- A matriz não implementa modelo mecânico de casing/formação.
- A matriz não consome APBSalt1D nem `SaltWallStressDiagnostics`.
- A abertura em `510 s` no fator `0.75x` não estabelece regressão
  `legacy-equivalence`.
- Os gráficos e CSVs em `results/comparison/phase10_29a/` não são versionados.

## Recomendação para 10.29B

Criar uma infraestrutura genérica de sensitivity runner para evitar duplicação
entre comparadores de fase. O runner deve validar/rodar YAMLs de matriz,
coletar `timeseries.csv`, emitir `summary.csv`/`metadata.json`, e deixar claro
que o resultado é diagnóstico.

## Atualização 10.30A

A Fase 10.30A transformou os cenários desta sensibilidade em matriz YAML
versionada:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml
```

Isso permite reproduzir a matriz pelo runner genérico sem usar scripts
específicos da Fase 10.29A. A interpretação permanece igual: sensibilidade
diagnóstica, não calibração automática.
