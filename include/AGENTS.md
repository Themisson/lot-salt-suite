# AGENTS.md — include/

Headers C++20 (interfaces públicas) do projeto lot-salt-suite.

## Regras de headers

1. Sem `using namespace std` em nenhum header
2. Include guards obrigatórios (ou `#pragma once`)
3. Dependências mínimas: preferir forward declarations
4. Eigen: incluir de `external/saltcreep/include/Eigen/` via CMakeLists.txt
5. yaml-cpp: incluir via FetchContent (não hardcode de path)
6. Sem código de implementação em headers (exceto templates inline)

## Não incluir

- Headers de `legance/` em código novo
- Headers de `external/saltcreep/include/apb_code/` em código novo
- Qualquer header que misture parser e física
