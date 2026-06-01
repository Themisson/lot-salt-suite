cmake_minimum_required(VERSION 3.20)
project(saltcreep CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(ENABLE_SANITIZERS "Build saltcreep targets with available sanitizer flags" OFF)
option(ENABLE_WERROR "Treat compiler warnings as errors for saltcreep targets" OFF)

# MSVC vs GCC/Clang warning flags
if(MSVC)
    add_compile_options(/W4 /wd4100)  # /wd4100: unused parameter (common in virtual stubs)
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
    tests/cpp/test_edge_cases.cpp
    ${SALT_SOURCES})
target_include_directories(tests_unit PRIVATE include)
target_link_libraries(tests_unit PRIVATE
    Catch2::Catch2WithMain
    yaml-cpp::yaml-cpp)
configure_saltcreep_target(tests_unit)
if(OpenMP_CXX_FOUND)
    target_link_libraries(tests_unit PRIVATE OpenMP::OpenMP_CXX)
endif()

include(${Catch2_SOURCE_DIR}/extras/Catch.cmake)
catch_discover_tests(tests_unit)
