#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <vector>

#include "solver/Assembler.hpp"
#include "thermal/conduction_1d_field.hpp"
#include "io/CaseParser.hpp"

namespace {
namespace fs = std::filesystem;

fs::path find_data_dir() {
    for (const auto& candidate : {
             fs::path("data"),
             fs::path("../data"),
             fs::path("../../data")}) {
        if (fs::exists(candidate / "litologias"))
            return candidate;
    }
    throw std::runtime_error("Cannot find data/litologias");
}

double log_profile(double r, double Ri, double Re, double Ti, double Te) {
    return Ti + (Te - Ti) * std::log(r / Ri) / std::log(Re / Ri);
}

Conduction1DField make_field(double dt_s, double t_initial_offset = 0.0) {
    const double Ri = 1.0;
    const double Re = 2.0;
    Mesh1D mesh = build_mesh_L3(Ri, Re, 16, 1.0);

    std::vector<double> initial(mesh.n_nodes);
    for (int i = 0; i < mesh.n_nodes; ++i) {
        const double r = mesh.nodes[i].r;
        const double s = std::log(r / Ri) / std::log(Re / Ri);
        initial[i] = 300.0 + 20.0 * std::sin(3.14159265358979323846 * s)
                     + t_initial_offset;
    }

    Conduction1DOptions options;
    options.k_W_m_K = 1.0;
    options.rho_kg_m3 = 10.0;
    options.cp_J_kg_K = 1.0;
    options.initial_T_K = 300.0;
    options.inner_wall_T_K = 300.0;
    options.outer_T_K = 300.0;
    options.dt_thermal_s = dt_s;
    options.beta = 0.5;
    options.outer_bc = "prescribed";
    options.initial_nodal_T_K = initial;
    return Conduction1DField(mesh, options);
}

} // namespace

TEST_CASE("Conduction1DField: prescribed outer BC converges to logarithmic steady state",
          "[thermal][conduction_1d]") {
    const double Ri = 1.0;
    const double Re = 3.0;
    const double Ti = 400.0;
    const double Te = 300.0;
    Mesh1D mesh = build_mesh_L3(Ri, Re, 32, 1.0);

    Conduction1DOptions options;
    options.k_W_m_K = 1000.0;
    options.rho_kg_m3 = 1000.0;
    options.cp_J_kg_K = 1.0;
    options.initial_T_K = Te;
    options.inner_wall_T_K = Ti;
    options.outer_T_K = Te;
    options.dt_thermal_s = 0.25;
    options.beta = 0.5;
    options.outer_bc = "prescribed";

    Conduction1DField field(mesh, options);
    field.advance_to(2000.0);

    double max_error = 0.0;
    for (const Node& node : mesh.nodes) {
        const double numerical = field.temperature_at(Eigen::Vector2d(node.r, 0.0), 2000.0);
        const double exact = log_profile(node.r, Ri, Re, Ti, Te);
        max_error = std::max(max_error, std::abs(numerical - exact));
    }
    REQUIRE(max_error < 0.15);
}

TEST_CASE("Conduction1DField: Crank-Nicolson temporal error decreases at second order",
          "[thermal][conduction_1d]") {
    constexpr double t_end = 0.25;
    constexpr double r_probe = 1.45;

    auto coarse = make_field(0.05);
    auto medium = make_field(0.025);
    auto fine = make_field(0.0125);
    auto reference = make_field(0.003125);

    const Eigen::Vector2d x(r_probe, 0.0);
    const double T_ref = reference.temperature_at(x, t_end);
    const double e1 = std::abs(coarse.temperature_at(x, t_end) - T_ref);
    const double e2 = std::abs(medium.temperature_at(x, t_end) - T_ref);
    const double e3 = std::abs(fine.temperature_at(x, t_end) - T_ref);

    REQUIRE(e1 / e2 > 2.5);
    REQUIRE(e2 / e3 > 2.5);
}

TEST_CASE("Conduction1DField: discrete energy balance matches boundary heat input",
          "[thermal][conduction_1d]") {
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 12, 1.0);

    Conduction1DOptions options;
    options.k_W_m_K = 3.0;
    options.rho_kg_m3 = 20.0;
    options.cp_J_kg_K = 2.0;
    options.initial_T_K = 300.0;
    options.inner_wall_T_K = 360.0;
    options.dt_thermal_s = 0.1;
    options.beta = 0.5;
    options.outer_bc = "flux_zero";

    Conduction1DField field(mesh, options);
    const double E0 = field.total_energy_J();
    field.advance_to(0.1);
    const double E1 = field.total_energy_J();

    const double dE = E1 - E0;
    const double q_boundary = field.last_boundary_heat_J();
    const double scale = std::max({std::abs(dE), std::abs(q_boundary), 1.0});
    REQUIRE(std::abs(dE - q_boundary) / scale < 1.0e-10);
}

TEST_CASE("CaseParser: conduction_1d accepts prescribed and flux_zero outer BCs",
          "[thermal][parser]") {
    const fs::path path = fs::temp_directory_path() / "saltcreep_conduction_1d_case.yaml";

    {
        std::ofstream yaml(path);
        yaml << R"(
name: conduction_parser
geometry:
  well_radius_m: 1.0
  outer_radius_factor: 3.0
mesh:
  n_elements_radial: 4
  ratio: 1.0
lithology:
  primary: halita
fluid:
  pressure_Pa: 1.0e6
thermal:
  enabled: true
  mode: conduction_1d
  initial_temp_C: 40.0
  inner_wall_temp_C: 90.0
  outer_temp_C: 50.0
  outer_bc: flux_zero
  k_W_m_K: 4.0
  rho_kg_m3: 2100.0
  cp_J_kg_K: 920.0
  dt_thermal_h: 0.25
  beta: 0.5
creep:
  elastic_only: true
)";
    }

    CaseData cd = parse_case(path, find_data_dir());
    REQUIRE(cd.thermal.mode == "conduction_1d");
    REQUIRE(cd.thermal.outer_bc == "flux_zero");
    REQUIRE(cd.thermal.inner_wall_T_K == Catch::Approx(363.15));
    REQUIRE(cd.thermal.outer_T_K == Catch::Approx(323.15));
    REQUIRE(cd.thermal.k_W_m_K == Catch::Approx(4.0));
    REQUIRE(cd.thermal.dt_thermal_s == Catch::Approx(0.25 * 3600.0));

    fs::remove(path);
}
