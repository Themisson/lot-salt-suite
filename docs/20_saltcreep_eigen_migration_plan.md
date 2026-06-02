# 20. Plano de migracao Eigen do saltcreep

## Decisao atual — apos Fase 6.10B

```text
PROVEN_SAFE_TO_MIGRATE
```

O Eigen oficial do `lot-salt-suite` e `include/Eigen/`, exposto aos targets
modernos por `lss::eigen`. A copia em `external/saltcreep/include/Eigen/`
permanece preservada. A Fase 6.10B provou que o saltcreep compila (build
forcado) e testa (126/126 Catch2) e executa o caso APB com resultado identico
(`closure=0.300817%`) quando forcado a usar `include/Eigen` via opcao CMake
`LSS_SALTCREEP_FORCE_LSS_EIGEN=ON`.

## Opcoes avaliadas

| Opcao | Descricao | Beneficio | Risco | Decisao |
|-------|-----------|-----------|-------|---------|
| A | Manter `external/saltcreep/include/Eigen` para builds do saltcreep | Preserva estabilidade e historico de validacao | Duplica Eigen no repositorio | Aceita por enquanto (baseline) |
| B | Forcar `include/Eigen` via `CMAKE_CXX_FLAGS` (Fase 6.10) | Teste rapido sem editar `external/saltcreep` | Nao garante precedencia no Visual Studio — provado nao funcionar | Descartada |
| C | Opcao CMake `LSS_SALTCREEP_FORCE_LSS_EIGEN` com proxy dir (Fase 6.10B) | Prova reprodutivel e reversivel; funciona no VS | Proxy copiado no build dir; nao automaticamente sincronizado | Implementada e validada |

## Opcao implementada — Fase 6.10B

```cmake
option(LSS_SALTCREEP_FORCE_LSS_EIGEN
    "Force saltcreep to use lot-salt-suite root include/Eigen (BEFORE PRIVATE)" OFF)
```

Mecanismo: um diretorio proxy `${CMAKE_BINARY_DIR}/lss_eigen_proxy/` e criado
com apenas `Eigen/` (copiado de `include/Eigen/`). O proxy e prepended com
`BEFORE PRIVATE` antes de `PRIVATE include` em ambos os targets `saltcreep` e
`tests_unit`. Os includes relativos do saltcreep (ex: `"io/CaseParser.hpp"`)
continuam resolvendo para `external/saltcreep/include/` normalmente.

Arquivo de teste criado: `external/saltcreep/tests/test_eigen_source.cpp`
(usa macro `LSS_SALTCREEP_EIGEN_MODE` para confirmar o modo em runtime).

## Criterios de rollback

Desativar a opcao experimental e voltar ao Eigen vendorizado se ocorrer qualquer
um destes sinais:

- falha de compilacao em MSVC, GCC ou Clang;
- falha em teste Catch2 do `saltcreep`;
- diferenca numerica nao explicada em fechamento, deslocamento, tensao ou dano;
- necessidade de alterar modelo constitutivo para compilar;
- conflito com o contrato de adapter C++.

## Proximo passo — Fase 6.11

A decisao `PROVEN_SAFE_TO_MIGRATE` esta registrada. A Fase 6.11 pode prosseguir:

1. Implementar `SaltCreepInterface` / `SaltCreepSaltcreepAdapter` em C++.
2. Quando o adapter entrar no build principal do `lot-salt-suite`, ativar
   `LSS_SALTCREEP_FORCE_LSS_EIGEN=ON` por padrao (ou via `lss::eigen`),
   eliminando a duplicacao de Eigen no longo prazo.
3. Ate la, a opcao permanece `OFF` por padrao para preservar o baseline.
