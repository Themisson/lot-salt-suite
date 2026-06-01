# Auditoria de compatibilidade Eigen do saltcreep

**Data:** 2026-06-01  
**Fase:** 6.10  
**Status:** concluida em modo auditoria, sem migracao automatica

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

## Conclusao tecnica

O `saltcreep` compila, testa e executa seus casos principais auditados com a
copia vendorizada de Eigen preservada. Tambem tolera a presenca de
`include/Eigen` no include path, mas o CMake atual do `saltcreep` ainda da
precedencia a `external/saltcreep/include`.

Assim, a recomendacao desta auditoria e:

```text
RECOMMEND_EXPERIMENTAL_OPTION_ONLY
```

A migracao para `include/Eigen` deve ser feita apenas por opcao explicita de
CMake em fase futura, com prova de ordem de include e comparacao numerica
documentada. Ate la, manter as duas copias preservadas.
