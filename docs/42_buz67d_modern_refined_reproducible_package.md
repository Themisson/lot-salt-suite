# BUZ-67D modern-refined reproducible package (Phase 10.31A)

## Executive summary

Phase 10.31A packages the BUZ-67D `modern-refined` sensitivity workflow into a reproducible end-to-end procedure. The package validates the minimum LOT/PKN cases, validates the versioned BUZ-67D sensitivity matrix, runs the matrix, and generates JSON/Markdown sensitivity reports.

Este pacote é reproduzível, mas os artefatos em results/ são locais e não devem ser commitados. A matriz é diagnóstica; o melhor fator por métrica não deve ser promovido automaticamente a calibração ou validação física.

## Prerequisites

- CMake and a C++20 compiler supported by the repository.
- Python with the repository test dependencies.
- A built `lot-sim` executable, normally at `build/Debug/lot-sim.exe` on Windows Debug builds.

## Build

```bash
cmake -S . -B build
cmake --build build --config Debug -j
```

## Validate minimum regressions

```bash
build/Debug/lot-sim.exe validate --case cases/validation/lot_pkn_minimal.yaml
build/Debug/lot-sim.exe validate --case cases/validation/lot_pkn_with_leakoff.yaml
build/Debug/lot-sim.exe validate --case cases/lot_tese_migrated/buz67d_pkn.yaml
```

## Run the package

```bash
python tools/run_buz67d_modern_refined_package.py \
  --lot-sim build/Debug/lot-sim.exe \
  --output-dir results/comparison/buz67d_modern_refined_package
```

The tool orchestrates:

1. minimum case validation;
2. validation of all cases referenced by `cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml`;
3. execution of `tools/run_lot_pkn_sensitivity_matrix.py`;
4. report generation through `tools/report_lot_pkn_sensitivity_matrix.py`;
5. metadata and command logging under the output directory.

## Dry-run

```bash
python tools/run_buz67d_modern_refined_package.py \
  --output-dir results/comparison/phase10_31a/dry_run_package \
  --dry-run
```

`--dry-run` writes `package_metadata.json` and `run_commands.txt` without requiring `lot-sim` to exist.

## Manual matrix execution

```bash
python tools/run_lot_pkn_sensitivity_matrix.py \
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml \
  --output-dir results/comparison/buz67d_cgeom_sensitivity \
  --lot-sim build/Debug/lot-sim.exe
```

## Manual report generation

```bash
python tools/report_lot_pkn_sensitivity_matrix.py \
  --summary results/comparison/buz67d_cgeom_sensitivity/summary.csv \
  --metadata results/comparison/buz67d_cgeom_sensitivity/metadata.json \
  --output-json results/comparison/buz67d_cgeom_sensitivity/report.json \
  --output-md results/comparison/buz67d_cgeom_sensitivity/report.md
```

For BUZ-67D legacy-target ranking, add:

```bash
--legacy-opening-time-s 510 --legacy-max-pressure-Pa 69035836.1743195
```

## Local outputs

The package writes local artifacts under the selected `results/` directory:

- `package_metadata.json`;
- `run_commands.txt`;
- `sensitivity_summary.csv`;
- `sensitivity_metadata.json`;
- `sensitivity_report.json`;
- `sensitivity_report.md`;
- `runs/<scenario_id>/timeseries.csv`;
- `runs/<scenario_id>/result.json`.

None of these files should be committed.

## Scenario interpretation

| Scenario | Interpretation |
|---|---|
| `cgeom_075_next_step` | Diagnostic sensitivity point that opens at 510 s in the current matrix. |
| `cgeom_100_next_step` | Modern-refined baseline, opening at 660 s in the current matrix. |
| `cgeom_125_next_step` | Higher compliance case that does not open within the current window. |
| `cgeom_100_same_step` | Sink-timing comparison, not a new physical model. |

The sensitivity is diagnostic. The `0.75x` factor is not automatic calibration, is not physical validation, and remains separate from strict LOT_Tese `legacy-equivalence`.

## Common issues

| Symptom | Likely cause | Action |
|---|---|---|
| `lot-sim executable not found` | Project was not built or path differs. | Build first or pass `--lot-sim <path>`. |
| Missing matrix file | Running from another directory. | Run from repository root or pass `--matrix <path>`. |
| Report generation fails | `summary.csv`/`metadata.json` not generated. | Run the matrix first or use `--only-report` with existing files. |
| Outputs appear in Git status | `results/` is not ignored locally or files were copied elsewhere. | Do not stage generated outputs. |

## Checklist for another computer

1. Clone the repository.
2. Build with CMake.
3. Confirm `build/Debug/lot-sim.exe` or pass a custom `--lot-sim`.
4. Run the package command.
5. Inspect `sensitivity_report.md`.
6. Keep all `results/` artifacts local.
7. Do not interpret best factors as calibration without a later validation phase.

## Phase 10.31B handoff

Phase 10.31B records this package as the primary reproducible artifact of Phase
10 and opens Stage 11 with a parametric-infrastructure focus.

Status:

```text
PHASE10_CLOSED_READY_FOR_STAGE11
STAGE11_PARAMETRIC_INFRASTRUCTURE_RECOMMENDED
```

The package remains diagnostic. `C_geom = 0.75x` is not automatic calibration,
and generated `results/` artifacts remain local and unversioned.

## Stage 11 study registration

Phase 11.1B registers the BUZ-67D C_geom matrix as a sensitivity study:

```text
cases/validation/sensitivity/studies_index.yaml
```

Study id:

```text
buz67d_cgeom_sensitivity
```

The registration is metadata/discovery infrastructure. It does not duplicate the
matrix and does not change the package runner.

## Stage 11 canonical study command

Phase 11.3C adds the study-oriented command:

```text
tools/run_lot_pkn_study.py
```

For the BUZ-67D C_geom v2 study:

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --lot-sim build/Debug/lot-sim.exe
```

This supersedes manual orchestration for routine local diagnostics, while the
older package remains documented for historical reproducibility.
