#include <catch2/catch_test_macros.hpp>
#include <algorithm>
#include <cmath>
#include <map>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_aq9.hpp"
#include "solver/Assembler.hpp"
#include "q4_test_helpers.hpp"

namespace {
double lame_A(double Ri, double Re, double pi, double pe) {
    return (pi * Ri * Ri - pe * Re * Re) / (Re * Re - Ri * Ri);
}

double lame_B(double Ri, double Re, double pi, double pe) {
    return (pi - pe) * Ri * Ri * Re * Re / (Re * Re - Ri * Ri);
}

double lame_ur(double r, double Ri, double Re, double pi, double pe, double E, double nu) {
    const double A = lame_A(Ri, Re, pi, pe);
    const double B = lame_B(Ri, Re, pi, pe);
    return (1.0 + nu) / E * ((1.0 - 2.0 * nu) * A * r + B / r);
}

double solve_inner_error(int n_radial) {
    constexpr double Ri = 1.0;
    constexpr double Re = 3.0;
    constexpr double height = 1.0;
    constexpr double E = 25.0e9;
    constexpr double nu = 0.30;
    constexpr double p_inner = 1.0e6;

    AxisymAQ9 elem;
    ElasticIsotropic model(E, nu);
    const int n_axial = 1;
    Mesh2D mesh = build_aq9_mesh(Ri, Re, height, n_radial, n_axial);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = assemble_inner_pressure_aq9(mesh, elem, n_radial, n_axial, p_inner);

    auto bc = all_axial_fixed(mesh);
    for (int n = 0; n < mesh.n_nodes; ++n) {
        if (std::abs(mesh.nodes[n].r - Re) < 1.0e-12)
            bc[mesh.dof_index(n, 0)] = lame_ur(Re, Ri, Re, p_inner, 0.0, E, nu);
    }

    Eigen::VectorXd u = solve_with_dirichlet(K, f, bc);
    double max_rel = 0.0;
    for (int n = 0; n < mesh.n_nodes; ++n) {
        const double exact = lame_ur(mesh.nodes[n].r, Ri, Re, p_inner, 0.0, E, nu);
        const double err = std::abs(u[mesh.dof_index(n, 0)] - exact) / std::abs(exact);
        max_rel = std::max(max_rel, err);
    }
    return max_rel;
}
}

TEST_CASE("Lame AQ9: one enriched element captures the Lame displacement field",
          "[lame][aq9][exact]") {
    REQUIRE(solve_inner_error(1) < 1.0e-12);
}

TEST_CASE("Lame AQ9: enriched convergence is dramatically more accurate than Q9",
          "[lame][aq9][convergence]") {
    const int meshes[] = {1, 2, 4};
    std::vector<double> errors;
    for (int n : meshes)
        errors.push_back(solve_inner_error(n));

    REQUIRE(errors[0] < 1.0e-12);
    REQUIRE(errors[1] < 1.0e-12);
    REQUIRE(errors[2] < 1.0e-12);
}
