# 48 — BUZ-67D parametric matrix v2 execution

## Resumo executivo

A Fase 11.3A executa a matriz paramétrica v2 BUZ-67D `modern-refined` com o runner genérico e verifica que a materialização `base_case + overrides` reproduz os diagnósticos principais já documentados para os cenários equivalentes da matriz v1.

Status:

```text
PHASE11_3A_V2_SENSITIVITY_RUN_VERIFIED
PARAMETRIC_MATRIX_V2_EXECUTION_CONFIRMED
V2_REPRODUCES_V1_DIAGNOSTICS
```

## Matriz executada

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

Contrato:

```text
schema_version = 2
matrix_id = buz67d_modern_refined_cgeom_sensitivity_v2
base_case = cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
```

## Materialização

A matriz v2 materializa casos derivados em results/ para execução local. Esses casos materializados são artefatos reproduzíveis, mas não devem ser commitados. A fonte versionada é a matriz v2 e o base_case.

Artefatos locais:

```text
results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/materialized_cases/
```

Casos materializados:

```text
cgeom_075_next_step.yaml
cgeom_100_next_step.yaml
cgeom_125_next_step.yaml
cgeom_100_same_step.yaml
```

## Execução

Comando:

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml `
  --output-dir results/comparison/phase11_3a/buz67d_cgeom_matrix_v2 `
  --lot-sim build/Debug/lot-sim.exe
```

Saídas locais:

```text
results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/summary.csv
results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/metadata.json
```

## Verificação

Ferramenta criada:

```text
tools/verify_phase11_3a_v2_sensitivity_run.py
```

Classificação:

```text
PHASE11_3A_V2_SENSITIVITY_RUN_OK
V2_REPRODUCES_V1_DIAGNOSTICS
```

## Comparação v2 vs v1

Quando os resultados v1 locais não estão disponíveis, a comparação usa os valores documentados das fases anteriores:

```text
source = DOCUMENTED_PHASE_SUMMARY
```

| Cenário | Resultado v2 | Referência documentada | Status |
|---|---:|---:|---|
| `cgeom_075_next_step` abertura | 510 s | 510 s | compatível |
| `cgeom_075_next_step` sink delay | 30 s | 30 s | compatível |
| `cgeom_100_next_step` abertura | 660 s | 660 s | compatível |
| `cgeom_100_next_step` sink delay | 30 s | 30 s | compatível |
| `cgeom_125_next_step` abertura | sem abertura | sem abertura | compatível |
| `cgeom_100_same_step` sink delay | 0 s | 0 s | compatível |

## Relatório genérico

Também foi executado:

```powershell
python tools/report_lot_pkn_sensitivity_matrix.py `
  --summary results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/summary.csv `
  --metadata results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/metadata.json `
  --output-json results/comparison/phase11_3a/v2_sensitivity_report.json `
  --output-md results/comparison/phase11_3a/v2_sensitivity_report.md
```

O relatório permanece diagnóstico e não promove fatores de compliance a calibração automática.

## Como reproduzir

1. Validar a matriz:

```powershell
python tools/validate_lot_pkn_parametric_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

2. Rodar a matriz:

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml `
  --output-dir results/comparison/phase11_3a/buz67d_cgeom_matrix_v2 `
  --lot-sim build/Debug/lot-sim.exe
```

3. Verificar:

```powershell
python tools/verify_phase11_3a_v2_sensitivity_run.py `
  --summary results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/summary.csv `
  --metadata results/comparison/phase11_3a/buz67d_cgeom_matrix_v2/metadata.json `
  --output-json results/comparison/phase11_3a/v2_run_verification.json `
  --output-md results/comparison/phase11_3a/v2_run_verification.md
```

## Limitações

- A comparação v2 vs v1 usa valores documentados quando resultados v1 locais não estão presentes.
- A execução confirma equivalência diagnóstica dos cenários selecionados, não validação física.
- Os casos materializados não são fonte versionada.
- `results/` permanece fora do Git.

## Próxima fase recomendada

A próxima fase pode consolidar execução multi-estudo ou adicionar resolução por `study_id`, agora que a matriz v2 foi validada em execução real.

## Fase 11.3B — resolução por study_id

A resolução por `study_id` foi adicionada em:

```text
tools/run_lot_pkn_sensitivity_study.py
```

O estudo verificado nesta página pode ser executado pelo índice:

```powershell
python tools/run_lot_pkn_sensitivity_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --studies-index cases/validation/sensitivity/studies_index.yaml `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --dry-run
```

Isso preserva a matriz v2 como fonte versionada e mantém casos materializados
em `results/`.
