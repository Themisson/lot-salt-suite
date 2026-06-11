# 54 - BUZ-67D extended C_geom sensitivity

## Resumo executivo

A Fase 11.5A cria e executa uma matriz v2 ampliada de sensibilidade de
`C_geom` para o BUZ-67D `modern-refined`.

Os fatores de C_geom avaliados nesta matriz são variações diagnósticas do
baseline modern-refined. Eles não constituem calibração física automática nem
validação independente do modelo.

## Matriz criada

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_extended_matrix_v2.yaml
```

```text
matrix_id: buz67d_modern_refined_cgeom_extended_v2
schema_version: 2
base_case: cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
```

## Study ID

```text
buz67d_cgeom_extended_sensitivity_v2
```

O estudo foi registrado em:

```text
cases/validation/sensitivity/studies_index.yaml
```

## Fatores avaliados

```text
0.50, 0.55, 0.60, 0.65, 0.70, 0.75,
0.80, 0.85, 0.90, 1.00, 1.10, 1.25
```

Todos os cenários usam:

```text
sink_timing = next_step
```

## Como executar

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_extended_sensitivity_v2 `
  --output-dir results/comparison/phase11_5a/buz67d_cgeom_extended `
  --lot-sim build/Debug/lot-sim.exe
```

## Como verificar

```powershell
python tools/verify_lot_pkn_study_results.py `
  --result-dir results/comparison/phase11_5a/buz67d_cgeom_extended `
  --require-report
```

## Como analisar

```powershell
python tools/analyze_phase11_5a_cgeom_extended.py `
  --summary results/comparison/phase11_5a/buz67d_cgeom_extended/summary.csv `
  --metadata results/comparison/phase11_5a/buz67d_cgeom_extended/metadata.json `
  --output-json results/comparison/phase11_5a/cgeom_extended_analysis.json `
  --output-md results/comparison/phase11_5a/cgeom_extended_analysis.md
```

## Resultado observado

O run local da fase executou 12 cenários e foi verificado com:

```text
LOT_PKN_STUDY_RESULTS_OK
CGEOM_EXTENDED_SENSITIVITY_ANALYZED
```

Ranking diagnóstico observado:

```text
best_by_opening_time  = cgeom_075_next_step
best_by_max_pressure  = cgeom_055_next_step
best_by_combined_score = cgeom_075_next_step
```

## Interpretação

A resposta de abertura permanece fortemente sensível a `C_geom`. O cenário
`0.75x` reproduz a abertura alvo diagnóstica de `510 s`, enquanto fatores mais
baixos abrem antes e fatores maiores deslocam ou impedem a abertura na janela.

Esse resultado é ranking operacional de sensibilidade. Ele não deve ser
promovido automaticamente a parâmetro calibrado.

## Próxima fase recomendada

A próxima etapa é a Fase 11.5B: matriz cruzada `C_geom x sink_timing`, para
separar o efeito da compliance do efeito da temporização do sink.
