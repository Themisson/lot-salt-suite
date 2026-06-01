# 10 — Plano de Pós-Processamento

**Status:** Implementado parcialmente | **Última atualização:** 2026-06-01

## Estrutura do pacote lotsaltpost

`
postprocess/lotsaltpost/
├── io.py       # Leitura de resultados CSV/JSON
├── compare.py  # Comparação novo × legado
├── lot.py      # LOT: curva P×V, diagnóstico de fratura
├── apb.py      # APB: pressão anular ×t
├── salt.py     # Sal: deslocamento radial, fluência
├── thermal.py  # Temperatura ×profundidade e ×tempo
├── coupling.py # Painel acoplado LOT+APB+sal
├── plots.py    # Primitivas matplotlib padronizadas
├── report.py   # Gerador HTML de relatório
├── export.py   # Exportação SVG/PDF para artigo
├── units.py    # Conversão nos resultados
├── style.py    # Paletas e marcadores
└── cli.py      # lotsaltpost run <estudo.yaml>
`

## Scripts disponíveis

| Script | Função |
|--------|--------|
| `lot_pkn_report.py` | Fase 6.7: gráficos e relatório HTML para saídas modernas LOT/PKN (`result.json` + `timeseries.csv`), sem regressão contra legado |
| `plot_lot_curve.py` | Curva LOT P×V e P×t |
| `plot_apb_pressure.py` | Pressão anular ×t |
| `compare_legado_novo.py` | Tabela de erro legado × novo |
| `plot_salt_closure.py` | Fechamento de poço ×t |
| `plot_coupled.py` | Painel completo |
| `generate_article_figures.py` | Figuras para publicação |

## Fase 6.7 — Pós-processamento moderno LOT/PKN

O script `postprocess/scripts/lot_pkn_report.py` lê apenas as saídas modernas
geradas por:

```bash
lot-sim run --mode lot-pkn
```

Entradas esperadas:

```text
result.json
timeseries.csv
```

Saídas geradas no diretório `--output`:

```text
pressure_vs_time.png
pressure_vs_volume.png
length_vs_time.png
width_vs_time.png
leakoff_vs_time.png
report.html
```

Uso:

```bash
python postprocess/scripts/lot_pkn_report.py \
  --run-dir results/lot_pkn_minimal \
  --output reports/lot_pkn_minimal
```

Também é possível informar os arquivos diretamente:

```bash
python postprocess/scripts/lot_pkn_report.py \
  --input results/lot_pkn_minimal/timeseries.csv \
  --summary results/lot_pkn_minimal/result.json \
  --output reports/lot_pkn_minimal
```

Todos os relatórios são rotulados como:

```text
Modern synthetic LOT/PKN output - no legacy regression
```

O relatório HTML contém aviso explícito de que usa somente outputs modernos
sintéticos e que nenhuma regressão numérica contra legado foi executada.

## Política — C++ first, Python postprocess only

O pós-processamento começa **depois** que o C++ termina a simulação e grava
`CSV/JSON`. O fluxo permitido é:

```text
CSV/JSON → Python plot/report → PNG/HTML
```

O fluxo runtime principal permanece:

```text
YAML/JSON → C++ parser → C++ model/runner → C++ writer → CSV/JSON
```

`lot_pkn_report.py` não faz pré-processamento, não monta entradas do solver, não
gera YAML de produção, não calcula `PknInput`, não calibra parâmetros e não
substitui módulos C++. Ele apenas valida `timeseries.csv`/`result.json`, gera
figuras e escreve `report.html`.

Novos scripts Python devem ser avaliados contra esta política antes de serem
criados. Se a tarefa envolver física, solver, parsing runtime, conversão de
unidades, acoplamento LOT/APB/sal, dano, breakdown ou integração com
`external/saltcreep`, a implementação deve ser C++.

### Robustez

O script valida:

- existência dos arquivos de entrada;
- colunas obrigatórias do CSV;
- ausência de `NaN`/`Inf`;
- presença de `summary` em `result.json`;
- criação do diretório de saída.

### Escopo deliberadamente fora

- Não lê `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/`.
- Não compara com `.dat`.
- Não declara validação contra legado.
- Não resolve R09; R09 permanece mitigado apenas para os casos PKN auditados e
  ainda bloqueia regressões envolvendo `idQ == 4`.
