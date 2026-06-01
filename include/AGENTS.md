# AGENTS.md — include/

Headers C++20 (interfaces públicas) do projeto lot-salt-suite.

## Regras de headers

1. Sem `using namespace std` em nenhum header
2. Include guards obrigatórios (ou `#pragma once`)
3. Dependências mínimas: preferir forward declarations
4. Eigen: incluir pelo target CMake `lss::eigen`, que aponta para `include/Eigen/`
5. yaml-cpp: incluir via FetchContent (não hardcode de path)
6. Sem código de implementação em headers (exceto templates inline)

## Não incluir

- Headers de `legance/` em código novo
- Headers de `external/saltcreep/include/apb_code/` em código novo
- Qualquer header que misture parser e física
- Qualquer interface que delegue física runtime para scripts Python

## Política C++ first

As interfaces públicas em `include/` definem o núcleo de simulação C++. Parser,
conversão de unidades, modelos, solvers, runners, writers e acoplamento devem
ter contratos C++ explícitos. Python pode consumir as saídas, mas não deve ser
dependência para executar o solver.
