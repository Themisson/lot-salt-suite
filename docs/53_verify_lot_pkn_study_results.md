# 53 - Verify LOT/PKN study results

## Objetivo

A Fase 11.4B adiciona:

```text
tools/verify_lot_pkn_study_results.py
```

A ferramenta valida a integridade operacional de um diretório produzido por
`tools/run_lot_pkn_study.py`.

O verificador confirma integridade operacional dos artefatos de resultado. Ele
não valida fisicamente o modelo nem declara equivalência com o legado.

## O que a ferramenta verifica

- existência do diretório de resultados;
- presença de `study_manifest.json`;
- `schema_version == 1`;
- campos obrigatórios do manifesto;
- `run_commands.txt`;
- `summary.csv` e `metadata.json` em execução completa;
- `sensitivity_report.json` e `sensitivity_report.md` quando
  `--require-report` é usado;
- linhas em `summary.csv`;
- JSON válido em `metadata.json`;
- cenários com `id` e `status`;
- cenários falhos em modo normal ou `--strict`.

## Uso

```powershell
python tools/verify_lot_pkn_study_results.py `
  --result-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2
```

Para exigir relatório:

```powershell
python tools/verify_lot_pkn_study_results.py `
  --result-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --require-report
```

Para validar um dry-run:

```powershell
python tools/verify_lot_pkn_study_results.py `
  --result-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --allow-dry-run
```

## Relatórios

Opcionalmente:

```powershell
python tools/verify_lot_pkn_study_results.py `
  --result-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --output-json results/comparison/studies/buz67d_cgeom_sensitivity_v2/verification.json `
  --output-md results/comparison/studies/buz67d_cgeom_sensitivity_v2/verification.md
```

Esses relatórios são artefatos locais em `results/` e não devem ser versionados.

## Classificações

```text
LOT_PKN_STUDY_RESULTS_OK
LOT_PKN_STUDY_RESULTS_DRY_RUN_OK
LOT_PKN_STUDY_RESULTS_PARTIAL
LOT_PKN_STUDY_RESULTS_FAILED
LOT_PKN_STUDY_RESULTS_INVALID_MANIFEST
LOT_PKN_STUDY_RESULTS_MISSING_OUTPUTS
LOT_PKN_STUDY_RESULTS_INCONCLUSIVE
```

## Limitações

O verificador não roda simulações, não compara contra o legado, não valida
fisicamente fratura e não verifica se `results/` foi acidentalmente adicionado
ao Git. Essa última checagem continua sendo gate de fase via `git status` e
`git ls-files results`.

## Uso em 11.5A

A matriz ampliada `buz67d_cgeom_extended_sensitivity_v2` foi verificada com
`--require-report`, produzindo classificação operacional
`LOT_PKN_STUDY_RESULTS_OK`.
