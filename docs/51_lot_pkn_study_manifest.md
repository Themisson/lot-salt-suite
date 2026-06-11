# 51 - LOT/PKN study manifest schema v1

## Objetivo

A Fase 11.4A define o `study_manifest.json` como contrato operacional
versionado por schema para estudos LOT/PKN executados por `study_id`.

O manifesto registra proveniencia, comandos, ambiente e artefatos esperados. Ele
nao substitui os arquivos de entrada versionados e nao transforma resultados
diagnosticos em validacao fisica.

## Schema v1

Campos principais:

```json
{
  "schema_version": 1,
  "study_id": "buz67d_cgeom_sensitivity_v2",
  "study_status": "completed",
  "matrix_path": "cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml",
  "matrix_id": "buz67d_modern_refined_cgeom_sensitivity_v2",
  "matrix_schema_version": 2,
  "base_case": "cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml",
  "studies_index": "cases/validation/sensitivity/studies_index.yaml",
  "output_dir": "results/comparison/studies/buz67d_cgeom_sensitivity_v2",
  "created_at_utc": "2026-06-11T00:00:00+00:00",
  "command": "python tools/run_lot_pkn_study.py ...",
  "commands": {
    "study_runner": "python tools/run_lot_pkn_sensitivity_study.py ...",
    "sensitivity_runner": "python tools/run_lot_pkn_sensitivity_matrix.py ...",
    "reporter": "python tools/report_lot_pkn_sensitivity_matrix.py ...",
    "verifier": "python tools/verify_lot_pkn_study_results.py --result-dir ..."
  },
  "environment": {
    "python_version": "3.x",
    "platform": "Windows-...",
    "executable": "python",
    "cwd": "..."
  },
  "git": {
    "available": true,
    "commit": "...",
    "branch": "main",
    "is_dirty": false
  },
  "lot_sim": {
    "path": "build/Debug/lot-sim.exe",
    "resolved_path": "...",
    "exists": true
  },
  "outputs": {
    "summary_csv": "results/.../summary.csv",
    "metadata_json": "results/.../metadata.json",
    "report_json": "results/.../sensitivity_report.json",
    "report_md": "results/.../sensitivity_report.md",
    "run_commands_txt": "results/.../run_commands.txt"
  },
  "scenarios": [
    {
      "id": "cgeom_100_next_step",
      "status": "completed",
      "case_path": "...",
      "materialized_case_path": "...",
      "metadata": {}
    }
  ],
  "caveats": []
}
```

## Status

`study_status` deve ser:

- `dry_run`: plano gerado sem execucao de simulacoes.
- `completed`: execucao completa com `summary.csv`.
- `partial`: execucao sem todos os artefatos esperados, por exemplo com
  `--skip-run` ou `--only-summary`.
- `failed`: reservado para fases futuras em que o comando registre falhas sem
  propagar excecao.

## Regras de robustez

- `git.available=false` quando Git nao esta disponivel.
- `git.is_dirty` pode ser `null` se o estado nao puder ser lido.
- `lot_sim.exists=false` e aceito em `--dry-run`.
- O manifesto deve ser gerado em `--dry-run`.
- Falha em coletar commit ou branch nao deve interromper o estudo.

## Limites

O manifesto e uma trilha operacional. Ele nao prova equivalencia com o
`LOT_Tese`, nao valida fisicamente fratura e nao deve ser usado para versionar
artefatos em `results/`.
