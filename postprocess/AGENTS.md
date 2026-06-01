# AGENTS.md — postprocess/

Pacote Python de pós-processamento `lotsaltpost`.

## Estrutura

`
postprocess/
├── lotsaltpost/   # Pacote instalável via pip
│   ├── io.py      # Leitura de resultados
│   ├── compare.py # Comparação novo × legado
│   ├── lot.py     # Gráficos LOT
│   ├── apb.py     # Gráficos APB
│   ├── salt.py    # Gráficos sal
│   ├── plots.py   # Primitivas matplotlib
│   ├── report.py  # Relatório HTML
│   ├── units.py   # Conversão de unidades
│   └── cli.py     # CLI: lotsaltpost run <estudo>
├── scripts/       # Scripts de análise específicos
└── templates/     # Templates HTML/CSS para relatórios
`

## Regras

1. Type hints obrigatórios em toda função pública
2. Evitar caminhos absolutos; usar pathlib.Path
3. Separar leitura / métricas / gráficos / relatório
4. Toda comparação deve produzir tabela de erro
5. Nunca gerar gráfico com dados sintéticos apresentado como resultado real
6. Python aqui é apenas pós-processamento, relatório, gráfico, auditoria ou migração pontual não-runtime
7. Não gerar entradas YAML de produção, não montar `PknInput`/casos runtime e não substituir solver C++
8. Não implementar modelos físicos usados pelo solver; novas físicas pertencem a `include/` + `src/`

## Política C++ first

O fluxo normal do projeto é:

`YAML/JSON → C++ parser → C++ model/runner → C++ writer → CSV/JSON`.

Scripts em `postprocess/` só podem consumir resultados já escritos pelo C++ ou
artefatos de auditoria explicitamente fora do runtime. Relatórios como
`lot_pkn_report.py` começam depois que o C++ já gerou `timeseries.csv` e
`result.json`.

## Subagente recomendado

`postprocess-report` para desenvolvimento e melhorias.
