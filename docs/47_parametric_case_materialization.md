# 47 — Parametric case materialization

## Objetivo

A Fase 11.2B adiciona uma ferramenta para materializar casos LOT/PKN derivados a partir de uma matriz `schema_version: 2` baseada em `base_case + overrides`.

Ferramenta:

```text
tools/materialize_lot_pkn_parametric_matrix.py
```

Status:

```text
PARAMETRIC_CASE_MATERIALIZER_ADDED
```

## Relação com o schema v2

O schema v2 é especificado em [docs/46_parametric_matrix_schema.md](46_parametric_matrix_schema.md). A materialização consome:

- `base_case`;
- `scenarios[].id`;
- `scenarios[].overrides`;
- `materialization.filename_template`, quando presente.

O `base_case` não é alterado. Cada cenário gera uma cópia derivada.

## Como materializar casos

```powershell
python tools/materialize_lot_pkn_parametric_matrix.py `
  --matrix tests/fixtures/comparison/phase11_2a_parametric_matrix_v2_fixture.yaml `
  --output-dir results/comparison/phase11_2b/materialized_cases
```

Saídas:

```text
<output-dir>/<scenario_id>.yaml
<output-dir>/materialization_manifest.json
```

## Regras de segurança

- O diretório default recomendado é `results/`.
- Escrita dentro de `cases/` exige `--allow-versioned-output`.
- Arquivos existentes não são sobrescritos sem `--force`.
- Nomes derivados não podem conter path traversal.
- Overrides falham quando o path não existe, salvo uso explícito de `--allow-create`.
- `results/` continua fora do Git.

## Manifest

O `materialization_manifest.json` registra:

- matriz de origem;
- `base_case`;
- cenários;
- YAML derivado;
- overrides aplicados;
- status de sobrescrita;
- flag `dry_run`.

## Dry-run

```powershell
python tools/materialize_lot_pkn_parametric_matrix.py `
  --matrix tests/fixtures/comparison/phase11_2a_parametric_matrix_v2_fixture.yaml `
  --output-dir results/comparison/phase11_2b/materialized_cases `
  --dry-run
```

O dry-run calcula o plano e não grava YAMLs nem manifest.

## Validação com lot-sim

A Fase 11.2C conecta este materializador ao runner genérico:

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

Quando o runner recebe uma matriz v2, ele materializa os casos em
`<output-dir>/materialized_cases/` e então valida/roda esses YAMLs derivados.
O materializador também pode continuar sendo usado diretamente para auditoria
ou dry-run.

## Fase 11.3A

A primeira execução real verificada com materialização v2 foi a matriz BUZ-67D
`modern-refined`:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

Os casos derivados foram gerados em `results/` e não foram versionados.

## Promoção manual

Um caso derivado só deve ser promovido para `cases/validation/` depois de revisão humana, justificativa documental e commit explícito. A ferramenta não promove casos automaticamente.

## Limitações

- Comentários do YAML original não são preservados.
- Listas não são alvo do contrato inicial de override.
- A ferramenta é utilitário de validação/diagnóstico, não pré-processador obrigatório do runtime.
