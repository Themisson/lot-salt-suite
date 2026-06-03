#include <algorithm>
#include <cmath>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "solver/Assembler.hpp"
#include "solver/ElasticSolver.hpp"
#include "solver/WallPressureField.hpp"

namespace {

constexpr double kRi = 0.1556;
constexpr double kRe = 10.0 * kRi;
constexpr double kE = 25.0e9;
constexpr double kNu = 0.30;
constexpr double kPressure = 10.0e6;

double lame_A(double Ri, double Re, double p_inner, double p_outer) {
  return (p_inner * Ri * Ri - p_outer * Re * Re) / (Re * Re - Ri * Ri);
}

double lame_B(double Ri, double Re, double p_inner, double p_outer) {
  return (p_inner - p_outer) * Ri * Ri * Re * Re / (Re * Re - Ri * Ri);
}

double lame_radial_displacement(double r,
                                double Ri,
                                double Re,
                                double p_inner,
                                double p_outer,
                                double E,
                                double nu) {
  const double A = lame_A(Ri, Re, p_inner, p_outer);
  const double B = lame_B(Ri, Re, p_inner, p_outer);
  return (1.0 + nu) / E * ((1.0 - 2.0 * nu) * A * r + B / r);
}

double positive_closure(double radial_displacement_m) {
  return std::max(0.0, -radial_displacement_m);
}

Eigen::VectorXd run_controlled_lame(double p_inner, double p_outer) {
  // Controlled synthetic Lame case: linear elasticity, small strains,
  // no creep, no damage, no thermal coupling, no LOT/PKN coupling.
  AxisymL3 element;
  ElasticIsotropic model(kE, kNu);
  Mesh1D mesh = build_mesh_L3(kRi, kRe, 100, 1000.0);
  ConstantWallPressureField inner_pressure(p_inner);

  auto K = Assembler::assemble_K(mesh, element, model);
  auto f = Assembler::assemble_boundary_pressure(
      mesh, element, inner_pressure, 0.0, p_outer);

  return ElasticSolver{}.solve(std::move(K), std::move(f), {}).u;
}

}  // namespace

TEST_CASE("Saltcreep backend controlled Lame case maps inner wall pressure to outward displacement") {
  const auto u = run_controlled_lame(kPressure, 0.0);

  const double u_wall = u[0];
  const double u_exact =
      lame_radial_displacement(kRi, kRi, kRe, kPressure, 0.0, kE, kNu);
  const double rel_error = std::abs(u_wall - u_exact) / std::abs(u_exact);

  CHECK(u_wall > 0.0);
  CHECK(positive_closure(u_wall) == Catch::Approx(0.0));
  CHECK(rel_error < 1.0e-6);
}

TEST_CASE("Saltcreep backend controlled Lame case maps confining pressure to inward closure") {
  const auto u = run_controlled_lame(0.0, kPressure);

  const double u_wall = u[0];
  const double u_exact =
      lame_radial_displacement(kRi, kRi, kRe, 0.0, kPressure, kE, kNu);
  const double rel_error = std::abs(u_wall - u_exact) / std::abs(u_exact);

  CHECK(u_wall < 0.0);
  CHECK(positive_closure(u_wall) == Catch::Approx(-u_wall));
  CHECK(positive_closure(u_wall) > 0.0);
  CHECK(rel_error < 1.0e-6);
}
