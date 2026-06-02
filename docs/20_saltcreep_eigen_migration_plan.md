# 20. Plano de migracao Eigen do saltcreep

## Decisao atual — apos Fase 6.11

```text
MIGRATION_COMPLETED
```

O Eigen oficial do `lot-salt-suite` e `include/Eigen/`, exposto aos targets
modernos por `lss::eigen`. A copia em `external/saltcreep/include/Eigen/`
permanece preservada como fallback.

A Fase 6.10B provou (com tres provas objetivas) que o saltcreep compila e testa
corretamente com `include/Eigen` via `LSS_SALTCREEP_FORCE_LSS_EIGEN=ON`.

A Fase 6.11 tornou essa configuracao oficial: `external/saltcreep/CMakeLists.txt`
agora auto-detecta o contexto `lot-salt-suite` e ativa `include/Eigen` por
padrao, sem necessidade de passar `-DLSS_SALTCREEP_FORCE_LSS_EIGEN=ON`
explicitamente. O build standalone fora da arvore `lot-salt-suite` usa Eigen
interno (`internal fallback`) sem alteracao.

**Resultado da Fase 6.11:**
- build migrado (auto-detect ON): 126/126 Catch2 passaram
- caso APB `mud_gradient_1d_8p5ppg.yaml`: `closure=0.300817%` (identico ao baseline)
- lot-salt-suite: 47/47 Catch2, validates OK, run lot-pkn OK
- `external/saltcreep/include/Eigen/` preservado e intocado

## Opcoes avaliadas

| Opcao | Descricao | Beneficio | Risco | Decisao |
|-------|-----------|-----------|-------|---------|
| A | Manter `external/saltcreep/include/Eigen` para builds do saltcreep | Preserva estabilidade e historico de validacao | Duplica Eigen no repositorio | Aceita como fallback (preservado) |
| B | Forcar `include/Eigen` via `CMAKE_CXX_FLAGS` (Fase 6.10) | Teste rapido sem editar `external/saltcreep` | Nao garante precedencia no Visual Studio — provado nao funcionar | Descartada |
| C | Opcao CMake `LSS_SALTCREEP_FORCE_LSS_EIGEN` com proxy dir (Fase 6.10B) | Prova reprodutivel e reversivel; funciona no VS | Proxy copiado no build dir; nao automaticamente sincronizado | Implementada e validada |
| D | Auto-deteccao de contexto `lot-salt-suite` com default `ON` (Fase 6.11) | Ativacao automatica sem flag; standalone preservado | Nenhum risco adicional — fallback intacto | **Implementada e migrada** |

## Opcao implementada — Fase 6.11 (migrado oficial)

A Fase 6.11 substituiu o default `OFF` por auto-deteccao:

```cmake
# Auto-detect whether we're being built within the lot-salt-suite tree
get_filename_component(_LSS_AUTO_DETECT_INCLUDE
    "${CMAKE_CURRENT_SOURCE_DIR}/../../include" ABSOLUTE)
if(EXISTS "${_LSS_AUTO_DETECT_INCLUDE}/Eigen")
    set(_LSS_EIGEN_AUTO_DEFAULT ON)
else()
    set(_LSS_EIGEN_AUTO_DEFAULT OFF)
endif()

option(LSS_SALTCREEP_FORCE_LSS_EIGEN
    "Use lot-salt-suite root include/Eigen instead of vendored copy (auto ON within lot-salt-suite)"
    ${_LSS_EIGEN_AUTO_DEFAULT})
```

Comportamento resultante:
- Dentro de `lot-salt-suite` (padrao): `include/Eigen` ativo, proxy criado, macro `lss`.
- Fora de `lot-salt-suite` (standalone): Eigen interno preservado, macro `internal`.
- Override manual: `-DLSS_SALTCREEP_FORCE_LSS_EIGEN=OFF` para forcar fallback.

Mensagem de status:
- Padrao (dentro de lot-salt-suite): `Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at ...)`
- Fallback: `Saltcreep Eigen mode: internal fallback (external/saltcreep/include/Eigen)`

## Opcao anterior — Fase 6.10B

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

## Proximo passo — Fase 7 (SaltCreepInterface)

A migracao Eigen esta completa. A Fase 7 pode prosseguir:

1. Implementar `SaltCreepInterface` / `SaltCreepSaltcreepAdapter` em C++.
2. O adapter deve usar `lss::eigen` para seus proprios tipos; o saltcreep
   continuara usando `include/Eigen` por auto-deteccao.
3. A duplicacao de Eigen (proxy em build dir) e aceitavel ate que o adapter
   estabilize — neste ponto, a eliminacao do `external/saltcreep/include/Eigen`
   pode ser avaliada como tarefa separada com escopo explicito.
