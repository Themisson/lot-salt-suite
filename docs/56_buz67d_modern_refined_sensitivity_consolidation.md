# BUZ-67D Modern-Refined Sensitivity Consolidation (Phase 11.5C)

## Resumo Executivo

A Fase 11.5C consolida as duas matrizes BUZ-67D modern-refined criadas nas
Fases 11.5A e 11.5B. O objetivo é fechar a interpretação diagnóstica do bloco
BUZ-67D antes da auditoria BUZ29-VISCO-first-well.

A consolidação da 11.5C interpreta sensibilidades diagnósticas do modo BUZ-67D
modern-refined. Ela não transforma fatores de C_geom em calibração física e não
declara equivalência estrita com o legado.

## Estudos Consolidados

| Fase | study_id | Status |
|---|---|---|
| 11.5A | `buz67d_cgeom_extended_sensitivity_v2` | `CGEOM_EXTENDED_SENSITIVITY_ANALYZED` |
| 11.5B | `buz67d_cgeom_sink_timing_sensitivity_v2` | `CGEOM_SINK_TIMING_MATRIX_ANALYZED` |

Os resultados são tratados como `DOCUMENTED_PHASE_SUMMARY`, usando os valores
registrados nos documentos e gates versionados das fases anteriores.

## Matriz C_geom Ampliada

A matriz 11.5A avaliou fatores:

```text
0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 1.00, 1.10, 1.25
```

com `sink_timing=next_step`.

Ranking diagnóstico:

```text
best_by_opening_time = cgeom_075_next_step
best_by_max_pressure = cgeom_055_next_step
best_by_combined_score = cgeom_075_next_step
```

## Matriz C_geom x sink_timing

A matriz 11.5B cruzou:

```text
C_geom factors = 0.60, 0.75, 1.00, 1.25
sink_timing = same_step, next_step
```

Resultados principais:

```text
scenario_count = 8
mean_opening_delta_next_minus_same_s = 0.0
mean_sink_delay_delta_next_minus_same_s = 30.0
mean_max_pressure_delta_next_minus_same_Pa = 1821956.0465000253
sink_delay_reproduced_where_expected = true
```

## Interpretação do Efeito de C_geom

`C_geom` controla fortemente a rigidez aparente, a pressão máxima e a cronologia
de abertura no modo modern-refined. Fatores menores aumentam a pressão e tendem
a antecipar a abertura; fatores maiores reduzem a pressão e podem impedir a
abertura na janela simulada.

O resultado C_geom = 0.75x deve permanecer como melhor diagnóstico combinado,
enquanto C_geom = 0.55x aparece como melhor aproximação para pressão máxima na
matriz ampliada. Essa diferença reforça que a escolha de parâmetro depende da
métrica e não deve ser automatizada como calibração física.

## Interpretação do Efeito de sink_timing

`sink_timing` controla principalmente a defasagem do consumo volumétrico
pós-abertura. Na matriz cruzada, trocar `same_step` por `next_step` preserva o
tempo de abertura dos pares com mesmo `C_geom`, mas desloca o sink positivo para
o passo seguinte, reproduzindo o atraso operacional de 30 s.

## Limitações

- Os estudos são modern-refined, não legacy-equivalence.
- Os rankings são diagnósticos, não calibração física.
- A análise não valida fratura física.
- A equivalência estrita com LOT_Tese continua bloqueada por geometria,
  sampling e sigmaTheta runtime.

## Campos Faltantes Para Análises Futuras

Os summaries atuais ainda não expõem explicitamente:

- `fracture_volume_max_m3`;
- `leakoff_volume_max_m3`;
- `fracture_length_max_m`;
- `fracture_width_max_m`;
- `net_pressure_max_Pa`.

Esses campos são candidatos à fase condicional 11.5D, desde que possam ser
agregados sem alterar física ou solver.

## Conclusão

O bloco BUZ-67D modern-refined tem sensibilidade operacional reproduzível por
`study_id`, verificação de resultados e interpretação consolidada. O próximo
passo recomendado é a auditoria BUZ29-VISCO-first-well para decidir se há
compatibilidade com `lot-pkn` ou se modelos não-PKN devem ser planejados.

## Próxima Fase Recomendada

```text
PHASE11_6A_BUZ29_VISCO_FIRST_WELL_AUDIT
```
