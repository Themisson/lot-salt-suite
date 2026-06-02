// Diagnostic test — Fase 6.10B
// Reports which Eigen source was resolved at compile time.
// Always passes; used as objective proof of include order.
#include <catch2/catch_test_macros.hpp>
#include <Eigen/Core>
#include <iostream>
#include <string>

#ifndef LSS_SALTCREEP_EIGEN_MODE
#define LSS_SALTCREEP_EIGEN_MODE "unknown"
#endif

TEST_CASE("Eigen source mode diagnostic", "[eigen_source][diagnostic]") {
    const std::string mode = LSS_SALTCREEP_EIGEN_MODE;
    std::cout << "\n[eigen_source] LSS_SALTCREEP_EIGEN_MODE = " << mode << "\n";
    std::cout << "[eigen_source] EIGEN_VERSION_STRING      = " << EIGEN_VERSION_STRING << "\n";
    // Verify mode is one of the two known values set by CMake.
    REQUIRE((mode == "lss" || mode == "internal"));
}
