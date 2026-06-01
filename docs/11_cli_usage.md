# 11 — Uso da CLI lot-sim

**Status:** Em andamento | **Última atualização:** 2026-06-01

## Subcomandos disponíveis

### inspect

```bash
lot-sim inspect --case <arquivo.yaml>
```

Carrega o YAML pelo `CaseParser`, aplica conversões para SI e imprime um resumo
do caso.

### validate

```bash
lot-sim validate --case <arquivo.yaml>
```

Carrega e valida semanticamente o contrato do caso. Para `simulation.mode:
lot-pkn`, confirma que `lot.model` e `lot.fracture.geometry` são `pkn`, que os
tempos de injeção são positivos e que altura/pressão de breakdown existem.

### run LOT/PKN

```bash
lot-sim run --case cases/validation/lot_pkn_minimal.yaml \
            --mode lot-pkn \
            --output results/lot_pkn_minimal
```

Fluxo executado:

```text
YAML -> CaseParser -> PknInput -> PknModel -> PknResult -> CSV/JSON
```

O modo `lot-pkn` é moderno e sintético/dimensional nesta fase. Ele não compara
resultados com `legance/`, `.dat` ou outputs legados.

Arquivos gerados no diretório de saída:

| Arquivo | Conteúdo |
|---------|----------|
| `result.json` | Metadados do caso, status `synthetic_modern_no_legacy_regression`, resumo final e avisos sobre R09. |
| `timeseries.csv` | Série temporal em SI de tempo, volume injetado, comprimento/abertura de fratura, volume de fratura, leakoff e pressão líquida. |

Cabeçalho do CSV:

```text
time_s,injected_volume_m3,fracture_length_m,fracture_width_m,fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa
```

## Exemplos

```bash
# Validar caso mínimo LOT/PKN
lot-sim validate --case cases/validation/lot_pkn_minimal.yaml

# Executar caso mínimo LOT/PKN
lot-sim run --case cases/validation/lot_pkn_minimal.yaml \
            --mode lot-pkn \
            --output results/lot_pkn_minimal

# Executar caso LOT/PKN com leakoff simplificado
lot-sim run --case cases/validation/lot_pkn_with_leakoff.yaml \
            --mode lot-pkn \
            --output results/lot_pkn_with_leakoff
```

## Fora de escopo atual

- `run --mode apb`, `salt`, `lot-salt`, `apb-salt` e `coupled`.
- Regressão numérica contra legado.
- Uso de `buz67d_pkn.yaml` como baseline físico.
- Acoplamento com APB ou sal.
