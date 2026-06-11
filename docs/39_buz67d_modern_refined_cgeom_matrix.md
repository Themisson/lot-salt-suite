# BUZ-67D modern-refined C_geom sensitivity matrix

## Resumo executivo

A Fase 10.30A cria uma matriz YAML versionada para a sensibilidade BUZ-67D
`modern-refined`:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml
```

Status:

```text
VERSIONED_BUZ67D_CGEOM_SENSITIVITY_MATRIX_ADDED
```

A matriz consolida os cenários criados nas Fases 10.28C e 10.29A e permite
rodar a sensibilidade com o runner genérico `tools/run_lot_pkn_sensitivity_matrix.py`.

## Objetivo

O objetivo é transformar a sensibilidade de `constant_geometric` em artefato
reproduzível. A matriz não implementa modelo novo, não altera solver e não muda
o fluxo padrão `lot-sim run --mode lot-pkn`.

## Cenários incluídos

| Cenário | C_geom factor | sink_timing | Origem |
|---|---:|---|---|
| `cgeom_060_next_step` | `0.60x` | `next_step` | Fase 10.29A |
| `cgeom_065_next_step` | `0.65x` | `next_step` | Fase 10.29A |
| `cgeom_070_next_step` | `0.70x` | `next_step` | Fase 10.29A |
| `cgeom_075_next_step` | `0.75x` | `next_step` | Fase 10.28C/10.29A |
| `cgeom_080_next_step` | `0.80x` | `next_step` | Fase 10.29A |
| `cgeom_085_next_step` | `0.85x` | `next_step` | Fase 10.29A |
| `cgeom_090_next_step` | `0.90x` | `next_step` | Fase 10.29A |
| `cgeom_100_next_step` | `1.00x` | `next_step` | baseline modern-refined |
| `cgeom_125_next_step` | `1.25x` | `next_step` | Fase 10.28C |
| `cgeom_100_same_step` | `1.00x` | `same_step` | Fase 10.28C |

## Origem dos YAMLs

Todos os cenários apontam para YAMLs já versionados em:

```text
cases/validation/sensitivity/
```

Nenhum caso protegido foi alterado. A matriz apenas referencia casos existentes.

## Interpretação dos fatores C_geom

Os fatores multiplicam o equivalente diagnóstico `constant_geometric` usado no
modo BUZ-67D `modern-refined`. A Fase 10.29A observou que `0.75x` aproxima a
abertura de `510 s`, enquanto `0.60x` aproxima melhor a pressão máxima isolada.

Esta matriz é diagnóstica. O fator de compliance que melhor aproxima uma métrica
específica não deve ser promovido automaticamente a parâmetro calibrado nem
interpretado como validação física sem critérios independentes.

## Como executar

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml `
  --output-dir results/comparison/buz67d_cgeom_sensitivity `
  --lot-sim build/Debug/lot-sim.exe
```

## Dry-run

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml `
  --output-dir results/comparison/phase10_30a/dry_run `
  --dry-run
```

## Saídas esperadas

O runner escreve localmente em `results/`:

```text
summary.csv
metadata.json
runs/<scenario_id>/timeseries.csv
runs/<scenario_id>/result.json
```

`results/` não deve ser versionado.

## Próxima fase

A Fase 10.30B deve executar a matriz versionada com o runner genérico e criar
um verificador dos resultados gerados.

## Resultado da Fase 10.30B

A Fase 10.30B executou esta matriz com:

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

e verificou `summary.csv`/`metadata.json` com:

```text
tools/verify_phase10_30b_sensitivity_run.py
```

Classificação:

```text
VERSIONED_SENSITIVITY_RUN_OK
```

A execução confirmou a presença dos 10 cenários versionados. O cenário
`cgeom_075_next_step` abriu em `510 s`, o baseline `cgeom_100_next_step` abriu
em `660 s`, e `cgeom_100_same_step` preservou abertura em `660 s` com
`sink_delay = 0 s`. A interpretação continua diagnóstica.

## Pacote reproduzível 10.31A

A matriz é a entrada padrão do pacote reproduzível:

```text
tools/run_buz67d_modern_refined_package.py
```

Esse pacote permite reproduzir validação, execução da matriz e relatório em
outro computador, desde que `lot-sim` esteja compilado ou disponível no `PATH`.
Os resultados gerados continuam locais em `results/`.
