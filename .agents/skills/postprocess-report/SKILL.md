---
name: postprocess-report
description: Improve Python postprocessing and generate diagnostic plots, comparison reports, HTML summaries, and publication-ready figures from lot-salt-suite CSV and JSON outputs.
---

# SKILL: postprocess-report

Melhora o pós-processamento Python e gera relatórios para o lot-salt-suite.

## Finalidade

- Desenvolver/melhorar o pacote postprocess/lotsaltpost/
- Criar gráficos: curva LOT P×V, pressão APB ×t, deslocamento radial, fluência
- Gerar relatórios HTML com gráficos embutidos
- Exportar figuras para artigo (SVG, PDF vetorizado)

## Quando usar

- Ao adicionar novo tipo de saída ao solver
- Para criar gráficos comparativos legado × novo
- Para gerar relatório técnico de validação
- Para preparar figuras de publicação

## Restrições

- Não alterar resultados numéricos (apenas leitura e visualização)
- Evitar caminhos absolutos; usar pathlib.Path
- Manter separação: io.py / compare.py / plots.py / report.py
- Toda comparação deve produzir tabela de erro

## Entregáveis

1. Módulos Python em postprocess/lotsaltpost/
2. Scripts em postprocess/scripts/
3. Testes pytest em tests/python/
4. Relatório HTML gerado a partir de dados reais (nunca sintéticos)

## Riscos a evitar

- Gerar gráfico com dados simulados/fictícios apresentado como resultado real
- Hardcode de caminhos absolutos
- Dependências não documentadas no pyproject.toml
