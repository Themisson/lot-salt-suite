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
