cmake_minimum_required(VERSION 3.20)
project(lot_salt_suite CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ============================================================
# Opções de build
# ============================================================
option(LSS_BUILD_TESTS "Build unit tests" ON)
option(LSS_BUILD_APPS  "Build lot-sim executable" ON)
option(LSS_ENABLE_OPENMP "Enable OpenMP parallelism" OFF)
option(LSS_ENABLE_CLI_SUBPROCESS_TESTS "Enable tests that execute lot-sim as a subprocess" ON)

# ============================================================
# Dependências externas via FetchContent
# ============================================================
include(FetchContent)

# CMake 4 compatibility: yaml-cpp calls cmake_minimum_required with a version
# below the CMake 4 threshold. CMAKE_POLICY_VERSION_MINIMUM raises the floor so
# configure succeeds without a manual -DCMAKE_POLICY_VERSION_MINIMUM flag.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5 CACHE STRING
    "Minimum CMake policy version for legacy FetchContent dependencies" FORCE)

# yaml-cpp
FetchContent_Declare(
  yaml-cpp
  GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
  GIT_TAG        0.8.0
)
set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(yaml-cpp)
if(TARGET yaml-cpp)
  target_compile_options(yaml-cpp PRIVATE $<$<CXX_COMPILER_ID:GNU>:-include cstdint>)
endif()

# Catch2 v3 (apenas se testes habilitados)
if(LSS_BUILD_TESTS)
  FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.5.2
  )
  FetchContent_MakeAvailable(Catch2)
  include(CTest)
  include(Catch)
endif()

# ============================================================
# Eigen header-only para cálculos do simulador
# ============================================================
# include/Eigen e o Eigen oficial do lot-salt-suite.
# external/saltcreep/include/Eigen permanece preservado para o saltcreep.
set(LSS_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/include")
add_library(lss_eigen INTERFACE)
add_library(lss::eigen ALIAS lss_eigen)
target_include_directories(lss_eigen INTERFACE
  ${LSS_INCLUDE_DIR}
)

# ============================================================
# OpenMP (opcional)
# ============================================================
if(LSS_ENABLE_OPENMP)
  find_package(OpenMP)
endif()

# ============================================================
# Sources dos módulos
# ============================================================
# TODO Fase 7: adicionar src/wellbore/*.cpp, src/fluids/*.cpp, etc.

set(LSS_CORE_SOURCES
  src/io/CaseParser.cpp
  src/io/ResultWriter.cpp
  src/lot/BreakdownDetector.cpp
  src/lot/LeakoffModel.cpp
  src/lot/PknModel.cpp
  src/lot/PknRunner.cpp
  src/salt/SaltCreepInterface.cpp
  src/salt/SaltCreepSaltcreepAdapter.cpp
)

# ============================================================
# Executável principal (Fase 5+)
# ============================================================
if(LSS_BUILD_APPS AND LSS_CORE_SOURCES)
  add_executable(lot-sim apps/lot-sim.cpp ${LSS_CORE_SOURCES})
  target_include_directories(lot-sim PRIVATE
    ${LSS_INCLUDE_DIR}
  )
  target_link_libraries(lot-sim PRIVATE yaml-cpp lss::eigen)
  if(LSS_ENABLE_OPENMP AND OpenMP_CXX_FOUND)
    target_link_libraries(lot-sim PRIVATE OpenMP::OpenMP_CXX)
  endif()
endif()

# ============================================================
# Testes (Fase 5+)
# ============================================================
if(LSS_BUILD_TESTS)
  add_executable(lot_sim_tests
    tests/cpp/test_units.cpp
    tests/cpp/test_case_parser.cpp
    tests/cpp/test_breakdown_detector.cpp
    tests/cpp/test_leakoff_model.cpp
    tests/cpp/test_pkn_model_synthetic.cpp
    tests/cpp/test_pkn_runner.cpp
    tests/cpp/test_result_writer.cpp
    tests/cpp/test_salt_creep_interface.cpp
    tests/cpp/test_salt_creep_saltcreep_adapter.cpp
    ${LSS_CORE_SOURCES}
  )
  target_include_directories(lot_sim_tests PRIVATE
    ${LSS_INCLUDE_DIR}
  )
  target_link_libraries(lot_sim_tests PRIVATE Catch2::Catch2WithMain yaml-cpp lss::eigen)
  if(LSS_ENABLE_CLI_SUBPROCESS_TESTS)
    target_compile_definitions(lot_sim_tests PRIVATE LSS_ENABLE_CLI_SUBPROCESS_TESTS=1)
  else()
    target_compile_definitions(lot_sim_tests PRIVATE LSS_ENABLE_CLI_SUBPROCESS_TESTS=0)
  endif()
  if(TARGET lot-sim)
    # Pass the absolute executable path via generator expression so CLI tests
    # locate lot-sim.exe correctly for both single-config and multi-config
    # (Visual Studio) generators without hard-coding the Debug/Release subdir.
    target_compile_definitions(lot_sim_tests PRIVATE
      LSS_LOT_SIM_EXECUTABLE="$<TARGET_FILE:lot-sim>"
    )
    add_dependencies(lot_sim_tests lot-sim)
  endif()
  # PRE_TEST defers test discovery to ctest time instead of MSBuild post-build,
  # which avoids the "unknown error" crash in Visual Studio multi-config generators.
  catch_discover_tests(lot_sim_tests
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    DISCOVERY_MODE PRE_TEST
  )

  set(LSS_SALTCREEP_CONTROLLED_EIGEN_PROXY_DIR
      "${CMAKE_BINARY_DIR}/lss_saltcreep_controlled_eigen_proxy")
  file(MAKE_DIRECTORY "${LSS_SALTCREEP_CONTROLLED_EIGEN_PROXY_DIR}")
  if(NOT EXISTS "${LSS_SALTCREEP_CONTROLLED_EIGEN_PROXY_DIR}/Eigen")
    file(COPY "${LSS_INCLUDE_DIR}/Eigen"
         DESTINATION "${LSS_SALTCREEP_CONTROLLED_EIGEN_PROXY_DIR}")
  endif()

  set(LSS_SALTCREEP_CONTROLLED_SOURCES
    external/saltcreep/src/constitutive/elastic_isotropic.cpp
    external/saltcreep/src/elements/axisym_1d_L3.cpp
    external/saltcreep/src/solver/Assembler.cpp
    external/saltcreep/src/solver/ElasticSolver.cpp
    external/saltcreep/src/solver/WallPressureField.cpp
  )

  add_executable(saltcreep_backend_controlled_tests
    tests/cpp/test_saltcreep_backend_controlled_case.cpp
    ${LSS_SALTCREEP_CONTROLLED_SOURCES}
  )
  target_include_directories(saltcreep_backend_controlled_tests
    BEFORE PRIVATE
      ${LSS_SALTCREEP_CONTROLLED_EIGEN_PROXY_DIR}
  )
  target_include_directories(saltcreep_backend_controlled_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/external/saltcreep/include
  )
  target_link_libraries(saltcreep_backend_controlled_tests PRIVATE
    Catch2::Catch2WithMain
  )
  catch_discover_tests(saltcreep_backend_controlled_tests
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    DISCOVERY_MODE PRE_TEST
  )

  set(LSS_SALTCREEP_TIME_GEOSTATIC_SOURCES
    ${LSS_SALTCREEP_CONTROLLED_SOURCES}
    external/saltcreep/src/constitutive/double_mechanism.cpp
    external/saltcreep/src/io/VtuWriter.cpp
    external/saltcreep/src/solver/DamageDiagnostics.cpp
    external/saltcreep/src/solver/TimeIntegrator.cpp
    external/saltcreep/src/solver/TimeOutput.cpp
    external/saltcreep/src/thermal/profile_field.cpp
  )

  add_executable(saltcreep_backend_time_geostatic_tests
    tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp
    ${LSS_SALTCREEP_TIME_GEOSTATIC_SOURCES}
  )
  target_include_directories(saltcreep_backend_time_geostatic_tests
    BEFORE PRIVATE
      ${LSS_SALTCREEP_CONTROLLED_EIGEN_PROXY_DIR}
  )
  target_include_directories(saltcreep_backend_time_geostatic_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/external/saltcreep/include
  )
  target_link_libraries(saltcreep_backend_time_geostatic_tests PRIVATE
    Catch2::Catch2WithMain
  )
  catch_discover_tests(saltcreep_backend_time_geostatic_tests
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    DISCOVERY_MODE PRE_TEST
  )
endif()

message(STATUS "lot-salt-suite configured. C++20, yaml-cpp, Eigen from include/Eigen.")
message(STATUS "Modules will be populated from Fase 5 onwards.")
