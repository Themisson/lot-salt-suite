#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "solver/Assembler.hpp"
#include "solver/TimeIntegrator.hpp"
#include "thermal/conduction_1d_field.hpp"
#include "thermal/profile_field.hpp"

namespace {

std::vector<Stress> zero_geostatic(const Mesh& mesh, const Element& element) {
    return std::vector<Stress>(
        mesh.n_elements * static_cast<int>(element.gauss_points().size()),
        Stress::Zero());
}

TimeIntegrator make_integrator(const Mesh1D& mesh,
                               const AxisymL3& element,
                               const ElasticIsotropic& model,
                               const ThermalField& thermal,
                               std::vector<int> fixed_dofs = {}) {
    auto K = Assembler::assemble_K(mesh, element, model);
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    return TimeIntegrator(mesh, element, model, thermal, std::move(K), std::move(f),
                          zero_geostatic(mesh, element), std::move(fixed_dofs));
}

} // namespace

TEST_CASE("Thermal pseudo-force: alpha zero preserves mechanical response",
          "[thermal][force]") {
    AxisymL3 element;
    ElasticIsotropic model(25.0e9, 0.30);
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 4, 1.0);
    ProfileField hot_no_expansion =
        ProfileField::make_constant(500.0, 0.0, 300.0);

    auto integrator = make_integrator(mesh, element, model, hot_no_expansion);
    integrator.advance(1.0);

    REQUIRE(integrator.state().u_total.norm() == Catch::Approx(0.0).margin(1.0e-18));
    for (const auto& eps_th : integrator.state().eps_th_gp)
        REQUIRE(eps_th.norm() == Catch::Approx(0.0).margin(1.0e-18));
}

TEST_CASE("Thermal pseudo-force: free uniform heating matches plane-strain expansion",
          "[thermal][force]") {
    constexpr double E = 25.0e9;
    constexpr double nu = 0.30;
    constexpr double alpha = 1.0e-5;
    constexpr double delta_T = 40.0;

    AxisymL3 element;
    ElasticIsotropic model(E, nu);
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 8, 1.0);
    ProfileField field =
        ProfileField::make_constant(300.0 + delta_T, alpha, 300.0);

    auto integrator = make_integrator(mesh, element, model, field);
    integrator.advance(1.0);

    const double coeff = (1.0 + nu) * alpha * delta_T;
    for (int i = 0; i < mesh.n_nodes; ++i) {
        const double expected = coeff * mesh.nodes[i].r;
        REQUIRE(integrator.state().u_total[i] == Catch::Approx(expected).epsilon(2.0e-10));
    }

    double max_radial_stress = 0.0;
    for (const auto& sigma : integrator.state().sigma_gp) {
        max_radial_stress = std::max(max_radial_stress, std::abs(sigma[0]));
        max_radial_stress = std::max(max_radial_stress, std::abs(sigma[1]));
    }
    REQUIRE(max_radial_stress < 1.0e-3);
}

TEST_CASE("Thermal pseudo-force: heated radial wall closes a fixed outer boundary",
          "[thermal][force][conduction_1d]") {
    AxisymL3 element;
    ElasticIsotropic model(25.0e9, 0.30);
    Mesh1D mesh = build_mesh_L3(1.0, 3.0, 12, 1.0);

    Conduction1DOptions options;
    options.k_W_m_K = 5.0;
    options.rho_kg_m3 = 2000.0;
    options.cp_J_kg_K = 100.0;
    options.initial_T_K = 300.0;
    options.inner_wall_T_K = 360.0;
    options.outer_T_K = 300.0;
    options.dt_thermal_s = 0.05;
    options.beta = 0.5;
    options.alpha_thermal = 2.0e-5;
    options.T_reference_K = 300.0;
    options.outer_bc = "prescribed";
    Conduction1DField thermal(mesh, options);

    auto integrator = make_integrator(
        mesh, element, model, thermal, {mesh.dof_index(mesh.n_nodes - 1, 0)});
    integrator.advance(0.5);

    REQUIRE(integrator.wall_displacement_m() < 0.0);
    REQUIRE(integrator.wall_closure_pct() > 0.0);
}
