# 49 — Run sensitivity studies by study_id

## Objetivo

A Fase 11.3B adiciona uma camada operacional para executar estudos LOT/PKN
registrados em:

```text
cases/validation/sensitivity/studies_index.yaml
```

O usuario nao precisa informar diretamente o caminho da matriz; ele informa o
`study_id`, e a ferramenta resolve o estudo, valida o status e delega a execucao
ao runner generico.

## Como registrar estudo no indice

Cada estudo deve declarar:

```yaml
studies:
  - id: buz67d_cgeom_sensitivity_v2
    title: BUZ-67D modern-refined C_geom sensitivity with parametric matrix v2
    matrix: cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
    route: modern-refined
    status: active
    tags:
      - BUZ-67D
      - modern-refined
      - cgeom
      - sensitivity
      - parametric-v2
    caveat: Diagnostic sensitivity only; generated cases stay in results unless manually promoted.
```

O campo `status` deve ser `active` para execucao normal. Estudos inativos so
podem ser executados com `--allow-inactive`.

## Como executar por study_id

```powershell
python tools/run_lot_pkn_sensitivity_study.py `
  --study-id buz67d_cgeom_sensitivity_v2 `
  --studies-index cases/validation/sensitivity/studies_index.yaml `
  --output-dir results/comparison/studies/buz67d_cgeom_sensitivity_v2 `
  --dry-run
```

Sem `--dry-run`, a ferramenta repassa a matriz resolvida para:

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

## Exemplo BUZ-67D v2

O estudo `buz67d_cgeom_sensitivity_v2` aponta para:

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

Essa matriz usa `schema_version: 2`, materializa casos derivados em `results/`
e preserva o contrato de que artefatos gerados localmente nao devem ser
versionados.

## Opcoes suportadas

```text
--dry-run
--skip-run
--only-summary
--lot-sim <path>
--allow-inactive
```

Essas opcoes sao repassadas ao runner generico quando aplicavel.

## Saidas geradas

A ferramenta escreve no `output-dir`:

```text
study_metadata.json
metadata.json
```

`study_metadata.json` registra:

- `study_id`;
- `matrix_path`;
- `studies_index`;
- `status`;
- comando recebido;
- `dry_run`;
- invocacao equivalente do runner;
- metadata retornada pelo runner.

## Erros comuns

- `study_id not found`: o estudo nao esta registrado no indice.
- `FileNotFoundError` para `studies_index`: o caminho do indice esta incorreto.
- `FileNotFoundError` para matriz: o estudo aponta para matriz inexistente.
- `status != active`: usar `--allow-inactive` apenas para auditorias
  controladas.

## Relacao com o runner generico

`run_lot_pkn_sensitivity_study.py` e um wrapper fino. Ele nao implementa
modelo fisico, nao altera solver, nao altera parser e nao cria pre-processador
obrigatorio de runtime. A execucao real continua sendo responsabilidade de:

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

## Caveats

- A execucao por `study_id` e infraestrutura operacional.
- O estudo BUZ-67D continua `modern-refined` diagnostico.
- A matriz v2 nao e `legacy-equivalence`.
- `results/` permanece local e fora do Git.

## Evolucao 11.3C

Para executar o estudo completo e gerar manifesto final, use:

```text
tools/run_lot_pkn_study.py
```

Esse comando reaproveita `run_lot_pkn_sensitivity_study.py`, chama o reporter
quando há resultados reais e grava `study_manifest.json` e `run_commands.txt`.
