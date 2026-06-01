# Subagente: docs-sync

Atualiza `docs/index.html` e arquivos docs/*.md após cada etapa.

## Quando usar

- Ao final de qualquer fase que modifique API pública
- Após adicionar novo módulo, skill ou caso
- Após executar validações (para atualizar resultados reais)

## Protocolo

1. Verificar `tools/docs_status.yaml` para status atual de cada seção
2. Atualizar apenas seções relevantes à tarefa concluída
3. Executar `python tools/generate_docs_index.py`
4. Verificar que index.html abre sem erros no browser

## Regras críticas

- Status `validated` somente após execução documentada com output real
- Não modificar `docs/12_validation_results.md` sem resultados de execução
- Atualizar contagem de testes no hero stats do index.html
