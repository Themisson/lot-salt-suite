# Generic LOT/PKN sensitivity runner

## Objetivo

A Fase 10.29B cria uma infraestrutura genérica para rodar matrizes de
sensibilidade LOT/PKN sem duplicar scripts específicos por fase.

Ferramenta:

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

Status:

```text
GENERIC_LOT_PKN_SENSITIVITY_RUNNER_ADDED
```

## Formato da matriz YAML

Exemplo mínimo:

```yaml
matrix_id: buz67d_cgeom_sensitivity
base_case: cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
mode: lot-pkn
scenarios:
  - id: cgeom_075
    case: cases/validation/sensitivity/buz67d_modern_refined_sens_cgeom_075.yaml
  - id: cgeom_100
    case: cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
```

Campos:

| Campo | Obrigatório | Uso |
|---|---:|---|
| `matrix_id` | sim | Identificador rastreável da matriz. |
| `mode` | não | Default `lot-pkn`. |
| `base_case` | não | Caso de referência documental. |
| `scenarios[].id` | sim | Nome do cenário e subdiretório de saída. |
| `scenarios[].case` | sim | YAML moderno a validar/rodar. |
| `scenarios[].timeseries` | não | CSV já existente para `--only-summary` ou testes. |

## Como rodar

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py `
  --matrix tests/fixtures/comparison/phase10_29b_sensitivity_matrix_fixture.yaml `
  --output-dir results/comparison/sensitivity_matrix_demo `
  --lot-sim build/Debug/lot-sim.exe
```

O runner:

1. valida cada caso com `lot-sim validate`;
2. roda cada caso com `lot-sim run --mode lot-pkn`;
3. coleta `timeseries.csv`;
4. escreve `summary.csv`;
5. escreve `metadata.json`.

## Modos auxiliares

| Opção | Efeito |
|---|---|
| `--dry-run` | Registra comandos planejados sem validar, rodar ou sumarizar. |
| `--skip-run` | Não executa `lot-sim`, mas tenta sumarizar outputs esperados. |
| `--only-summary` | Apenas sumariza `timeseries.csv` existentes. |
| `--legacy-csv` | Guarda caminho de referência legado em metadata; comparação física não é automática. |
| `--lot-sim` | Usa executável explícito, por exemplo `build/Debug/lot-sim.exe`. |

## Summary e metadata

O `summary.csv` contém, por cenário:

- `max_pressure_Pa`;
- `fracture_initiation_time_s`;
- `first_sink_positive_time_s`;
- `sink_delay_s`;
- `final_pressure_Pa`.

O `metadata.json` contém matriz, comandos planejados, flags de execução e
status.

## Limitações

- O runner é ferramenta de validação/diagnóstico, não caminho runtime.
- O runner não cria YAMLs de produção.
- O runner não compara fratura física automaticamente.
- `results/` continua fora do versionamento.
- Legacy-equivalence continua separada de modern-refined.

## Exemplo BUZ-67D modern-refined

A matriz BUZ-67D pode apontar para os casos em:

```text
cases/validation/sensitivity/
```

Esses casos permanecem diagnósticos. O runner automatiza validação, execução e
sumarização; ele não transforma o melhor cenário em calibração validada.

## Matriz versionada BUZ-67D

A Fase 10.30A adiciona a matriz versionada:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml
```

Ela contém os cenários `0.60x..1.25x` de `constant_geometric` e o cenário
`same_step`. O status associado é:

```text
VERSIONED_BUZ67D_CGEOM_SENSITIVITY_MATRIX_ADDED
```

A matriz continua diagnóstica e não promove nenhum fator a calibração
automática.

## Execução verificada da matriz BUZ-67D

A Fase 10.30B executa a matriz versionada com o runner genérico e verifica os
artefatos locais `summary.csv` e `metadata.json` por meio de:

```text
tools/verify_phase10_30b_sensitivity_run.py
```

O verificador confirma:

- `matrix_id = buz67d_modern_refined_cgeom_sensitivity`;
- 10 cenários no resumo;
- presença de `cgeom_100_next_step`;
- presença de `cgeom_075_next_step`;
- presença de `cgeom_100_same_step`;
- ausência de ação marcada como falha.

Status:

```text
VERSIONED_SENSITIVITY_RUN_OK
```

Os resultados continuam em `results/` e não são versionados.

## Relatório automático de sensibilidade

A Fase 10.30C adiciona:

```text
tools/report_lot_pkn_sensitivity_matrix.py
docs/41_sensitivity_reporting.md
```

O relatório consome `summary.csv` e `metadata.json` produzidos pelo runner e
gera JSON/Markdown com ranking por abertura, pressão máxima e score combinado.
Quando alvos legados não são fornecidos, o relatório é relativo ao baseline.
Quando alvos legados documentados são fornecidos, os resultados continuam
diagnósticos e não viram calibração automática.

## Pacote reproduzível BUZ-67D

A Fase 10.31A adiciona um orquestrador operacional:

```text
tools/run_buz67d_modern_refined_package.py
```

Ele valida os casos mínimos, valida os casos da matriz versionada, roda a
matriz com o runner genérico e chama o gerador de relatório. Os artefatos são
gravados em `results/` e permanecem fora do Git.

Status:

```text
BUZ67D_MODERN_REFINED_PACKAGE_RUNNER_ADDED
```

## Índice de estudos de sensibilidade

A Fase 11.1B adiciona `cases/validation/sensitivity/studies_index.yaml` e
`tools/list_lot_pkn_sensitivity_studies.py`. O índice permite descobrir matrizes
versionadas sem duplicar conteúdo:

```powershell
python tools/list_lot_pkn_sensitivity_studies.py --index cases/validation/sensitivity/studies_index.yaml --validate
```

O runner ainda recebe `--matrix` diretamente. A resolução de `study_id` fica
como evolução futura, se o índice permanecer estável.

## Parametric matrix schema v2

A Fase 11.2A especifica o contrato de matriz paramétrica `schema_version: 2`
em [docs/46_parametric_matrix_schema.md](46_parametric_matrix_schema.md).
O formato v2 permite declarar `base_case + scenario.overrides`, preservando a
compatibilidade com o formato v1 baseado em `scenario.case`.

Ferramenta adicionada:

```text
tools/validate_lot_pkn_parametric_matrix.py
```

Status:

```text
PARAMETRIC_MATRIX_SCHEMA_V2_SPECIFIED
PARAMETRIC_MATRIX_VALIDATOR_ADDED
```

Nesta fase o runner permanece compatível com v1. A materialização de casos
derivados e a execução direta de matrizes v2 ficam para as fases 11.2B e 11.2C.

## Materialização de casos paramétricos

A Fase 11.2B adiciona o utilitário:

```text
tools/materialize_lot_pkn_parametric_matrix.py
```

Ele consome matrizes v2 e grava YAMLs derivados em `results/` ou diretório
temporário. O runner ainda não chama esse materializador automaticamente nesta
fase; essa integração fica para 11.2C.

## Runner com suporte a matriz v2

A Fase 11.2C integra o materializador ao runner. Quando a matriz declara
`schema_version: 2`, o runner materializa os cenários em:

```text
<output-dir>/materialized_cases/
```

e usa esses YAMLs derivados para `lot-sim validate` e `lot-sim run`. Matrizes
v1 continuam usando `scenarios[].case` como antes.

Novas opções:

| Opção | Efeito |
|---|---|
| `--materialized-dir` | Define diretório explícito para YAMLs derivados. |
| `--force-materialize` | Permite sobrescrever YAMLs derivados existentes. |
| `--keep-materialized` | Reservado; os arquivos em `output-dir` já são mantidos para rastreabilidade local. |

O `summary.csv` e o `metadata.json` registram `materialized_case_path` para
matrizes v2.

Status:

```text
SENSITIVITY_RUNNER_SUPPORTS_PARAMETRIC_MATRIX_V2
BUZ67D_CGEOM_SENSITIVITY_V2_REGISTERED
```

## Execução verificada da matriz v2 BUZ-67D

A Fase 11.3A executa a matriz:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

com materialização em `results/` e verifica:

```text
PHASE11_3A_V2_SENSITIVITY_RUN_OK
V2_REPRODUCES_V1_DIAGNOSTICS
```

O verificador associado é:

```text
tools/verify_phase11_3a_v2_sensitivity_run.py
```

## Execução por study_id

A Fase 11.3B adiciona o wrapper:

```text
tools/run_lot_pkn_sensitivity_study.py
```

Ele resolve `study_id` em `cases/validation/sensitivity/studies_index.yaml`,
verifica `status: active`, resolve o caminho da matriz e delega a execução ao
runner genérico. Essa camada não altera `run_lot_pkn_sensitivity_matrix.py` nem
o runtime C++; ela apenas torna a execução de estudos registrados mais
ergonômica e reproduzível.

Exemplo:

```powershell
python tools/run_lot_pkn_sensitivity_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --studies-index cases/validation/sensitivity/studies_index.yaml `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --dry-run
```

Status:

```text
SENSITIVITY_STUDY_ID_EXECUTION_ADDED
BUZ67D_CGEOM_SENSITIVITY_V2_RUNNABLE_BY_STUDY_ID
```
