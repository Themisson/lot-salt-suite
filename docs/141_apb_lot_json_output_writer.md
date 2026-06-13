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
