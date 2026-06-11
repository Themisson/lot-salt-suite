# 46 — Parametric matrix schema v2

## Resumo executivo

A Fase 11.2A especifica uma segunda versão do contrato de matriz LOT/PKN para estudos paramétricos. A versão atual, aqui chamada de `v1`, continua válida e referencia um YAML completo por cenário. A versão `v2` adiciona `base_case + overrides`, preparando geração materializada em `results/` sem exigir que cada cenário derivado seja versionado.

Status:

```text
PARAMETRIC_MATRIX_SCHEMA_V2_SPECIFIED
PARAMETRIC_MATRIX_VALIDATOR_ADDED
```

## Matrix v1

A matriz `v1` é o formato existente. Cada cenário aponta para um caso YAML já materializado:

```yaml
matrix_id: buz67d_cgeom_sensitivity
mode: lot-pkn
scenarios:
  - id: cgeom_075_next_step
    case: cases/validation/sensitivity/buz67d_modern_refined_sens_cgeom_075.yaml
    metadata:
      cgeom_factor: 0.75
```

Esse formato permanece suportado. Ele é adequado quando cada cenário já foi revisado e promovido manualmente para `cases/validation/sensitivity/`.

## Matrix v2

A matriz `v2` declara um `base_case` e cenários com `overrides`:

```yaml
matrix_id: buz67d_modern_refined_cgeom_parametric
schema_version: 2
description: >
  Parametric matrix using base_case + overrides.
mode: lot-pkn
base_case: cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
materialization:
  output_subdir: generated_cases
  filename_template: "{scenario_id}.yaml"
scenarios:
  - id: cgeom_075_next_step
    overrides:
      lot.volumetric_balance.compliance.geometric_compressibility.value: 1.3928975203957504e-8
      lot.fracture.balance.sink_timing: next_step
    metadata:
      cgeom_factor: 0.75
      interpretation: diagnostic_sensitivity
```

O `base_case` deve apontar para um YAML existente. Os cenários derivados devem ser materializados em `results/` ou diretório temporário por ferramenta explícita. Eles não devem ser gravados automaticamente em `cases/validation/`.

## Compatibilidade

| Recurso | v1 | v2 |
|---|---:|---:|
| `matrix_id` | obrigatório | obrigatório |
| `mode` | opcional, default `lot-pkn` | opcional, default `lot-pkn` |
| `base_case` | documental/opcional | obrigatório |
| `scenarios[].case` | obrigatório | não usado |
| `scenarios[].overrides` | não usado | obrigatório |
| `scenarios[].metadata` | opcional | opcional, recomendado |

Matrizes antigas sem `schema_version` são interpretadas como `schema_version: 1`.

## Regras de override

- Paths usam notação por ponto, por exemplo `lot.fracture.balance.sink_timing`.
- Por padrão, cada path deve existir no `base_case`.
- Criação de chaves novas só é permitida com opção explícita `allow_create`.
- Valores numéricos devem continuar numéricos.
- Strings devem continuar strings.
- Listas não são parte do contrato inicial, salvo suporte explícito futuro.
- Se o path não existir, a materialização deve falhar com erro claro.

## Regras de segurança

- O `base_case` não deve ser alterado.
- Casos derivados devem ser gerados em `results/` ou diretório temporário.
- Escrita em `cases/validation/` deve exigir opção explícita de promoção manual.
- Path traversal não deve ser permitido nos nomes materializados.
- `results/` não deve ser versionado.

## Validador

A Fase 11.2A adiciona:

```text
tools/validate_lot_pkn_parametric_matrix.py
```

Uso:

```powershell
python tools/validate_lot_pkn_parametric_matrix.py `
  --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml
```

Classificações principais:

```text
MATRIX_V1_VALID
MATRIX_V2_VALID
MATRIX_INVALID
MATRIX_UNSUPPORTED_VERSION
MATRIX_MISSING_BASE_CASE
MATRIX_MISSING_SCENARIO_CASE
MATRIX_DUPLICATE_SCENARIO_ID
```

## Materialização

A Fase 11.2B adiciona:

```text
tools/materialize_lot_pkn_parametric_matrix.py
docs/47_parametric_case_materialization.md
```

O materializador lê matrizes v2, aplica overrides em uma cópia do `base_case`,
grava casos derivados em `results/` ou diretório temporário, e escreve
`materialization_manifest.json`. A escrita em `cases/` exige opção explícita.

Status:

```text
PARAMETRIC_CASE_MATERIALIZER_ADDED
```

## Limitações

A integração do runner com matrizes v2 fica para a Fase 11.2C.
