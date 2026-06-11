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
