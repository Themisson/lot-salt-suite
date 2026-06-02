# 21. Resultado da migração Eigen do saltcreep

**Data:** 2026-06-01  
**Fase:** 6.11  
**Decisão:** `MIGRATION_COMPLETED`

## Resumo

A Fase 6.11 converteu a prova experimental da Fase 6.10B em configuração oficial.
O `external/saltcreep/CMakeLists.txt` agora auto-detecta o contexto `lot-salt-suite`
e ativa `include/Eigen` por padrão, sem necessidade de flags manuais.

## Configuração final

### Auto-detecção implementada

```cmake
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

### Comportamento resultante

| Contexto | Default | Eigen ativo | Macro runtime |
|----------|---------|-------------|---------------|
| Dentro de `lot-salt-suite` | `ON` (auto) | `include/Eigen` via proxy | `lss` |
| Standalone fora da árvore | `OFF` (auto) | `external/saltcreep/include/Eigen` | `internal` |
| Override manual `OFF` | `OFF` (explícito) | `external/saltcreep/include/Eigen` | `internal` |

### Mensagens de status

Modo integrado (padrão dentro de lot-salt-suite):
```text
-- Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at .../lss_eigen_proxy/Eigen)
```

Fallback (standalone ou override):
```text
-- Saltcreep Eigen mode: internal fallback (external/saltcreep/include/Eigen)
```

## Rollback

Para usar o Eigen interno como fallback explícito:

```powershell
cmake -S external/saltcreep -B external/saltcreep/build_fallback -DLSS_SALTCREEP_FORCE_LSS_EIGEN=OFF
```

Critérios de rollback (reativar se ocorrer):
- falha de compilação em MSVC, GCC ou Clang;
- falha em teste Catch2 do `saltcreep`;
- diferença numérica não explicada em fechamento, deslocamento, tensão ou dano;
- necessidade de alterar modelo constitutivo para compilar;
- conflito com o contrato de adapter C++.

## Testes executados — Fase 6.11

### Build migrado (auto-detecção ON, sem flag manual)

```powershell
cmake -S external/saltcreep -B external/saltcreep/build_migrated_lss_eigen -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build external/saltcreep/build_migrated_lss_eigen -j
ctest --test-dir external/saltcreep/build_migrated_lss_eigen --output-on-failure -j 4
```

Resultado:
```text
100% tests passed, 0 tests failed out of 126
```

### Prova 1 — CMake configure

```text
-- Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at .../build_migrated_lss_eigen/lss_eigen_proxy/Eigen)
-- Configuring done
```

### Prova 2 — AdditionalIncludeDirectories no vcxproj

```text
lss_eigen_proxy;                              ← PRIMEIRO (LSS Eigen via proxy)
external\saltcreep\include;                   ← SEGUNDO (Eigen vendorizado — shadow)
...catch2...yaml-cpp...
```

### Prova 3 — Macro runtime

```text
[eigen_source] LSS_SALTCREEP_EIGEN_MODE = lss
[eigen_source] EIGEN_VERSION_STRING      = 5.0.0
All tests passed (1 assertion in 1 test case)
```

## Resultado APB

| Build | Caso | Resultado | Status |
|-------|------|-----------|--------|
| baseline (Fase 6.10B) | `mud_gradient_1d_8p5ppg.yaml` | `closure=0.300817%` | referência |
| migrado (Fase 6.11) | `mud_gradient_1d_8p5ppg.yaml` | `closure=0.300817%` | **idêntico** |

## Resultado lot-salt-suite

```text
100% tests passed, 0 tests failed out of 47
```

Validates:
- `lot_pkn_minimal.yaml` → `OK: lot_pkn_minimal_validation`
- `lot_pkn_with_leakoff.yaml` → `OK: lot_pkn_with_leakoff_validation`
- `buz67d_pkn.yaml` → `OK: buz67d_pkn_migrated_contract`

Run:
- `lot-sim run --case lot_pkn_minimal.yaml --mode lot-pkn --output results/lot_pkn_minimal_saltcreep_eigen_migrated` → `OK`

## Preservação do Eigen vendorizado

`external/saltcreep/include/Eigen/` permanece intacto. Confirmação:

```text
nenhum arquivo em external/saltcreep/include/Eigen/ foi alterado ou removido.
```

O proxy em `build_migrated_lss_eigen/lss_eigen_proxy/` contém uma cópia de
`include/Eigen/` criada em tempo de configure, no build dir (ignorado pelo git).

## Riscos remanescentes

| Risco | Severidade | Mitigação |
|-------|------------|-----------|
| Proxy não sincronizado se `include/Eigen` mudar | Baixo | Novo configure recria o proxy; o `if(NOT EXISTS ...)` previne sobrescrita acidental mas não atualiza — para forçar sincronização, apagar o proxy e reconfigurar |
| Build standalone fora de lot-salt-suite usa Eigen interno (sem validação Fase 6.10B) | Informativo | Comportamento esperado; saltcreep standalone usa seu próprio Eigen com o qual foi originalmente testado |
| Duplicação de Eigen persiste no repositório | Baixo | Aceita até adapter `SaltCreepSaltcreepAdapter` estabilizar; remoção de `external/saltcreep/include/Eigen/` é escopo futuro explícito |

## Recomendação para Fase 7

Com a migração Eigen concluída:

1. Implementar `SaltCreepInterface` C++ abstrata em `include/salt/SaltCreepInterface.hpp`.
2. Implementar `SaltCreepSaltcreepAdapter` em `src/salt/` integrando `external/saltcreep/`.
3. O adapter deve usar `lss::eigen` para seus próprios tipos; o saltcreep continuará com `include/Eigen` por auto-detecção.
4. Quando o adapter estabilizar e os testes de integração passarem, avaliar remoção de `external/saltcreep/include/Eigen/` como tarefa separada.
5. Não implementar nenhuma física nova antes do adapter ter testes Catch2 cobrindo a interface.
