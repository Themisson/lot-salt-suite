# SKILL: cpp-refactor

Refatora código C++ do projeto lot-salt-suite preservando comportamento numérico.

## Finalidade

- Decomposição de classes monolíticas (ex: APB1da → módulos)
- Extração de parâmetros hard-coded para arquivos de caso YAML
- Modernização para C++20 (concepts, smart pointers, RAII)
- Separação de responsabilidades (solver / IO / física)

## Quando usar

- Para decompor APB1da em módulos menores (Fase 7)
- Para adicionar novos módulos com testes
- Para refatorar código legado COPIADO (não o original)

## Restrições

- Nunca alterar formulação física em conjunto com refatoração estrutural
- Nunca modificar arquivos em legance/ ou external/saltcreep/
- Sempre criar testes de regressão antes de refatorar
- Sempre verificar com ctest e pytest após refatoração

## Entregáveis

1. Módulos C++20 com headers em include/ e implementações em src/
2. Testes Catch2 em tests/cpp/
3. Comparação de resultado pré × pós refatoração
4. Entrada atualizada no CMakeLists.txt

## Riscos a evitar

- Alterar ordem de operações que afete precisão numérica
- Remover estado intermediário necessário para convergência
- Introduzir cópias desnecessárias de dados volumosos
- Quebrar compatibilidade com parser YAML existente
