# 50 — Canonical LOT/PKN study runner

## Objetivo

A Fase 11.3C adiciona um comando unico para executar estudos LOT/PKN
registrados por `study_id`:

```text
tools/run_lot_pkn_study.py
```

Ele orquestra:

1. resolucao do estudo no indice;
2. execucao do runner por matriz;
3. geracao de relatorio, quando ha outputs reais;
4. criacao de manifesto local;
5. registro dos comandos de reproducao.

## Relacao com studies_index

O comando usa por padrao:

```text
cases/validation/sensitivity/studies_index.yaml
```

O estudo `buz67d_cgeom_sensitivity_v2` aponta para a matriz v2 BUZ-67D
`modern-refined`. O indice continua sendo metadado versionado; os artefatos
gerados pela execucao continuam em `results/`.

## Como executar um estudo

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --lot-sim build/Debug/lot-sim.exe
```

Para revisar o plano sem rodar simulacoes:

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --dry-run
```

## Opcoes

```text
--studies-index cases/validation/sensitivity/studies_index.yaml
--lot-sim build/Debug/lot-sim.exe
--dry-run
--skip-run
--only-summary
--skip-report
--allow-inactive
```

## Saidas geradas

No `output-dir`, o comando escreve:

```text
study_metadata.json
metadata.json
study_manifest.json
run_commands.txt
sensitivity_report.json
sensitivity_report.md
```

Em `--dry-run`, `sensitivity_report.*` nao e gerado porque nao ha
`summary.csv` real. O manifesto ainda registra o comando de relatorio que seria
executado.

## Manifesto

`study_manifest.json` usa `schema_version: 1` a partir da Fase 11.4A. O schema
informal esta definido em `docs/51_lot_pkn_study_manifest.md`.

`study_manifest.json` inclui:

- `study_id`;
- `study_status`;
- `matrix_path`;
- `matrix_id`;
- `matrix_schema_version`;
- `base_case`;
- `studies_index`;
- `output_dir`;
- `created_at_utc`;
- `command`;
- `commands`;
- `environment`;
- `git`;
- `lot_sim`;
- `outputs`;
- `scenarios`;
- `caveats`.

Em `--dry-run`, o manifesto registra os artefatos planejados e marca
`study_status=dry_run`. Em execucao completa, `study_status=completed` se o
runner produzir `summary.csv`.

## Provenance

A Fase 11.4A adiciona provenance operacional completa ao estudo. O manifesto
registra commit/branch, estado dirty quando disponivel, versao do Python,
plataforma, executavel `lot-sim`, comandos de reproducao e cenarios. Falha em
ler Git nao interrompe a execucao; o manifesto registra caveat.

## Uso em outro computador

1. Clonar o repositorio.
2. Configurar e compilar:

```powershell
cmake -S . -B build
cmake --build build --config Debug -j
```

3. Rodar o estudo:

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --lot-sim build/Debug/lot-sim.exe
```

## Caveat sobre results/

`results/` e artefato local reproduzivel. Ele nao deve ser commitado. A fonte
versionada continua sendo:

```text
cases/validation/sensitivity/studies_index.yaml
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

## Escopo

O comando e infraestrutura operacional de validacao/diagnostico. Ele nao altera
solver, parser, CMake, schemas, casos protegidos ou runtime LOT/PKN.

## Verificação de resultados

A Fase 11.4B adiciona:

```text
tools/verify_lot_pkn_study_results.py
```

`run_commands.txt` registra o comando:

```powershell
python tools/verify_lot_pkn_study_results.py --result-dir <output-dir>
```

Use `--allow-dry-run` para validar manifestos gerados sem simulação e
`--require-report` para exigir `sensitivity_report.json` e
`sensitivity_report.md`.

## Exemplo 11.5A

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_extended_sensitivity_v2 `
  --output-dir results/comparison/phase11_5a/buz67d_cgeom_extended `
  --lot-sim build/Debug/lot-sim.exe
```
