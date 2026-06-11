# BUZ-67D C_geom x sink_timing Sensitivity (Phase 11.5B)

## Executive Summary

Phase 11.5B adds a two-factor modern-refined diagnostic matrix for BUZ-67D,
crossing equivalent geometric compliance (`C_geom`) with fracture sink timing.
The study is executed through the canonical `study_id` route and verified with
the LOT-PKN study result verifier.

A matriz C_geom x sink_timing quantifica efeitos diagnosticos de compliance e
temporizacao do sink. Ela nao estabelece calibracao fisica nem equivalencia
estrita com o legado.

## Objective

The goal is to separate, without changing solver behavior:

- the effect of `C_geom` on pressure scale and opening chronology;
- the effect of `sink_timing` on the positive sink delay;
- the interaction between compliance and sink timing in the current
  modern-refined BUZ-67D diagnostic route.

## Matrix

The versioned matrix is:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_sink_timing_matrix_v2.yaml
```

The registered study is:

```text
buz67d_cgeom_sink_timing_sensitivity_v2
```

The matrix uses the same modern-refined base case as the previous v2 studies:

```text
cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
```

## Factors

| C_geom factor | sink_timing |
|---:|---|
| 0.60 | same_step |
| 0.60 | next_step |
| 0.75 | same_step |
| 0.75 | next_step |
| 1.00 | same_step |
| 1.00 | next_step |
| 1.25 | same_step |
| 1.25 | next_step |

All scenarios are diagnostic only. They do not promote any factor to a
calibrated physical parameter.

## How to Execute

Dry run:

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sink_timing_sensitivity_v2 `
  --output-dir results/comparison/phase11_5b/buz67d_cgeom_sink_timing_dry_run `
  --dry-run
```

Full run:

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sink_timing_sensitivity_v2 `
  --output-dir results/comparison/phase11_5b/buz67d_cgeom_sink_timing `
  --lot-sim build/Debug/lot-sim.exe
```

## How to Verify

```powershell
python tools/verify_lot_pkn_study_results.py `
  --result-dir results/comparison/phase11_5b/buz67d_cgeom_sink_timing `
  --require-report
```

The Phase 11.5B execution returned:

```text
CLASSIFICATION=LOT_PKN_STUDY_RESULTS_OK
ERRORS=0
WARNINGS=0
```

## Analysis Tool

The phase-specific analyzer is:

```text
tools/analyze_phase11_5b_cgeom_sink_timing.py
```

It reports:

- per-scenario opening time, sink delay, maximum pressure, and final pressure;
- comparisons with the same `C_geom` and varying `sink_timing`;
- comparisons with the same `sink_timing` and varying `C_geom`;
- mean next-step minus same-step deltas.

Observed classification:

```text
CGEOM_SINK_TIMING_MATRIX_ANALYZED
```

Observed high-level effects:

```text
mean_opening_delta_next_minus_same_s = 0.0
mean_sink_delay_delta_next_minus_same_s = 30.0
mean_max_pressure_delta_next_minus_same_Pa = 1821956.0465000253
sink_delay_reproduced_where_expected = true
```

## Interpretation

Within this matrix, `sink_timing` controls whether the positive sink appears in
the same step or the following 30 s step. For paired cases with the same
`C_geom`, switching from `same_step` to `next_step` preserves the opening time
but increases the observed sink delay by 30 s.

The opening chronology remains mainly governed by the compliance factor in this
diagnostic setup:

| Scenario | Opening time (s) | Sink delay (s) | Max pressure (Pa) |
|---|---:|---:|---:|
| `cgeom_060_same_step` | 420 | 0 | 65847565.962323785 |
| `cgeom_060_next_step` | 420 | 30 | 68856439.09995255 |
| `cgeom_075_same_step` | 510 | 0 | 65668756.7184024 |
| `cgeom_075_next_step` | 510 | 30 | 68102290.56498069 |
| `cgeom_100_same_step` | 660 | 0 | 65485976.41080395 |
| `cgeom_100_next_step` | 660 | 30 | 67331393.612597 |
| `cgeom_125_same_step` | not opened | n/a | 63888110.8869083 |
| `cgeom_125_next_step` | not opened | n/a | 63888110.8869083 |

## Caveats

- All rankings and effects are diagnostic only; not physical calibration.
- The matrix separates `C_geom` and `sink_timing` effects without changing
  solver behavior.
- This is modern-refined analysis, not strict LOT_Tese legacy-equivalence.
- The current study summary does not export fracture and leakoff volume maxima
  as separate columns, so those remain unavailable in the phase analyzer.

## Recommended Next Phase

The next useful phase is to consolidate the two 11.5 studies into a compact
modern-refined interpretation package or extend the canonical study tooling so
summary CSVs expose volume maxima explicitly for future sensitivity analyses.
