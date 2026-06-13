# APB/LOT JSON output writer

## Resumo executivo

Foi criado o writer moderno `ApbLotJsonOutputWriter` para saida estruturada
APB/LOT em JSON. A regra de nome e:

```text
entrada.ext -> entrada_out.json
```

Output explicito continua tendo prioridade.

## Contrato minimo

O arquivo contem:

- `metadata`;
- `configuration`;
- `time_series`;
- `layers`;
- `annulars`;
- `summary`;
- `caveats`.

O schema de saida e identificado por:

```text
apb_lot_output_v1
```

## Compatibilidade

`.dat` legado permanece disponivel como modo opcional. O writer JSON nao altera
`ResultWriter` do PKN nem o formato fisico `result.json`/`timeseries.csv`.

## Regressao estendida APB/LOT

A fase `APB_LOT_RUN_EXTENDED_REGRESSION_SUITE` confirmou que o contrato minimo
do `_out.json` contem `metadata`, `configuration`, `time_series`, `layers`,
`annulars`, `summary` e `caveats`. A secao `configuration` registra
explicitamente:

```text
output_format
leakoff_coupling_mode
salt_displacement_mode
```

Status: `JSON_OUTPUT_CONTRACT_VALID`.

## Validacao com caso real APB/LOT

A fase `APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE` confirmou que o
writer ainda nao esta integrado ao runtime. `apps/lot-sim.cpp` continua
executando apenas `run --mode lot-pkn`, portanto nenhum `*_out.json` efetivo
foi gerado por um caso APB/LOT real.

Status:

```text
APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER
REAL_CASE_RUNNER_INTEGRATION_REQUIRED
```

## Validacao posterior da semantica numerica

Depois da integracao controlada do runner APB/LOT, a fase
`APB_LOT_VALIDATE_REAL_RUNNER_NUMERICAL_SEMANTICS` confirmou que o `_out.json`
moderno e parseavel e contem `time_series` com valores finitos, tempo monotono e
`summary` consistente. A validacao permanece diagnostica/controlada e nao altera
`ResultWriter` do PKN.
