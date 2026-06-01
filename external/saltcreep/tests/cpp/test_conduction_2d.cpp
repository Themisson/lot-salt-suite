#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <stdexcept>

#include "elements/axisym_2d_q4.hpp"
#include "elements/axisym_2d_q8.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "thermal/conduction_1d_field.hpp"
#include "thermal/conduction_2d_field.hpp"

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
} // namespace

TEST_CASE("Conduction2DField: uniform Q8 solution matches radial Conduction1D",
          "[thermal][conduction_2d]") {
    const double Ri = 1.0;
    const double Re = 3.0;
    Mesh1D mesh_1d = build_mesh_L3(Ri, Re, 12, 1.0);
    Mesh2D mesh_2d = build_mesh_structured_2d("axisym_2d_Q8", Ri, Re, 1.0, 12, 1, 1.0);
    AxisymQ8 q8;

    Conduction1DOptions opt1;
    opt1.k_W_m_K = 5.0;
    opt1.rho_kg_m3 = 50.0;
    opt1.cp_J_kg_K = 2.0;
    opt1.initial_T_K = 300.0;
    opt1.inner_wall_T_K = 360.0;
    opt1.outer_T_K = 310.0;
    opt1.dt_thermal_s = 0.05;
    opt1.outer_bc = "prescribed";

    Conduction2DOptions opt2;
    opt2.k_W_m_K = opt1.k_W_m_K;
    opt2.rho_kg_m3 = opt1.rho_kg_m3;
    opt2.cp_J_kg_K = opt1.cp_J_kg_K;
    opt2.initial_T_K = opt1.initial_T_K;
    opt2.inner_wall_T_K = opt1.inner_wall_T_K;
    opt2.outer_T_K = opt1.outer_T_K;
    opt2.dt_thermal_s = opt1.dt_thermal_s;
    opt2.outer_bc = "prescribed";
    opt2.top_bc = "flux_zero";
    opt2.bottom_bc = "flux_zero";

    Conduction1DField field_1d(mesh_1d, opt1);
    Conduction2DField field_2d(mesh_2d, q8, opt2);

    const double t = 1.0;
    for (double r : {1.0, 1.25, 1.75, 2.5, 3.0}) {
        const double T1 = field_1d.temperature_at(Eigen::Vector2d(r, 0.0), t);
        const double T2 = field_2d.temperature_at(Eigen::Vector2d(r, 0.5), t);
        REQUIRE(T2 == Catch::Approx(T1).margin(2.0e-2));
    }
}

TEST_CASE("Conduction2DField: prescribed radial steady state reproduces logarithmic profile",
          "[thermal][conduction_2d]") {
    const double Ri = 1.0;
    const double Re = 3.0;
    const double Ti = 400.0;
    const double Te = 300.0;
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q8", Ri, Re, 1.0, 8, 1, 1.0);
    AxisymQ8 q8;

    Conduction2DOptions options;
    options.k_W_m_K = 1000.0;
    options.rho_kg_m3 = 1000.0;
    options.cp_J_kg_K = 1.0;
    options.initial_T_K = Te;
    options.inner_wall_T_K = Ti;
    options.outer_T_K = Te;
    options.dt_thermal_s = 0.25;
    options.outer_bc = "prescribed";
    options.top_bc = "flux_zero";
    options.bottom_bc = "flux_zero";

    Conduction2DField field(mesh, q8, options);
    field.advance_to(2000.0);

    double max_error = 0.0;
    for (double r : {1.05, 1.5, 2.0, 2.75}) {
        const double numerical = field.temperature_at(Eigen::Vector2d(r, 0.5), 2000.0);
        const double exact = log_profile(r, Ri, Re, Ti, Te);
        max_error = std::max(max_error, std::abs(numerical - exact));
    }
    REQUIRE(max_error < 0.6);
}

TEST_CASE("Conduction2DField: low-conductivity layer slows radial heating",
          "[thermal][conduction_2d]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 2.0, 1.0, 12, 2, 1.0);
    AxisymQ4 q4;

    Conduction2DOptions options;
    options.k_W_m_K = 5.0;
    options.rho_kg_m3 = 100.0;
    options.cp_J_kg_K = 2.0;
    options.initial_T_K = 300.0;
    options.inner_wall_T_K = 400.0;
    options.dt_thermal_s = 0.02;
    options.outer_bc = "flux_zero";
    options.top_bc = "flux_zero";
    options.bottom_bc = "flux_zero";
    options.layers = {
        Conduction2DLayer{0.0, 0.5, 20.0, 100.0, 2.0},
        Conduction2DLayer{0.5, 1.0, 0.4, 100.0, 2.0},
    };

    Conduction2DField field(mesh, q4, options);
    const double t = 0.35;
    const double high_k = field.temperature_at(Eigen::Vector2d(1.35, 0.25), t);
    const double low_k = field.temperature_at(Eigen::Vector2d(1.35, 0.75), t);

    REQUIRE(high_k > low_k + 0.5);
}

TEST_CASE("Conduction2DField: discrete energy balance matches prescribed-boundary heat",
          "[thermal][conduction_2d]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 2.0, 1.0, 10, 2, 1.0);
    AxisymQ4 q4;

    Conduction2DOptions options;
    options.k_W_m_K = 3.0;
    options.rho_kg_m3 = 20.0;
    options.cp_J_kg_K = 2.0;
    options.initial_T_K = 300.0;
    options.inner_wall_T_K = 360.0;
    options.dt_thermal_s = 0.1;
    options.outer_bc = "flux_zero";
    options.top_bc = "flux_zero";
    options.bottom_bc = "flux_zero";

    Conduction2DField field(mesh, q4, options);
    const double E0 = field.total_energy_J();
    field.advance_to(0.1);
    const double E1 = field.total_energy_J();

    const double dE = E1 - E0;
    const double q_boundary = field.last_boundary_heat_J();
    const double scale = std::max({std::abs(dE), std::abs(q_boundary), 1.0});
    REQUIRE(std::abs(dE - q_boundary) / scale < 1.0e-10);
}

TEST_CASE("CaseParser: conduction_2d accepts layers and boundary conditions",
          "[thermal][parser]") {
    const fs::path path = fs::temp_directory_path() / "saltcreep_conduction_2d_case.yaml";

    {
        std::ofstream yaml(path);
        yaml << R"(
name: conduction_2d_parser
geometry:
  well_radius_m: 1.0
  outer_radius_factor: 3.0
mesh:
  n_elements_radial: 4
  n_elements_axial: 2
  ratio: 1.0
element:
  type: axisym_2d_Q8
lithology:
  primary: halita
fluid:
  pressure_Pa: 1.0e6
thermal:
  enabled: true
  mode: conduction_2d
  initial_temp_C: 40.0
  inner_wall_temp_C: 90.0
  outer_temp_C: 50.0
  top_temp_C: 30.0
  bottom_temp_C: 70.0
  outer_bc: prescribed
  top_bc: flux_zero
  bottom_bc: prescribed
  dt_thermal_h: 0.25
  beta: 0.5
  layers:
    - z_top_m: 0.0
      z_bottom_m: 0.5
      k_W_per_mK: 5.4
      rho_kg_per_m3: 2160.0
      cp_J_per_kgK: 860.0
    - z_top_m: 0.5
      z_bottom_m: 1.0
      k_W_per_mK: 3.1
      rho_kg_per_m3: 1600.0
      cp_J_per_kgK: 920.0
creep:
  elastic_only: true
)";
    }

    CaseData cd = parse_case(path, find_data_dir());
    REQUIRE(cd.thermal.mode == "conduction_2d");
    REQUIRE(cd.thermal.outer_bc == "prescribed");
    REQUIRE(cd.thermal.top_bc == "flux_zero");
    REQUIRE(cd.thermal.bottom_bc == "prescribed");
    REQUIRE(cd.thermal.top_T_K == Catch::Approx(303.15));
    REQUIRE(cd.thermal.bottom_T_K == Catch::Approx(343.15));
    REQUIRE(cd.thermal.layers.size() == 2);
    REQUIRE(cd.thermal.layers[0].k_W_m_K == Catch::Approx(5.4));
    REQUIRE(cd.thermal.layers[1].rho_kg_m3 == Catch::Approx(1600.0));

    fs::remove(path);
}
