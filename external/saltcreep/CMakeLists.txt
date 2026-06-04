cmake_minimum_required(VERSION 3.20)
project(saltcreep CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

option(ENABLE_SANITIZERS "Build saltcreep targets with available sanitizer flags" OFF)
option(ENABLE_WERROR "Treat compiler warnings as errors for saltcreep targets" OFF)

# ── LSS Eigen integration (Fase 6.11) ─────────────────────────────────────────
# Auto-detect whether saltcreep is being built within the lot-salt-suite tree
# by checking for include/Eigen at the expected relative path (../../include).
# When auto-detected (default ON within lot-salt-suite), saltcreep targets
# resolve <Eigen/...> from a proxy dir containing only that copy, keeping
# include search order correct for saltcreep's own relative headers.
# The vendored copy in external/saltcreep/include/Eigen/ is always preserved.
# Set -DLSS_SALTCREEP_FORCE_LSS_EIGEN=OFF explicitly for standalone builds
# outside the lot-salt-suite tree, or to use the vendored copy as fallback.
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

if(LSS_SALTCREEP_FORCE_LSS_EIGEN)
    if(NOT DEFINED LSS_ROOT_INCLUDE_DIR)
        get_filename_component(LSS_ROOT_INCLUDE_DIR
            "${CMAKE_CURRENT_SOURCE_DIR}/../../include" ABSOLUTE)
    endif()
    if(NOT EXISTS "${LSS_ROOT_INCLUDE_DIR}/Eigen")
        message(FATAL_ERROR
            "LSS_SALTCREEP_FORCE_LSS_EIGEN=ON but Eigen not found at "
            "${LSS_ROOT_INCLUDE_DIR}/Eigen. "
            "Pass -DLSS_SALTCREEP_FORCE_LSS_EIGEN=OFF for standalone builds.")
    endif()
    # Create a proxy directory in the binary dir that contains ONLY Eigen/.
    # This prevents saltcreep's relative includes (e.g. "io/CaseParser.hpp")
    # from resolving to lot-salt-suite headers when BEFORE PRIVATE is used.
    set(LSS_EIGEN_PROXY_DIR "${CMAKE_BINARY_DIR}/lss_eigen_proxy")
    file(MAKE_DIRECTORY "${LSS_EIGEN_PROXY_DIR}")
    if(NOT EXISTS "${LSS_EIGEN_PROXY_DIR}/Eigen")
        file(COPY "${LSS_ROOT_INCLUDE_DIR}/Eigen"
             DESTINATION "${LSS_EIGEN_PROXY_DIR}")
    endif()
    message(STATUS
        "Saltcreep Eigen mode: lot-salt-suite include/Eigen"
        " (proxy at ${LSS_EIGEN_PROXY_DIR}/Eigen)")
    set(LSS_SALTCREEP_EIGEN_MODE_VALUE "lss")
else()
    message(STATUS "Saltcreep Eigen mode: internal fallback (external/saltcreep/include/Eigen)")
    set(LSS_SALTCREEP_EIGEN_MODE_VALUE "internal")
endif()

# MSVC vs GCC/Clang warning flags
if(MSVC)
    add_compile_options(/W4 /wd4100 /FS)  # /FS serializes PDB writes in parallel builds.
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── External dependencies via FetchContent ────────────────────────────────────
include(FetchContent)

FetchContent_Declare(yaml-cpp
    GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
    GIT_TAG        0.8.0
    GIT_SHALLOW    TRUE)
set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(yaml-cpp)
if(TARGET yaml-cpp AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(yaml-cpp PRIVATE -include cstdint)
endif()

FetchContent_Declare(Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.5.2
    GIT_SHALLOW    TRUE)
FetchContent_MakeAvailable(Catch2)

find_package(OpenMP)

set(SALTCREEP_SANITIZER_FLAGS "")
set(SALTCREEP_SANITIZER_LINK_FLAGS "")
if(ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        include(CheckCXXSourceCompiles)
        set(CMAKE_REQUIRED_FLAGS "-fsanitize=address,undefined")
        check_cxx_source_compiles("int main() { return 0; }" SALTCREEP_HAS_ASAN_UBSAN)
        unset(CMAKE_REQUIRED_FLAGS)

        if(SALTCREEP_HAS_ASAN_UBSAN)
            set(SALTCREEP_SANITIZER_FLAGS
                -fsanitize=address,undefined
                -fno-omit-frame-pointer)
            set(SALTCREEP_SANITIZER_LINK_FLAGS
                -fsanitize=address,undefined)
        else()
            message(WARNING
                "ENABLE_SANITIZERS requested, but this compiler/linker cannot link "
                "address+undefined sanitizers")
        endif()
    elseif(MSVC)
        set(SALTCREEP_SANITIZER_FLAGS /fsanitize=address)
    else()
        message(WARNING "ENABLE_SANITIZERS requested, but no sanitizer flags are configured for ${CMAKE_CXX_COMPILER_ID}")
    endif()
endif()

function(configure_saltcreep_target target_name)
    if(ENABLE_WERROR)
        if(MSVC)
            target_compile_options(${target_name} PRIVATE /WX)
        else()
            target_compile_options(${target_name} PRIVATE -Werror)
            if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
                target_compile_options(${target_name} PRIVATE -Wno-error=stringop-overflow)
            endif()
        endif()
    endif()

    if(SALTCREEP_SANITIZER_FLAGS)
        target_compile_options(${target_name} PRIVATE ${SALTCREEP_SANITIZER_FLAGS})
    endif()
    if(SALTCREEP_SANITIZER_LINK_FLAGS)
        target_link_options(${target_name} PRIVATE ${SALTCREEP_SANITIZER_LINK_FLAGS})
    endif()
endfunction()

# ── Source files shared by main executable and tests ─────────────────────────
file(GLOB_RECURSE SALT_SOURCES CONFIGURE_DEPENDS src/*.cpp)

# ── Main executable ───────────────────────────────────────────────────────────
add_executable(saltcreep main/main.cpp ${SALT_SOURCES})
target_include_directories(saltcreep PRIVATE include)
if(LSS_SALTCREEP_FORCE_LSS_EIGEN)
    # Prepend the proxy dir (contains ONLY Eigen/) BEFORE the vendored copy.
    # Using the full lot-salt-suite include/ would shadow saltcreep's own
    # relative includes (e.g. "io/CaseParser.hpp"). The proxy avoids this.
    target_include_directories(saltcreep BEFORE PRIVATE "${LSS_EIGEN_PROXY_DIR}")
endif()
target_compile_definitions(saltcreep PRIVATE
    LSS_SALTCREEP_EIGEN_MODE="${LSS_SALTCREEP_EIGEN_MODE_VALUE}")
target_link_libraries(saltcreep PRIVATE yaml-cpp::yaml-cpp)
configure_saltcreep_target(saltcreep)
if(OpenMP_CXX_FOUND)
    target_link_libraries(saltcreep PRIVATE OpenMP::OpenMP_CXX)
endif()

# ── Unit tests ────────────────────────────────────────────────────────────────
enable_testing()
include(CTest)

add_executable(tests_unit
    tests/cpp/test_lame.cpp
    tests/cpp/test_patch_l3.cpp
    tests/cpp/test_dm.cpp
    tests/cpp/test_tcc_regression.cpp
    tests/cpp/test_edmt.cpp
    tests/cpp/test_isv_sh_dm.cpp
    tests/cpp/test_patch_q4.cpp
    tests/cpp/test_lame_q4.cpp
    tests/cpp/test_tcc_q4.cpp
    tests/cpp/test_patch_t3.cpp
    tests/cpp/test_lame_t3.cpp
    tests/cpp/test_tcc_t3.cpp
    tests/cpp/test_patch_q8.cpp
    tests/cpp/test_lame_q8.cpp
    tests/cpp/test_tcc_q8.cpp
    tests/cpp/test_patch_q9.cpp
    tests/cpp/test_lame_q9.cpp
    tests/cpp/test_tcc_q9.cpp
    tests/cpp/test_patch_aq9.cpp
    tests/cpp/test_lame_aq9.cpp
    tests/cpp/test_tcc_aq9.cpp
    tests/cpp/test_patch_t6.cpp
    tests/cpp/test_lame_t6.cpp
    tests/cpp/test_tcc_t6.cpp
    tests/cpp/test_implicit_adaptive.cpp
    tests/cpp/test_motta_v1.cpp
    tests/cpp/test_dilatancy_envelope.cpp
    tests/cpp/test_wang_2004.cpp
    tests/cpp/test_aubertin_isv_sh_d.cpp
    tests/cpp/test_profile_field.cpp
    tests/cpp/test_conduction_1d.cpp
    tests/cpp/test_conduction_2d.cpp
    tests/cpp/test_thermal_force.cpp
    tests/cpp/test_openmp_consistency.cpp
    tests/cpp/test_damage_diagnostics.cpp
    tests/cpp/test_mesh_adaptation.cpp
    tests/cpp/test_wall_pressure_field.cpp
    tests/cpp/test_stress_diagnostics.cpp
    tests/cpp/test_csv_time_depth_fields.cpp
    tests/cpp/test_edge_cases.cpp
    tests/test_eigen_source.cpp
    ${SALT_SOURCES})
target_include_directories(tests_unit PRIVATE include)
if(LSS_SALTCREEP_FORCE_LSS_EIGEN)
    target_include_directories(tests_unit BEFORE PRIVATE "${LSS_EIGEN_PROXY_DIR}")
endif()
target_compile_definitions(tests_unit PRIVATE
    LSS_SALTCREEP_EIGEN_MODE="${LSS_SALTCREEP_EIGEN_MODE_VALUE}")
target_link_libraries(tests_unit PRIVATE
    Catch2::Catch2WithMain
    yaml-cpp::yaml-cpp)
configure_saltcreep_target(tests_unit)
if(OpenMP_CXX_FOUND)
    target_link_libraries(tests_unit PRIVATE OpenMP::OpenMP_CXX)
endif()

include(${Catch2_SOURCE_DIR}/extras/Catch.cmake)
catch_discover_tests(tests_unit)
