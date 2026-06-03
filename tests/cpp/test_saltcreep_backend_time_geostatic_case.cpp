#include <algorithm>
#include <cmath>
#include <memory>
#include <vector>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "solver/Assembler.hpp"
#include "solver/ElasticSolver.hpp"
#include "solver/TimeIntegrator.hpp"
#include "solver/WallPressureField.hpp"
#include "thermal/profile_field.hpp"

namespace {

constexpr double kRi = 0.1556;
constexpr double kRe = 10.0 * kRi;
constexpr double kE = 25.0e9;
constexpr double kNu = 0.30;
constexpr double kPressure = 10.0e6;
constexpr double kDt = 60.0;

std::vector<Stress> uniform_geostatic(const Mesh& mesh,
                                      const Element& element,
                                      double sigma_v,
                                      double k0) {
  const int total_gp =
      mesh.n_elements * static_cast<int>(element.gauss_points().size());
  const double sigma_h = k0 * sigma_v;
  return std::vector<Stress>(total_gp, Stress{sigma_h, sigma_h, sigma_v, 0.0});
}

double positive_closure(double radial_displacement_m) {
  return std::max(0.0, -radial_displacement_m);
}

}  // namespace

TEST_CASE("Saltcreep backend time integrator preserves static elastic Lame response with neutral fields") {
  AxisymL3 element;
  ElasticIsotropic model(kE, kNu);
  Mesh1D mesh = build_mesh_L3(kRi, kRe, 100, 1000.0);
  ProfileField thermal = ProfileField::make_constant(350.0, 0.0, 350.0);
  auto wall_pressure = std::make_shared<ConstantWallPressureField>(kPressure);

  auto K_static = Assembler::assemble_K(mesh, element, model);
  auto f_static =
      Assembler::assemble_boundary_pressure(mesh, element, *wall_pressure, 0.0);
  const auto u_static =
      ElasticSolver{}.solve(std::move(K_static), f_static, {}).u;

  auto K_time = Assembler::assemble_K(mesh, element, model);
  auto f_time =
      Assembler::assemble_boundary_pressure(mesh, element, *wall_pressure, 0.0);
  TimeIntegrator integrator(mesh,
                            element,
                            model,
                            thermal,
                            std::move(K_time),
                            std::move(f_time),
                            uniform_geostatic(mesh, element, 0.0, 1.0),
                            {},
                            {},
                            wall_pressure);

  const double u_wall_initial = integrator.wall_displacement_m();
  integrator.advance(kDt);
  integrator.advance(kDt);
  const double u_wall_final = integrator.wall_displacement_m();

  CHECK(u_wall_final > 0.0);
  CHECK(positive_closure(u_wall_final) == Catch::Approx(0.0));
  CHECK(u_wall_initial == Catch::Approx(u_static[0]).epsilon(1.0e-12));
  CHECK(u_wall_final == Catch::Approx(u_static[0]).epsilon(1.0e-12));
  CHECK(integrator.wall_closure_pct() ==
        Catch::Approx(-u_wall_final / kRi * 100.0).epsilon(1.0e-12));
}

TEST_CASE("Saltcreep backend time integrator maps simplified compressive geostatic field to closure") {
  AxisymL3 element;
  ElasticIsotropic model(kE, kNu);
  Mesh1D mesh = build_mesh_L3(kRi, kRe, 60, 200.0);
  ProfileField thermal = ProfileField::make_constant(350.0, 0.0, 350.0);
  auto wall_pressure = std::make_shared<ConstantWallPressureField>(0.0);

  auto K = Assembler::assemble_K(mesh, element, model);
  auto f = Assembler::assemble_boundary_pressure(mesh, element, *wall_pressure, 0.0);
  const std::vector<int> fixed_dofs = {mesh.dof_index(mesh.n_nodes - 1, 0)};

  TimeIntegrator integrator(mesh,
                            element,
                            model,
                            thermal,
                            std::move(K),
                            std::move(f),
                            uniform_geostatic(mesh, element, -2.0e6, 1.0),
                            fixed_dofs,
                            {},
                            wall_pressure);

  const double u_wall_initial = integrator.wall_displacement_m();
  integrator.advance(kDt);
  const double u_wall_final = integrator.wall_displacement_m();

  CHECK(std::isfinite(u_wall_final));
  CHECK(u_wall_initial < 0.0);
  CHECK(u_wall_final == Catch::Approx(u_wall_initial).epsilon(1.0e-12));
  CHECK(positive_closure(u_wall_final) == Catch::Approx(-u_wall_final));
  CHECK(integrator.wall_closure_pct() > 0.0);
}
