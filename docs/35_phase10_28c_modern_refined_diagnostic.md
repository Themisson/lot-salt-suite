# Phase 10.28C modern-refined diagnostic

## Resumo executivo

A Fase 10.28C executou a rota B definida pela Fase 10.28B:

```text
PHASE10_28C_SENSITIVITY_MATRIX_EXECUTED
classification = PHASE10_28C_SENSITIVITY_MATRIX_RUN_OK
route = sensitivity
```

A matriz usa BUZ-67D `modern-refined` com quatro cenários pequenos e
rastreáveis. Ela não é `legacy-equivalence`, não consome geometria APBSalt1D e
não valida fratura física. O objetivo é medir sensibilidade diagnóstica a
`constant_geometric` e `sink_timing`.

## Rota executada

A rota additional well foi bloqueada na Fase 10.28B porque BUZ-29D não estava
pronto como caso PKN moderno completo. A Fase 10.28C executou a matriz BUZ-67D
`modern-refined`.

## Cenários

| Cenário | YAML | C_geom factor | sink_timing | sigmaTheta |
|---|---|---:|---|---|
| S0 baseline | `cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml` | `1.0x` | `next_step` | refined time-series |
| S1 lower compliance | `cases/validation/sensitivity/buz67d_modern_refined_sens_cgeom_075.yaml` | `0.75x` | `next_step` | refined time-series |
| S2 higher compliance | `cases/validation/sensitivity/buz67d_modern_refined_sens_cgeom_125.yaml` | `1.25x` | `next_step` | refined time-series |
| S3 same_step | `cases/validation/sensitivity/buz67d_modern_refined_sens_same_step.yaml` | `1.0x` | `same_step` | refined time-series |

## Resultados por cenário

| Cenário | max_pressure_Pa | fracture_initiation_time_s | first_sink_positive_time_s | sink_delay_s | delta_vs_baseline_Pa |
|---|---:|---:|---:|---:|---:|
| baseline | `67331393.612597` | `660.0` | `690.0` | `30.0` | `0.0` |
| cgeom_075 | `68102290.56498069` | `510.0` | `540.0` | `30.0` | `770896.9523836821` |
| cgeom_125 | `63888110.8869083` | not opened | not available | not available | `-3443282.7256887034` |
| same_step | `65485976.41080395` | `660.0` | `660.0` | `0.0` | `-1845417.2017930523` |

## Sensibilidade observada

A matriz confirma que a rota `modern-refined` é sensível à compliance
diagnóstica:

- `0.75x C_geom` aumenta a pressão máxima e move a abertura para `510 s`;
- `1.25x C_geom` reduz a pressão máxima e não abre na janela executada;
- `same_step` preserva a abertura em `660 s`, mas remove o atraso de sink;
- o baseline preserva `sink_delay_s = 30 s`.

O cenário `0.75x` não deve ser promovido a calibração automática. Ele mostra
que o tempo de abertura é sensível à compliance equivalente, mas
`constant_geometric` continua diagnóstico e não um modelo mecânico validado.

## Gráficos locais

Os gráficos foram gerados localmente em `results/comparison/phase10_28c/` e
não devem ser versionados:

```text
sensitivity_pressure_vs_time.png
sensitivity_volume_pressure.png
sensitivity_max_pressure_bar.png
sensitivity_opening_time_bar.png
sensitivity_sink_delay_bar.png
```

## Limitações

- A matriz não compara BUZ-29D.
- A matriz não é regressão estrita contra `LOT_Tese`.
- A geometria APBSalt1D continua metadata-only/bloqueada.
- `pressure_source/timing` permanece subordinado ao gate geométrico.
- A aproximação de `510 s` no cenário `0.75x` é diagnóstico de sensibilidade,
  não validação física nem nova calibração padrão.

## Recomendação

A próxima fase deve decidir entre:

- expandir a matriz `modern-refined` com mais eixos controlados;
- preparar figuras/relatório de comparação para tese/artigo;
- auditar BUZ-29D em uma fase própria antes de criar YAML moderno;
- manter `legacy-equivalence` separada até existir consumo real APBSalt1D.
