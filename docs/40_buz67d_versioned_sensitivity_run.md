# BUZ-67D versioned sensitivity run (Phase 10.30B)

## Executive summary

Phase 10.30B executed the versioned BUZ-67D modern-refined C_geom matrix created in Phase 10.30A through the generic LOT/PKN sensitivity runner. The run is diagnostic only. It verifies that the versioned matrix can be executed reproducibly and that the generated `summary.csv` and `metadata.json` contain the expected scenarios and metrics.

The phase does not create a physical calibration, does not change the LOT/PKN solver, and does not mix modern-refined validation with legacy-equivalence regression.

## Command

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml `
  --output-dir results/comparison/phase10_30b/buz67d_cgeom_matrix `
  --lot-sim build/Debug/lot-sim.exe
```

The outputs under `results/comparison/phase10_30b/` are local artifacts and are not versioned.

## Matrix status

| Item | Value |
|---|---|
| Matrix ID | `buz67d_modern_refined_cgeom_sensitivity` |
| Scenario count | 10 |
| Baseline scenario | `cgeom_100_next_step` |
| Required diagnostic scenario | `cgeom_075_next_step` |
| Same-step comparison | `cgeom_100_same_step` |
| Verification classification | `VERSIONED_SENSITIVITY_RUN_OK` |

## Observed metrics

| Scenario | C_geom factor | Sink timing | Opening time (s) | Sink delay (s) | Max pressure (MPa) |
|---|---:|---|---:|---:|---:|
| `cgeom_060_next_step` | 0.60 | next_step | 420 | 30 | 68.856 |
| `cgeom_065_next_step` | 0.65 | next_step | 450 | 30 | 68.568 |
| `cgeom_070_next_step` | 0.70 | next_step | 480 | 30 | 68.319 |
| `cgeom_075_next_step` | 0.75 | next_step | 510 | 30 | 68.102 |
| `cgeom_080_next_step` | 0.80 | next_step | 540 | 30 | 67.911 |
| `cgeom_085_next_step` | 0.85 | next_step | 570 | 30 | 67.742 |
| `cgeom_090_next_step` | 0.90 | next_step | 600 | 30 | 67.590 |
| `cgeom_100_next_step` | 1.00 | next_step | 660 | 30 | 67.331 |
| `cgeom_125_next_step` | 1.25 | next_step | not opened | not applicable | 63.888 |
| `cgeom_100_same_step` | 1.00 | same_step | 660 | 0 | 65.486 |

## Interpretation

The versioned run preserves the Phase 10.28C/10.29A observation: reducing the diagnostic constant geometric compliance shifts opening earlier, and `0.75x` reaches the legacy opening time of 510 s in this controlled sensitivity matrix. This remains a sensitivity result, not an automatic calibration and not a physical validation.

The same-step scenario confirms that changing sink timing affects the sink delay and pressure response, but does not move the fracture initiation time for the `1.0x` compliance case.

## Caveats

- The matrix is modern-refined, not strict LOT_Tese legacy-equivalence.
- Results under `results/` are reproducible local artifacts, not versioned files.
- The 0.75x scenario is a diagnostic sensitivity point and must not be promoted automatically to a calibrated parameter.
- APBSalt1D metadata remains metadata-only until spatial sigmaTheta sampling exists.

## Phase 10.30C reporting

Phase 10.30C adds `tools/report_lot_pkn_sensitivity_matrix.py` to turn this
run's `summary.csv` and `metadata.json` into a reproducible JSON/Markdown
report. For the documented BUZ-67D legacy targets, the report keeps the same
diagnostic interpretation:

- best opening-time factor: `0.75x`;
- best maximum-pressure factor: `0.60x`;
- best combined-score factor: `0.75x`.

These are report rankings, not automatic calibration.
