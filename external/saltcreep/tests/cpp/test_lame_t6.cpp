#include <catch2/catch_test_macros.hpp>
#include <algorithm>
#include <cmath>
#include <map>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_t6.hpp"
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
}

TEST_CASE("Lame T6: radial displacement converges at quadratic-element rate",
          "[lame][t6][convergence]") {
    constexpr double Ri = 1.0;
    constexpr double Re = 3.0;
    constexpr double height = 1.0;
    constexpr double E = 25.0e9;
    constexpr double nu = 0.30;
    constexpr double p_inner = 1.0e6;

    AxisymT6 elem;
    ElasticIsotropic model(E, nu);
    const int meshes[] = {3, 6, 12, 24};
    std::vector<double> errors;

    for (int n_radial : meshes) {
        const int n_axial = std::max(2, n_radial / 2);
        Mesh2D mesh = build_t6_mesh(Ri, Re, height, n_radial, n_axial);
        auto K = Assembler::assemble_K(mesh, elem, model);
        auto f = assemble_inner_pressure_t6(mesh, elem, n_radial, n_axial, p_inner);

        auto bc = all_axial_fixed(mesh);
        const int nz_fine = 2 * n_axial;
        for (int n = 0; n < mesh.n_nodes; ++n) {
            if (std::abs(mesh.nodes[n].r - Re) < 1.0e-12)
                bc[mesh.dof_index(n, 0)] = lame_ur(Re, Ri, Re, p_inner, 0.0, E, nu);
        }

        Eigen::VectorXd u = solve_with_dirichlet(K, f, bc);
        double avg_inner = 0.0;
        int count_inner = 0;
        for (int n = 0; n < mesh.n_nodes; ++n) {
            if (std::abs(mesh.nodes[n].r - Ri) < 1.0e-12) {
                avg_inner += u[mesh.dof_index(n, 0)];
                ++count_inner;
            }
        }
        REQUIRE(count_inner == nz_fine + 1);
        avg_inner /= static_cast<double>(count_inner);

        const double exact = lame_ur(Ri, Ri, Re, p_inner, 0.0, E, nu);
        errors.push_back(std::abs(avg_inner - exact) / std::abs(exact));
    }

    std::vector<double> rates;
    for (size_t i = 0; i + 1 < errors.size(); ++i)
        rates.push_back(std::log(errors[i] / errors[i + 1]) / std::log(2.0));

    const double min_rate = *std::min_element(rates.begin(), rates.end());
    REQUIRE(min_rate >= 2.5);
}
