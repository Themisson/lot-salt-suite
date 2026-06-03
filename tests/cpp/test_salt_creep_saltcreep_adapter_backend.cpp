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

lss::salt::SaltCreepAdapterConfig elastic_config() {
  auto config = lss::salt::make_default_salt_creep_adapter_config();
  config.geometry.inner_radius_m = kRi;
  config.geometry.outer_radius_m = kRe;
  config.mesh.radial_elements = 100;
  config.material.elastic_modulus_Pa = kE;
  config.material.poisson_ratio = kNu;
  config.time.total_time_s = 240.0;
  config.wall_pressure.initial_wall_pressure_Pa = kPressure;
  return config;
}

lss::salt::SaltCreepQuery query(double time_s, double pressure_Pa) {
  return {
      time_s,
      pressure_Pa,
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

TEST_CASE("SaltCreepSaltcreepAdapter minimum backend is available for default config") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter;

  CHECK(adapter.is_available());
}

TEST_CASE("SaltCreepSaltcreepAdapter minimum backend matches controlled Lame inner pressure") {
  const auto config = elastic_config();
  const lss::salt::SaltCreepSaltcreepAdapter adapter(config);

  const auto response = adapter.evaluate_wall_response(query(60.0, kPressure));
  const double u_exact =
      lame_radial_displacement(kRi, kRi, kRe, kPressure, 0.0, kE, kNu);
  const double rel_error =
      std::abs(response.radial_displacement_m - u_exact) / std::abs(u_exact);

  CHECK(response.valid);
  CHECK(response.radial_displacement_m > 0.0);
  CHECK(response.radial_closure_m == Catch::Approx(0.0));
  CHECK(response.radial_closure_m ==
        Catch::Approx(std::max(0.0, -response.radial_displacement_m)));
  CHECK(rel_error < 1.0e-6);
}

TEST_CASE("SaltCreepSaltcreepAdapter minimum backend maps geostatic compression to closure") {
  auto config = elastic_config();
  config.geostatic.enabled = true;
  config.geostatic.radial_stress_Pa = -2.0e6;
  config.geostatic.hoop_stress_Pa = -2.0e6;
  config.geostatic.vertical_stress_Pa = -2.0e6;
  config.wall_pressure.initial_wall_pressure_Pa = 0.0;
  const lss::salt::SaltCreepSaltcreepAdapter adapter(config);

  const auto response = adapter.evaluate_wall_response(query(60.0, 0.0));

  CHECK(response.valid);
  CHECK(std::isfinite(response.radial_displacement_m));
  CHECK(response.radial_displacement_m < 0.0);
  CHECK(response.radial_closure_m > 0.0);
  CHECK(response.radial_closure_m ==
        Catch::Approx(std::max(0.0, -response.radial_displacement_m)));
  CHECK(response.radial_strain < 0.0);
}

TEST_CASE("SaltCreepSaltcreepAdapter records response in logically const evaluation") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(elastic_config());

  const auto first = adapter.evaluate_wall_response(query(60.0, kPressure));
  const auto second = adapter.evaluate_wall_response(query(120.0, kPressure));

  CHECK(first.valid);
  CHECK(second.valid);
  CHECK(adapter.state().step_count() == 2);
  CHECK(adapter.state().current_time_s() == Catch::Approx(120.0));
  CHECK(adapter.state().last_wall_pressure_Pa() == Catch::Approx(kPressure));
  CHECK(adapter.state().last_radial_displacement_m() ==
        Catch::Approx(second.radial_displacement_m));
  CHECK(adapter.state().last_radial_closure_m() ==
        Catch::Approx(second.radial_closure_m));
}

TEST_CASE("SaltCreepSaltcreepAdapter rejects decreasing query time through state machine") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(elastic_config());

  CHECK(adapter.evaluate_wall_response(query(120.0, kPressure)).valid);
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query(60.0, kPressure)),
                  std::invalid_argument);
}

TEST_CASE("SaltCreepSaltcreepAdapter reports unavailable unsupported backend config") {
  auto config = elastic_config();
  config.geometry.axisymmetric = false;
  const lss::salt::SaltCreepSaltcreepAdapter adapter(config);

  CHECK_FALSE(adapter.is_available());
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query(60.0, kPressure)),
                  std::logic_error);
}
