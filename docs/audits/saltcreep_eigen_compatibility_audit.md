# Auditoria de compatibilidade Eigen do saltcreep

**Data:** 2026-06-01 (auditoria) / 2026-06-01 (prova forcada — Fase 6.10B)  
**Fase:** 6.10 / 6.10B  
**Status:** PROVEN_SAFE_TO_MIGRATE

## Objetivo

Verificar se `external/saltcreep/` pode ser compilado e executado sem degradacao
aparente quando se considera o Eigen oficial do `lot-salt-suite` em
`include/Eigen/`, preservando a copia vendorizada existente em
`external/saltcreep/include/Eigen/`.

Nenhum arquivo em `external/saltcreep/`, `legance/`, `legacy/` ou
`tests/baselines/` foi alterado.

## Inventario Eigen

O `saltcreep` inclui Eigen diretamente em headers e fontes C++:

| Area | Arquivos observados |
|------|--------------------|
| Tipos base | `external/saltcreep/include/types.hpp` |
| Elementos | `include/elements/*.hpp`, `src/elements/axisym_2d_aq9.cpp` |
| Solver | `include/solver/*.hpp`, `src/solver/ImplicitAdaptiveIntegrator.cpp` |
| Termico | `include/thermal/*.hpp`, `src/thermal/conduction_2d_field.cpp` |
| Malha/erro | `include/mesh/mesh_refiner.hpp`, `src/mesh/error_estimator.cpp` |
| I/O VTU | `include/io/VtuWriter.hpp` |
| Testes | `tests/cpp/q4_test_helpers.hpp` |

Includes usados:

```text
<Eigen/Core>
<Eigen/Sparse>
<Eigen/SparseCholesky>
<Eigen/Cholesky>
<Eigen/LU>
```

O CMake do `saltcreep` cria os targets `saltcreep` e `tests_unit` com:

```cmake
target_include_directories(saltcreep PRIVATE include)
target_include_directories(tests_unit PRIVATE include)
```

Logo, no estado atual, `external/saltcreep/include/Eigen/` continua tendo
precedencia natural para builds do proprio `saltcreep`.

## Builds executados

### Baseline vendorizado

```powershell
cmake -S external/saltcreep -B external/saltcreep/build_baseline -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build external/saltcreep/build_baseline -j
ctest --test-dir external/saltcreep/build_baseline --output-on-failure -j 4
```

Resultado:

```text
100% tests passed, 0 tests failed out of 125
Total Test time (real) = 1028.24 sec
```

### Build experimental com `include/Eigen` no include path

```powershell
cmake -S external/saltcreep -B external/saltcreep/build_lss_eigen -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "-DCMAKE_CXX_FLAGS=-IC:/Users/themi/Desktop/lot-salt-suite/include"
cmake --build external/saltcreep/build_lss_eigen -j
ctest --test-dir external/saltcreep/build_lss_eigen --output-on-failure -j 4
```

Resultado:

```text
100% tests passed, 0 tests failed out of 125
Total Test time (real) = 1020.63 sec
```

Observacao importante: com o gerador Visual Studio, o arquivo `.vcxproj` gerado
ainda lista `external/saltcreep/include` antes de `C:/Users/themi/Desktop/lot-salt-suite/include`.
Portanto, este build confirma compatibilidade do estado atual e da convivencia
dos include paths, mas **nao prova** que o `saltcreep` foi de fato compilado
contra `include/Eigen` em vez da copia vendorizada.

## Casos executados

Os casos foram rodados a partir de diretorios temporarios sob `tmp/`, para evitar
sobrescrever `external/saltcreep/results/`.

```powershell
..\..\external\saltcreep\build_baseline\Debug\saltcreep.exe ..\..\external\saltcreep\cases\tcc\lame_test.yaml
..\..\external\saltcreep\build_baseline\Debug\saltcreep.exe ..\..\external\saltcreep\cases\apb\mud_gradient_1d_8p5ppg.yaml
..\..\external\saltcreep\build_lss_eigen\Debug\saltcreep.exe ..\..\external\saltcreep\cases\tcc\lame_test.yaml
..\..\external\saltcreep\build_lss_eigen\Debug\saltcreep.exe ..\..\external\saltcreep\cases\apb\mud_gradient_1d_8p5ppg.yaml
```

Resultados principais:

| Build | Caso | Resultado |
|-------|------|-----------|
| baseline | `lame_test.yaml` | `Output: "results\\lame_test\\displacements.csv"` |
| baseline | `mud_gradient_1d_8p5ppg.yaml` | `[time] t=2h  closure=0.300817%` |
| experimental | `lame_test.yaml` | `Output: "results\\lame_test\\displacements.csv"` |
| experimental | `mud_gradient_1d_8p5ppg.yaml` | `[time] t=2h  closure=0.300817%` |

## Conclusao tecnica — Fase 6.10

O `saltcreep` compila, testa e executa seus casos principais auditados com a
copia vendorizada de Eigen preservada. Tambem tolerou a presenca de
`include/Eigen` no include path via `CMAKE_CXX_FLAGS`, mas o CMake (gerador
Visual Studio) ainda dava precedencia a `external/saltcreep/include`.

---

## Fase 6.10B — Prova forcada do Eigen oficial (2026-06-01)

### Objetivo

Provar tecnicamente que o `saltcreep` pode ser compilado e testado usando de
fato `include/Eigen` — em vez da copia vendorizada — via opcao CMake real.

### Opcao implementada

```cmake
option(LSS_SALTCREEP_FORCE_LSS_EIGEN
    "Force saltcreep to use lot-salt-suite root include/Eigen (BEFORE PRIVATE)" OFF)
```

Padrao `OFF` preserva o comportamento validado. Quando `ON`:

1. O CMake cria `${CMAKE_BINARY_DIR}/lss_eigen_proxy/` contendo apenas
   `Eigen/` (copiado de `include/Eigen/`).
2. O proxy e adicionado com `BEFORE PRIVATE` aos targets `saltcreep` e
   `tests_unit`, antes de `PRIVATE include` (que contem a copia vendorizada).
3. O compilador encontra `<Eigen/Core>` no proxy primeiro.
4. Os includes relativos do saltcreep (ex: `"io/CaseParser.hpp"`) nao sao
   afetados porque o proxy contem apenas `Eigen/`.

### Provas objetivas

**Prova 1 — CMake configure:**

```text
-- Saltcreep Eigen mode: lot-salt-suite include/Eigen
   (proxy at .../build_lss_eigen/lss_eigen_proxy/Eigen)
```

vs. baseline:

```text
-- Saltcreep Eigen mode: internal (external/saltcreep/include/Eigen)
```

**Prova 2 — `AdditionalIncludeDirectories` no `tests_unit.vcxproj`:**

Baseline (`OFF`):
```
external\saltcreep\include;                 ← PRIMEIRO (Eigen vendorizado)
...catch2...yaml-cpp...
```

Forcado (`ON`):
```
build_lss_eigen\lss_eigen_proxy;            ← PRIMEIRO (LSS Eigen via proxy)
external\saltcreep\include;                 ← SEGUNDO (Eigen vendorizado — shadow)
...catch2...yaml-cpp...
```

O Visual Studio usara `lss_eigen_proxy/Eigen/Core` ao compilar `#include <Eigen/Core>`.

**Prova 3 — macro runtime `LSS_SALTCREEP_EIGEN_MODE`:**

O CMake define `LSS_SALTCREEP_EIGEN_MODE="lss"` ou `"internal"` conforme a
opcao. O `test_eigen_source` confirma em runtime:

| Build | Saida do test |
|-------|---------------|
| baseline | `LSS_SALTCREEP_EIGEN_MODE = internal` |
| forcado  | `LSS_SALTCREEP_EIGEN_MODE = lss`      |

### Builds e testes executados

| Build | Opcao | CMake msg | tests_unit.vcxproj | Macro runtime | ctest | Tempo |
|-------|-------|-----------|-------------------|---------------|-------|-------|
| `build_baseline` | `OFF` | internal | saltcreep/include PRIMEIRO | internal | 126/126 | 996.27 s |
| `build_lss_eigen` | `ON` | lss (proxy) | lss_eigen_proxy PRIMEIRO | lss | 126/126 | 1024.06 s |

### Caso APB

| Build | Caso | Resultado |
|-------|------|-----------|
| baseline | `mud_gradient_1d_8p5ppg.yaml` | `closure=0.300817%` |
| forcado  | `mud_gradient_1d_8p5ppg.yaml` | `closure=0.300817%` |

Resultados identicos.

### Decisao final

```text
PROVEN_SAFE_TO_MIGRATE
```

Criterios atendidos:
- [x] build forcado realmente usou `include/Eigen` (tres provas objetivas);
- [x] 126/126 testes Catch2 passaram no build forcado;
- [x] caso APB manteve `closure=0.300817%` (identico ao baseline);
- [x] nenhum arquivo/result/baseline foi alterado.

A copia vendorizada `external/saltcreep/include/Eigen/` permanece preservada.
O proxy `lss_eigen_proxy/` criado no build dir e ignorado pelo git (esta em
`external/saltcreep/build_lss_eigen/`). Nenhum dado de regressao foi
sobrescrito.
