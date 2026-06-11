# LOT/PKN sensitivity reporting (Phase 10.30C)

## Objective

Phase 10.30C adds a reproducible report generator for LOT/PKN sensitivity matrix outputs. The tool consumes the `summary.csv` and `metadata.json` produced by `tools/run_lot_pkn_sensitivity_matrix.py` and writes a compact JSON/Markdown report.

This remains a diagnostic post-processing path. It does not alter C++ runtime behavior, does not create a new physical model, and does not promote any sensitivity factor to calibrated status.

## Tool

```text
tools/report_lot_pkn_sensitivity_matrix.py
```

Example:

```powershell
python tools/report_lot_pkn_sensitivity_matrix.py `
  --summary results/comparison/phase10_30b/buz67d_cgeom_matrix/summary.csv `
  --metadata results/comparison/phase10_30b/buz67d_cgeom_matrix/metadata.json `
  --output-json results/comparison/phase10_30c/sensitivity_report.json `
  --output-md results/comparison/phase10_30c/sensitivity_report.md `
  --legacy-opening-time-s 510 `
  --legacy-max-pressure-Pa 69035836.1743195
```

The legacy target arguments are optional. Without them, the report is baseline-relative.

## Outputs

The report includes:

- `matrix_id`;
- scenario count;
- baseline scenario;
- `best_factor_by_opening_time`;
- `best_factor_by_max_pressure`;
- `best_factor_by_combined_score`;
- ranking table;
- diagnostic caveats.

## Interpretation

For the BUZ-67D versioned C_geom matrix, using documented legacy targets identifies:

| Selection criterion | Diagnostic factor | Scenario |
|---|---:|---|
| Opening time | 0.75x | `cgeom_075_next_step` |
| Maximum pressure | 0.60x | `cgeom_060_next_step` |
| Combined score | 0.75x | `cgeom_075_next_step` |

These are reporting results, not automatic calibration. The factor that best approximates a metric must not be promoted to a validated physical parameter without independent criteria.

## Caveats

- The report is generated from local `results/` artifacts; those artifacts are not versioned.
- Modern-refined sensitivity remains separate from strict LOT_Tese legacy-equivalence.
- A best factor by score is a diagnostic ranking, not a solver parameter update.
- The report generator is Python post-processing, not runtime solver logic.
