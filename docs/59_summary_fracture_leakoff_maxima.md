# Fracture/leakoff maxima in sensitivity summaries (Fase 11.5D)

## Resumo executivo

A Fase 11.5D adiciona, de forma condicional e Python-only, máximos de fratura,
leakoff e pressão líquida aos `summary.csv` gerados por
`tools/run_lot_pkn_sensitivity_matrix.py`.

Gate:

```text
SUMMARY_MAXIMA_PYTHON_ONLY_SAFE
```

O gate é seguro porque `timeseries.csv` moderno já exporta:

```text
fracture_volume_m3
leakoff_volume_m3
fracture_length_m
fracture_width_m
net_pressure_Pa
```

Portanto, a fase não exige alteração C++, parser, schema, writer ou casos.

## Campos adicionados ao summary

| Campo | Origem em `timeseries.csv` | Interpretação |
|---|---|---|
| `max_fracture_volume_m3` | `fracture_volume_m3` | Máximo diagnóstico do volume de fratura. |
| `max_leakoff_volume_m3` | `leakoff_volume_m3` | Máximo diagnóstico do volume acumulado de leakoff. |
| `max_fracture_length_m` | `fracture_length_m` | Máximo diagnóstico do comprimento de fratura. |
| `max_fracture_width_m` | `fracture_width_m` | Máximo diagnóstico da abertura/largura de fratura. |
| `max_net_pressure_Pa` | `net_pressure_Pa` | Máximo diagnóstico da pressão líquida PKN. |

Se uma matriz antiga ou fixture sintética não contiver essas colunas, o runner
mantém compatibilidade e deixa as células vazias.

## Escopo

Esta fase altera apenas ferramenta e testes Python. Ela não:

- muda a formulação LOT/PKN;
- muda o writer C++;
- muda casos protegidos;
- promove fatores de `C_geom` a calibração física;
- versiona `results/`.

## Uso

Ao rodar uma matriz por:

```text
python tools/run_lot_pkn_study.py --study-id buz67d_cgeom_sensitivity_v2 --output-dir results/comparison/<run>
```

o `summary.csv` passa a conter os campos máximos quando os `timeseries.csv`
produzidos pelo solver moderno incluem as colunas necessárias.

## Caveat

Os máximos são agregações diagnósticas de pós-processamento. Eles ajudam a
comparar cenários, mas não são validação física nem calibração automática.
