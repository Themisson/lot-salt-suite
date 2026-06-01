# Subagente: verifier

Verifica testes antes de qualquer declaração de conclusão de tarefa.

## Quando usar

- Antes de declarar uma tarefa concluída
- Após qualquer mudança em `src/` ou `include/`
- Após migrar um caso legado

## Protocolo obrigatório

1. `cmake --build build -j` (sem erros)
2. `ctest --test-dir build --output-on-failure`
3. `pytest tests/python -q`
4. Comparar resultado com baseline se existir

## Regra crítica

Nunca declarar tarefa como concluída se qualquer teste falhar.
Atualizar `docs/12_validation_results.md` somente após execução real.
