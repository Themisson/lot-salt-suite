---
name: docs-html-report
description: Create and update lot-salt-suite technical Markdown documentation, docs/index.html, docs_status.yaml, validation notes, and project report pages after implementation or audit phases.
---

# SKILL: docs-html-report

Cria e atualiza documentação técnica Markdown e o docs/index.html navegável.

## Finalidade

- Criar e atualizar arquivos docs/*.md
- Regenerar docs/index.html após mudanças de conteúdo ou status
- Manter tools/docs_status.yaml como fonte de verdade
- Sincronizar contagem de testes no hero stats do index.html

## Quando usar

- Após finalizar qualquer fase do projeto
- Ao adicionar novo módulo, modelo ou caso
- Ao executar validações (atualizar resultados reais)
- Para manutenção periódica da documentação

## Restrições

- Status 'validated' somente após CI verde documentado
- Não editar docs/12_validation_results.md sem resultados reais
- Atualizar tools/docs_status.yaml ANTES de regenerar index.html
- Não modificar legance/ ou external/saltcreep/

## Entregáveis

1. Arquivo(s) docs/*.md atualizados
2. tools/docs_status.yaml atualizado
3. docs/index.html regenerado e funcional offline
4. Hero stats com contagem correta de testes

## Riscos a evitar

- Declarar fase como 'validada' antes de executar
- index.html com links quebrados
- Status inconsistente entre docs_status.yaml e index.html
