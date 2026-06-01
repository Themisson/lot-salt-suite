# 10 — Plano de Pós-Processamento

**Status:** Planejado | **Última atualização:** 2026-06-01

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
| `plot_lot_curve.py` | Curva LOT P×V e P×t |
| `plot_apb_pressure.py` | Pressão anular ×t |
| `compare_legado_novo.py` | Tabela de erro legado × novo |
| `plot_salt_closure.py` | Fechamento de poço ×t |
| `plot_coupled.py` | Painel completo |
| `generate_article_figures.py` | Figuras para publicação |
