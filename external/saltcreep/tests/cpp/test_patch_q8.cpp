#include <catch2/catch_test_macros.hpp>
#include <cmath>
#include <map>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_q8.hpp"
#include "solver/Assembler.hpp"
#include "q4_test_helpers.hpp"

namespace {
double ur_linear(double r, double z) {
    return 1.0 + 0.1 * r + 0.05 * z;
}

double uz_linear(double r, double z) {
    return -0.05 * r + 0.2 * z;
}

double ur_quad(double r, double z) {
    return 1.0 + 0.1 * r + 0.05 * z + 0.02 * r * r + 0.03 * r * z + 0.01 * z * z;
}

double uz_quad(double r, double z) {
    return -0.05 * r + 0.2 * z + 0.015 * r * r - 0.02 * r * z + 0.025 * z * z;
}
}

TEST_CASE("AxisymQ8: linear displacement patch is recovered from consistent nodal forces",
          "[patch][q8]") {
    AxisymQ8 elem;
    ElasticIsotropic model(25.0e9, 0.30);
    Mesh2D mesh = build_q8_mesh(1.0, 2.0, 1.0, 1, 1);

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

TEST_CASE("AxisymQ8: B matrix reproduces quadratic field gradients at Gauss points",
          "[patch][q8]") {
    AxisymQ8 elem;
    Mesh2D mesh = build_q8_mesh(1.0, 2.0, 1.0, 1, 1);
    auto coords = element_coords(mesh, 0, elem.n_nodes());

    Eigen::VectorXd ue(16);
    for (int i = 0; i < elem.n_nodes(); ++i) {
        ue[2 * i] = ur_quad(coords[i].r, coords[i].z);
        ue[2 * i + 1] = uz_quad(coords[i].r, coords[i].z);
    }

    for (const auto& gp : elem.gauss_points()) {
        double N[8];
        elem.shape_functions(gp, N);
        double r_gp = 0.0;
        double z_gp = 0.0;
        for (int i = 0; i < elem.n_nodes(); ++i) {
            r_gp += N[i] * coords[i].r;
            z_gp += N[i] * coords[i].z;
        }

        Eigen::Vector4d strain = elem.B_matrix(gp, coords) * ue;
        const double exact_ur = ur_quad(r_gp, z_gp);
        const double exact_err = 0.1 + 0.04 * r_gp + 0.03 * z_gp;
        const double exact_ezz = 0.2 - 0.02 * r_gp + 0.05 * z_gp;
        const double exact_grz = 0.06 * r_gp;

        REQUIRE(std::abs(strain[0] - exact_err) < 1.0e-13);
        REQUIRE(std::abs(strain[1] - exact_ur / r_gp) < 1.0e-13);
        REQUIRE(std::abs(strain[2] - exact_ezz) < 1.0e-13);
        REQUIRE(std::abs(strain[3] - exact_grz) < 1.0e-13);
    }
}
