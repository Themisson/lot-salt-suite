---
name: validation-benchmark
description: Create, run, and review lot-salt-suite validation tests, regression benchmarks, legacy-modern comparisons, baselines, and documented validation metrics.
---

# SKILL: validation-benchmark

Cria, executa e revisa testes de regressão e benchmarks para o lot-salt-suite.

## Finalidade

- Capturar baselines de resultados dos legados
- Comparar resultados novo × legado com métricas de erro
- Executar suíte de validação V0-V9 (docs/06_validation_plan.md)
- Gerar relatório de validação em docs/12_validation_results.md

## Quando usar

- Antes de qualquer refatoração (capturar baseline)
- Após migrar um caso (comparar com baseline)
- Para validar novo módulo contra solução analítica
- Para gerar relatório periódico de regressão

## Restrições

- NUNCA atualizar docs/12_validation_results.md sem executar os testes
- NUNCA relaxar tolerâncias de regressão sem aprovação
- Baselines em tests/baselines/ são imutáveis (alterar apenas com aprovação)
- Nunca comparar resultados de versões diferentes de compilador sem documentar

## Entregáveis

1. Baselines em tests/baselines/<caso>.json
2. Tabela de erro (L2, L∞, diferença máxima) por campo e caso
3. Seção em docs/12_validation_results.md com outputs reais
4. Status atualizado em tools/docs_status.yaml

## Riscos a evitar

- Declarar validação como executada sem outputs reais documentados
- Usar tolerância muito larga que mascare divergências reais
- Comparar casos com parâmetros de solver diferentes
