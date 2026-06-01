#include <catch2/catch_test_macros.hpp>
#include <cmath>
#include <map>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_q4.hpp"
#include "solver/Assembler.hpp"
#include "q4_test_helpers.hpp"

TEST_CASE("AxisymQ4: linear displacement patch is recovered from consistent nodal forces",
          "[patch][q4]") {
    AxisymQ4 elem;
    ElasticIsotropic model(25.0e9, 0.30);
    Mesh2D mesh = build_q4_mesh(1.0, 2.0, 1.0, 1, 1);

    auto K = Assembler::assemble_K(mesh, elem, model);
    Eigen::VectorXd u_expected(mesh.total_dofs());
    for (int n = 0; n < mesh.n_nodes; ++n) {
        const double r = mesh.nodes[n].r;
        const double z = mesh.nodes[n].z;
        u_expected[mesh.dof_index(n, 0)] = 1.0 + 0.1 * r + 0.05 * z;
        u_expected[mesh.dof_index(n, 1)] = -0.05 * r + 0.2 * z;
    }

    Eigen::VectorXd f = K * u_expected;
    std::map<int, double> bc;
    bc[mesh.dof_index(0, 0)] = u_expected[mesh.dof_index(0, 0)];
    bc[mesh.dof_index(0, 1)] = u_expected[mesh.dof_index(0, 1)];
    bc[mesh.dof_index(1, 1)] = u_expected[mesh.dof_index(1, 1)];

    Eigen::VectorXd u = solve_with_dirichlet(K, f, bc);
    const double rel_err = (u - u_expected).norm() / u_expected.norm();
    REQUIRE(rel_err < 1.0e-14);
}

TEST_CASE("AxisymQ4: B matrix reproduces linear field gradients at Gauss points",
          "[patch][q4]") {
    AxisymQ4 elem;
    Mesh2D mesh = build_q4_mesh(1.0, 2.0, 1.0, 1, 1);
    Eigen::VectorXd ue(8);
    for (int i = 0; i < 4; ++i) {
        const Node& node = mesh.nodes[mesh.elem_nodes[i]];
        ue[2 * i] = 1.0 + 0.1 * node.r + 0.05 * node.z;
        ue[2 * i + 1] = -0.05 * node.r + 0.2 * node.z;
    }

    auto coords = element_coords(mesh, 0, elem.n_nodes());
    for (const auto& gp : elem.gauss_points()) {
        double N[4];
        elem.shape_functions(gp, N);
        double r_gp = 0.0;
        for (int i = 0; i < 4; ++i)
            r_gp += N[i] * coords[i].r;

        Eigen::Vector4d strain = elem.B_matrix(gp, coords) * ue;
        const double u_r_gp = 1.0 + 0.1 * r_gp + 0.05 *
            (N[0] * coords[0].z + N[1] * coords[1].z + N[2] * coords[2].z + N[3] * coords[3].z);

        REQUIRE(std::abs(strain[0] - 0.1) < 1.0e-14);
        REQUIRE(std::abs(strain[1] - u_r_gp / r_gp) < 1.0e-14);
        REQUIRE(std::abs(strain[2] - 0.2) < 1.0e-14);
        REQUIRE(std::abs(strain[3]) < 1.0e-14);
    }
}
