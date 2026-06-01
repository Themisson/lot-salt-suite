# 14 — Guia do Desenvolvedor

**Status:** Planejado | **Última atualização:** 2026-06-01

## Fluxo de trabalho

### Adicionar um novo módulo C++

1. Criar `include/<modulo>/<Modulo>.hpp` com interface pública
2. Criar `src/<modulo>/<Modulo>.cpp` com implementação
3. Criar `tests/cpp/test_<modulo>.cpp` com Catch2 (mínimo 3 testes)
4. Adicionar ao `CMakeLists.txt`
5. Verificar com `cmake --build build -j && ctest`
6. Atualizar `docs/07_target_architecture.md`
7. Executar `python tools/generate_docs_index.py`

### Migrar um caso legado

1. Ler o arquivo `.cpp` ou `.json` com `legacy-explorer`
2. Extrair parâmetros com `tools/migrate_*.py`
3. Criar YAML em `cases/`
4. Validar com `lot-sim inspect --case <arquivo.yaml>`
5. Executar com `lot-sim run`
6. Comparar com baseline (se existir)
7. Documentar em `docs/09_migration_plan.md`

### Atualizar docs/index.html

1. Editar o arquivo `.md` relevante em `docs/`
2. Atualizar `tools/docs_status.yaml` se o status mudou
3. Executar `python tools/generate_docs_index.py`
4. Verificar que index.html abre sem erro no browser

### Antes de qualquer PR/commit

1. `cmake --build build -j` — zero erros
2. `ctest --test-dir build --output-on-failure` — 100% verde
3. `pytest tests/python -q` — 100% verde
4. Revisar `docs/08_known_issues.md` — nenhum risco novo sem documentação

## Skills disponíveis

| Skill | Quando usar |
|-------|------------|
| `/formulation-audit` | Antes de implementar qualquer módulo físico |
| `/cpp-refactor` | Para refatoração C++ |
| `/validation-benchmark` | Para criar/executar testes de regressão |
| `/postprocess-report` | Para pós-processamento Python |
| `/docs-html-report` | Para atualizar documentação |
| `/lot-salt-integration` | Para integração LOT+sal |
