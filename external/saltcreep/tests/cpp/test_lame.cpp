#include <catch2/catch_test_macros.hpp>
#include <cmath>
#include <vector>
#include <algorithm>

#include "elements/axisym_1d_L3.hpp"
#include "constitutive/elastic_isotropic.hpp"
#include "solver/Assembler.hpp"
#include "solver/ElasticSolver.hpp"

// ---------------------------------------------------------------------------
// Lame analytical solution (tension-positive, plane-strain axisymmetric).
// Both boundaries are Neumann: sigma_rr(Ri)=-pi, sigma_rr(Re)=-pe.
// ---------------------------------------------------------------------------
static double lame_A(double Ri, double Re, double pi, double pe) {
    return (pi * Ri*Ri - pe * Re*Re) / (Re*Re - Ri*Ri);
}
static double lame_B(double Ri, double Re, double pi, double pe) {
    return (pi - pe) * Ri*Ri * Re*Re / (Re*Re - Ri*Ri);
}
static double lame_ur(double r, double Ri, double Re,
                       double pi, double pe, double E, double nu) {
    double A = lame_A(Ri, Re, pi, pe);
    double B = lame_B(Ri, Re, pi, pe);
    return (1.0 + nu) / E * ((1.0 - 2.0*nu) * A * r + B / r);
}
static double lame_srr(double r, double Ri, double Re, double pi, double pe) {
    double A = lame_A(Ri, Re, pi, pe);
    double B = lame_B(Ri, Re, pi, pe);
    return A - B / (r*r);
}

// ---------------------------------------------------------------------------
// Run FEM with purely Neumann BCs.
// The 1D axisymmetric K is positive-definite (N/r term): no Dirichlet needed.
// ---------------------------------------------------------------------------
static Eigen::VectorXd run_lame(double Ri, double Re, int n,
                                 double ratio, double E, double nu,
                                 double p_inner, double p_outer) {
    AxisymL3         elem;
    ElasticIsotropic model(E, nu);
    Mesh1D mesh = build_mesh_L3(Ri, Re, n, ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, p_inner, p_outer);
    return ElasticSolver{}.solve(std::move(K), std::move(f), {}).u;
}

// ---------------------------------------------------------------------------
// Geometry for ACCURACY tests: Re/Ri = 10.
//   n=100 with ratio=1000: h0 ~ 0.09 mm, h_last ~ 94 mm -> rel_err ~ 3e-7.
//   (n=30 gives ~8e-6 because large outer elements h_last=297mm dominate error;
//    the convergence test below verifies the rate is ~h^3, confirming correctness.)
//
// Geometry for CONVERGENCE test: Re/Ri = 100 (larger domain, visible rate variation).
// ---------------------------------------------------------------------------
static constexpr double kRi  = 0.1556;          // m
static constexpr double kReA = 10.0 * 0.1556;   // m  (accuracy tests)
static constexpr double kReC = 100.0 * 0.1556;  // m  (convergence test)
static constexpr double kE   = 25.0e9;           // Pa
static constexpr double kNu  = 0.30;
static constexpr double kP   = 10.0e6;           // Pa
static constexpr int    kNA  = 100;              // elements for accuracy tests

// ---------------------------------------------------------------------------
TEST_CASE("Lame: inner pressure only", "[lame]") {
    auto u = run_lame(kRi, kReA, kNA, 1000.0, kE, kNu, kP, 0.0);
    double u_exact = lame_ur(kRi, kRi, kReA, kP, 0.0, kE, kNu);
    double rel_err = std::abs(u[0] - u_exact) / std::abs(u_exact);
    REQUIRE(rel_err < 1.0e-6);
}

TEST_CASE("Lame: outer pressure only", "[lame]") {
    auto u = run_lame(kRi, kReA, kNA, 1000.0, kE, kNu, 0.0, kP);
    double u_exact = lame_ur(kRi, kRi, kReA, 0.0, kP, kE, kNu);
    double rel_err = std::abs(u[0] - u_exact) / std::abs(u_exact);
    REQUIRE(rel_err < 1.0e-6);
}

TEST_CASE("Lame: both pressures", "[lame]") {
    const double pi = kP, pe = 0.5 * kP;
    auto u = run_lame(kRi, kReA, kNA, 1000.0, kE, kNu, pi, pe);
    double u_exact = lame_ur(kRi, kRi, kReA, pi, pe, kE, kNu);
    double rel_err = std::abs(u[0] - u_exact) / std::abs(u_exact);
    REQUIRE(rel_err < 1.0e-6);
}

TEST_CASE("Lame: sigma_rr at first Gauss point matches analytical", "[lame]") {
    AxisymL3         elem;
    ElasticIsotropic model(kE, kNu);
    Mesh1D mesh = build_mesh_L3(kRi, kReA, kNA, 1000.0);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, kP, 0.0);
    auto u = ElasticSolver{}.solve(std::move(K), std::move(f), {}).u;

    // First GP of element 0 (xi = -sqrt(3/5), closest to inner wall)
    auto gps = elem.gauss_points();
    double xi = gps[0].xi;
    std::vector<double> coords = {mesh.node_r[0], mesh.node_r[1], mesh.node_r[2]};
    Eigen::MatrixXd B  = elem.B_matrix(xi, coords);
    Eigen::Vector3d ue(u[0], u[1], u[2]);
    Eigen::Vector4d sigma = model.D_elastic() * B * ue;

    double N[3]; elem.shape_functions(xi, N);
    double r_gp = N[0]*coords[0] + N[1]*coords[1] + N[2]*coords[2];
    double srr_exact = lame_srr(r_gp, kRi, kReA, kP, 0.0);
    double rel_err = std::abs(sigma[0] - srr_exact) / std::abs(srr_exact);
    REQUIRE(rel_err < 1.0e-4);
}

TEST_CASE("Lame: convergence rate h3 for L3 quadratic element", "[lame][convergence]") {
    // Uses larger domain (Re/Ri=100) to expose convergence over multiple doublings.
    const int meshes[] = {5, 10, 20, 40};
    std::vector<double> errors;
    for (int n : meshes) {
        auto u = run_lame(kRi, kReC, n, 1000.0, kE, kNu, kP, 0.0);
        double u_exact = lame_ur(kRi, kRi, kReC, kP, 0.0, kE, kNu);
        errors.push_back(std::abs(u[0] - u_exact) / std::abs(u_exact));
    }
    std::vector<double> rates;
    for (size_t i = 0; i + 1 < errors.size(); ++i) {
        if (errors[i+1] < 1e-15) break;
        rates.push_back(std::log(errors[i] / errors[i+1]) / std::log(2.0));
    }
    double min_rate = *std::min_element(rates.begin(), rates.end());
    REQUIRE(min_rate > 2.8);
}
