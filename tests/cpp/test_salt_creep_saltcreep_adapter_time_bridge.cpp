#include <algorithm>
#include <cmath>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepSaltcreepAdapter.hpp"

namespace {

constexpr double kRi = 0.1556;
constexpr double kRe = 10.0 * kRi;
constexpr double kE = 25.0e9;
constexpr double kNu = 0.30;
constexpr double kPressure = 10.0e6;

lss::salt::SaltCreepAdapterConfig bridge_adapter_config() {
  auto config = lss::salt::make_default_salt_creep_adapter_config();
  config.geometry.inner_radius_m = kRi;
  config.geometry.outer_radius_m = kRe;
  config.geometry.height_m = 1.0;
  config.mesh.radial_elements = 100;
  config.mesh.axial_elements = 1;
  config.material.elastic_modulus_Pa = kE;
  config.material.poisson_ratio = kNu;
  config.thermal.temperature_K = 350.0;
  config.thermal.reference_temperature_K = 350.0;
  config.thermal.alpha_thermal_1_K = 0.0;
  config.time.dt_s = 60.0;
  config.time.total_time_s = 240.0;
  config.wall_pressure.initial_wall_pressure_Pa = kPressure;
  return config;
}

lss::salt::SaltCreepQuery bridge_query(double time_s) {
  return {
      time_s,
      kPressure,
      350.0,
      kRi,
  };
}

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

}  // namespace

TEST_CASE("SaltCreepSaltcreepAdapter lazily builds persistent time bridge") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(bridge_adapter_config());

  CHECK(adapter.is_available());
  CHECK(adapter.backend_build_count() == 0);

  const auto first = adapter.evaluate_wall_response(bridge_query(60.0));
  const auto second = adapter.evaluate_wall_response(bridge_query(120.0));

  CHECK(first.valid);
  CHECK(second.valid);
  CHECK(adapter.backend_build_count() == 1);
  CHECK(adapter.state().step_count() == 2);
  CHECK(adapter.state().current_time_s() == Catch::Approx(120.0));
}

TEST_CASE("SaltCreepSaltcreepAdapter time bridge keeps controlled elastic Lame response") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(bridge_adapter_config());

  const auto response = adapter.evaluate_wall_response(bridge_query(60.0));
  const double u_exact =
      lame_radial_displacement(kRi, kRi, kRe, kPressure, 0.0, kE, kNu);
  const double rel_error =
      std::abs(response.radial_displacement_m - u_exact) / std::abs(u_exact);

  CHECK(response.valid);
  CHECK(response.radial_displacement_m > 0.0);
  CHECK(response.radial_closure_m ==
        Catch::Approx(std::max(0.0, -response.radial_displacement_m)));
  CHECK(rel_error < 1.0e-6);
}

TEST_CASE("SaltCreepSaltcreepAdapter rejects unsupported bridge mapping config") {
  auto config = bridge_adapter_config();
  config.geostatic.use_explicit_gauss_point_vector = false;
  const lss::salt::SaltCreepSaltcreepAdapter adapter(config);

  CHECK_FALSE(adapter.is_available());
  CHECK(adapter.backend_build_count() == 0);
  CHECK_THROWS_AS(adapter.evaluate_wall_response(bridge_query(60.0)),
                  std::logic_error);
}

TEST_CASE("SaltCreepSaltcreepAdapter time bridge rejects dynamic pressure policy") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(bridge_adapter_config());
  auto query = bridge_query(60.0);
  query.wall_pressure_Pa = 1.1 * kPressure;

  CHECK_THROWS_AS(adapter.evaluate_wall_response(query), std::invalid_argument);
  CHECK(adapter.backend_build_count() == 0);
}
