#include <catch2/catch_test_macros.hpp>
#include <algorithm>
#include <cmath>
#include <map>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_q4.hpp"
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

TEST_CASE("Lame Q4: radial displacement converges at linear-element rate",
          "[lame][q4][convergence]") {
    constexpr double Ri = 1.0;
    constexpr double Re = 3.0;
    constexpr double height = 1.0;
    constexpr double E = 25.0e9;
    constexpr double nu = 0.30;
    constexpr double p_inner = 1.0e6;

    AxisymQ4 elem;
    ElasticIsotropic model(E, nu);
    const int meshes[] = {5, 10, 20, 40};
    std::vector<double> errors;

    for (int n_radial : meshes) {
        const int n_axial = std::max(2, n_radial / 2);
        Mesh2D mesh = build_q4_mesh(Ri, Re, height, n_radial, n_axial);
        auto K = Assembler::assemble_K(mesh, elem, model);
        auto f = assemble_inner_pressure_q4(mesh, elem, n_radial, n_axial, p_inner);

        auto bc = all_axial_fixed(mesh);
        for (int iz = 0; iz <= n_axial; ++iz) {
            const int outer_node = iz * (n_radial + 1) + n_radial;
            bc[mesh.dof_index(outer_node, 0)] = lame_ur(Re, Ri, Re, p_inner, 0.0, E, nu);
        }

        Eigen::VectorXd u = solve_with_dirichlet(K, f, bc);
        double avg_inner = 0.0;
        for (int iz = 0; iz <= n_axial; ++iz) {
            const int inner_node = iz * (n_radial + 1);
            avg_inner += u[mesh.dof_index(inner_node, 0)];
        }
        avg_inner /= static_cast<double>(n_axial + 1);

        const double exact = lame_ur(Ri, Ri, Re, p_inner, 0.0, E, nu);
        errors.push_back(std::abs(avg_inner - exact) / std::abs(exact));
    }

    std::vector<double> rates;
    for (size_t i = 0; i + 1 < errors.size(); ++i)
        rates.push_back(std::log(errors[i] / errors[i + 1]) / std::log(2.0));

    const double min_rate = *std::min_element(rates.begin(), rates.end());
    REQUIRE(min_rate >= 1.8);
}
