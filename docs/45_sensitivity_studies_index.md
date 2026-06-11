# 45 — Sensitivity studies index

## Objetivo

O índice de estudos de sensibilidade é a primeira infraestrutura da Etapa 11.
Ele registra matrizes LOT/PKN disponíveis sem duplicar os arquivos de matriz e
sem alterar o runner existente.

## Formato do índice

Arquivo canônico:

```text
cases/validation/sensitivity/studies_index.yaml
```

Estrutura mínima:

```yaml
studies:
  - id: buz67d_cgeom_sensitivity
    title: BUZ-67D modern-refined C_geom sensitivity
    matrix: cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml
    route: modern-refined
    status: active
    tags:
      - BUZ-67D
      - modern-refined
      - cgeom
      - sensitivity
    caveat: Diagnostic sensitivity only; not automatic calibration.
```

## Como listar estudos

```powershell
python tools/list_lot_pkn_sensitivity_studies.py --index cases/validation/sensitivity/studies_index.yaml
```

## Como validar o índice

```powershell
python tools/list_lot_pkn_sensitivity_studies.py --index cases/validation/sensitivity/studies_index.yaml --validate
```

A validação confirma que cada matriz referenciada existe. Ela não executa os
cenários nem declara validação física.

## Filtros

```powershell
python tools/list_lot_pkn_sensitivity_studies.py --index cases/validation/sensitivity/studies_index.yaml --tag modern-refined
python tools/list_lot_pkn_sensitivity_studies.py --index cases/validation/sensitivity/studies_index.yaml --status active
python tools/list_lot_pkn_sensitivity_studies.py --index cases/validation/sensitivity/studies_index.yaml --json
```

## Como rodar um estudo referenciado

Resolva o campo `matrix` do estudo e use o runner existente:

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml --output-dir results/comparison/buz67d_cgeom_matrix
```

Nesta fase o runner não foi alterado para aceitar `study_id`; isso fica como
evolução possível da 11.2A se o contrato do índice se mostrar estável.

## Exemplo BUZ-67D

O estudo inicial registrado é:

```text
buz67d_cgeom_sensitivity
```

Ele aponta para a matriz BUZ-67D `modern-refined` de C_geom e permanece
diagnóstico:

- não é calibração automática;
- não é regressão estrita `legacy-equivalence`;
- não altera runtime C++;
- não versiona `results/`.

## Como adicionar novo estudo

1. Criar ou selecionar uma matriz YAML versionada.
2. Adicionar entrada ao `studies_index.yaml`.
3. Declarar `route`, `status`, `tags` e `caveat`.
4. Rodar a ferramenta com `--validate`.
5. Manter `results/` fora do Git.

## Relação com matriz paramétrica v2

A Fase 11.2A adiciona a especificação `schema_version: 2` para matrizes
paramétricas baseadas em `base_case + overrides`. O índice pode apontar tanto
para matrizes v1 quanto, em fases futuras, para matrizes v2. A validação do
índice continua verificando apenas a existência do arquivo de matriz; a
validação estrutural da matriz fica com:

```text
tools/validate_lot_pkn_parametric_matrix.py
```

## Estudo v2 registrado

A Fase 11.2C registra a variante:

```text
buz67d_cgeom_sensitivity_v2
```

Ela aponta para:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

Essa matriz usa `base_case + overrides`; os casos derivados são gerados pelo
runner em `results/` e não são versionados automaticamente.

A Fase 11.3A executou essa matriz e confirmou:

```text
PHASE11_3A_V2_SENSITIVITY_RUN_OK
V2_REPRODUCES_V1_DIAGNOSTICS
```

## Execução direta por study_id

A Fase 11.3B adiciona:

```text
tools/run_lot_pkn_sensitivity_study.py
```

Agora o estudo pode ser executado pelo identificador do índice:

```powershell
python tools/run_lot_pkn_sensitivity_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --studies-index cases/validation/sensitivity/studies_index.yaml `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --dry-run
```

O wrapper exige `status: active` por padrão e escreve `study_metadata.json` no
diretório de saída. Estudos inativos exigem `--allow-inactive`. A execução por
`study_id` não altera a semântica das matrizes e continua gravando artefatos
locais em `results/`.

## Comando único por estudo

A Fase 11.3C adiciona `tools/run_lot_pkn_study.py`, que usa o mesmo índice e
gera também `study_manifest.json` e `run_commands.txt`.

```powershell
python tools/run_lot_pkn_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --dry-run
```

Esse comando é a entrada recomendada para reproduzir estudos registrados em
outro computador.

## Provenance

Desde a Fase 11.4A, `tools/run_lot_pkn_study.py` copia a resolução do
`study_id` para `study_manifest.json` v1. Isso registra o `studies_index`, a
matriz resolvida, o `matrix_id`, o `base_case` e os comandos de reprodução sem
versionar `results/`.

## Estudo ampliado de C_geom

A Fase 11.5A registra:

```text
buz67d_cgeom_extended_sensitivity_v2
```

Esse estudo aponta para
`cases/validation/sensitivity/buz67d_modern_refined_cgeom_extended_matrix_v2.yaml`
e avalia fatores `0.50..1.25` com `sink_timing=next_step`.

## Estudo cruzado C_geom x sink_timing

A Fase 11.5B registra:

```text
buz67d_cgeom_sink_timing_sensitivity_v2
```

Esse estudo aponta para
`cases/validation/sensitivity/buz67d_modern_refined_cgeom_sink_timing_matrix_v2.yaml`
e cruza fatores `0.60`, `0.75`, `1.00` e `1.25` com `same_step` e
`next_step`. A matriz separa efeitos diagnósticos de compliance e temporização
do sink, mas não calibra fisicamente o modelo.

## Consolidação BUZ-67D

A Fase 11.5C consolida os dois estudos em
`docs/56_buz67d_modern_refined_sensitivity_consolidation.md`. O documento fecha
o bloco BUZ-67D modern-refined e recomenda a transição para a auditoria
BUZ29-VISCO-first-well.

## Summaries com máximos — Fase 11.5D

A Fase 11.5D adiciona ao `summary.csv` do runner genérico os campos:

```text
max_fracture_volume_m3
max_leakoff_volume_m3
max_fracture_length_m
max_fracture_width_m
max_net_pressure_Pa
```

Esses campos são agregados a partir de `timeseries.csv` quando as colunas
existem. A mudança não altera o índice de estudos, não muda casos e não
versiona `results/`.
