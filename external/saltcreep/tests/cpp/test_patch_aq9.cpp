#include <catch2/catch_test_macros.hpp>
#include <cmath>
#include <map>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_aq9.hpp"
#include "solver/Assembler.hpp"
#include "q4_test_helpers.hpp"

namespace {
double ur_linear(double r, double z) {
    return 1.0 + 0.1 * r + 0.05 * z;
}

double uz_linear(double r, double z) {
    return -0.05 * r + 0.2 * z;
}

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
}

TEST_CASE("AxisymAQ9: linear displacement patch is recovered from consistent nodal forces",
          "[patch][aq9]") {
    AxisymAQ9 elem;
    ElasticIsotropic model(25.0e9, 0.30);
    Mesh2D mesh = build_aq9_mesh(1.0, 2.0, 1.0, 1, 1);

    auto K = Assembler::assemble_K(mesh, elem, model);
    Eigen::VectorXd u_expected(mesh.total_dofs());
    for (int n = 0; n < mesh.n_nodes; ++n) {
        const double r = mesh.nodes[n].r;
        const double z = mesh.nodes[n].z;
        u_expected[mesh.dof_index(n, 0)] = ur_linear(r, z);
        u_expected[mesh.dof_index(n, 1)] = uz_linear(r, z);
    }

    Eigen::VectorXd f = K * u_expected;
    std::map<int, double> bc;
    bc[mesh.dof_index(0, 0)] = u_expected[mesh.dof_index(0, 0)];
    bc[mesh.dof_index(0, 1)] = u_expected[mesh.dof_index(0, 1)];
    bc[mesh.dof_index(1, 1)] = u_expected[mesh.dof_index(1, 1)];

    Eigen::VectorXd u = solve_with_dirichlet(K, f, bc);
    REQUIRE((u - u_expected).norm() / u_expected.norm() < 1.0e-13);
}

TEST_CASE("AxisymAQ9: B matrix reproduces the Lame radial basis exactly",
          "[patch][aq9][lame]") {
    constexpr double Ri = 1.0;
    constexpr double Re = 3.0;
    constexpr double E = 25.0e9;
    constexpr double nu = 0.30;
    constexpr double p_inner = 1.0e6;

    AxisymAQ9 elem;
    Mesh2D mesh = build_aq9_mesh(Ri, Re, 1.0, 1, 1);
    auto coords = element_coords(mesh, 0, elem.n_nodes());

    Eigen::VectorXd ue(18);
    for (int i = 0; i < elem.n_nodes(); ++i) {
        ue[2 * i] = lame_ur(coords[i].r, Ri, Re, p_inner, 0.0, E, nu);
        ue[2 * i + 1] = 0.0;
    }

    const double A = lame_A(Ri, Re, p_inner, 0.0);
    const double B = lame_B(Ri, Re, p_inner, 0.0);
    const double c_r = (1.0 + nu) / E * (1.0 - 2.0 * nu) * A;
    const double c_inv = (1.0 + nu) / E * B;

    for (const auto& gp : elem.gauss_points()) {
        double N[9];
        elem.shape_functions(gp, coords, N);
        double r_gp = 0.0;
        for (int i = 0; i < elem.n_nodes(); ++i)
            r_gp += N[i] * coords[i].r;

        Eigen::Vector4d strain = elem.B_matrix(gp, coords) * ue;
        REQUIRE(std::abs(strain[0] - (c_r - c_inv / (r_gp * r_gp))) < 1.0e-14);
        REQUIRE(std::abs(strain[1] - (c_r + c_inv / (r_gp * r_gp))) < 1.0e-14);
        REQUIRE(std::abs(strain[2]) < 1.0e-14);
        REQUIRE(std::abs(strain[3]) < 1.0e-14);
        REQUIRE(elem.jacobian_weight(gp, coords) > 0.0);
    }
}
