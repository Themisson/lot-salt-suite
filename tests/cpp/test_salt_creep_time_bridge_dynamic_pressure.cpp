#include <cmath>
#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepTimeBridge.hpp"

namespace {

constexpr double kRi = 0.1556;
constexpr double kRe = 10.0 * kRi;
constexpr double kE = 25.0e9;
constexpr double kNu = 0.30;
constexpr double kPressure = 10.0e6;

lss::salt::SaltCreepTimeBridgeConfig dynamic_bridge_config(
    double initial_pressure_Pa = 0.0) {
  lss::salt::SaltCreepTimeBridgeConfig config;
  config.inner_radius_m = kRi;
  config.outer_radius_m = kRe;
  config.height_m = 1.0;
  config.radial_elements = 100;
  config.elastic_modulus_Pa = kE;
  config.poisson_ratio = kNu;
  config.temperature_K = 350.0;
  config.reference_temperature_K = 350.0;
  config.alpha_thermal_1_K = 0.0;
  config.wall_pressure_Pa = initial_pressure_Pa;
  return config;
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

TEST_CASE("SaltCreepTimeBridge dynamic pressure preserves constant Lame response") {
  lss::salt::SaltCreepTimeBridge bridge(
      dynamic_bridge_config(kPressure));

  const auto response = bridge.advance_to(60.0, kPressure);
  const double u_exact =
      lame_radial_displacement(kRi, kRi, kRe, kPressure, 0.0, kE, kNu);
  const double rel_error =
      std::abs(response.wall_displacement_m - u_exact) / std::abs(u_exact);

  CHECK(response.valid);
  CHECK(response.current_time_s == Catch::Approx(60.0));
  CHECK(response.wall_displacement_m > 0.0);
  CHECK(response.radial_closure_m == Catch::Approx(0.0));
  CHECK(rel_error < 1.0e-6);
}

TEST_CASE("SaltCreepTimeBridge accepts variable pressure and returns finite result") {
  lss::salt::SaltCreepTimeBridge bridge(dynamic_bridge_config());

  const auto first = bridge.advance_to(60.0, 0.5 * kPressure);
  const auto second = bridge.advance_to(120.0, kPressure);

  CHECK(first.valid);
  CHECK(second.valid);
  CHECK(std::isfinite(first.wall_displacement_m));
  CHECK(std::isfinite(second.wall_displacement_m));
  CHECK(second.current_time_s == Catch::Approx(120.0));
  CHECK(second.step_count == 2);
}

TEST_CASE("SaltCreepTimeBridge applies the latest dynamic wall pressure") {
  lss::salt::SaltCreepTimeBridge bridge(dynamic_bridge_config());

  const auto first = bridge.advance_to(60.0, 0.5 * kPressure);
  const auto second = bridge.advance_to(120.0, kPressure);
  const double u_half =
      lame_radial_displacement(kRi, kRi, kRe, 0.5 * kPressure, 0.0, kE, kNu);
  const double u_full =
      lame_radial_displacement(kRi, kRi, kRe, kPressure, 0.0, kE, kNu);

  CHECK(first.wall_displacement_m == Catch::Approx(u_half).epsilon(1.0e-6));
  CHECK(second.wall_displacement_m == Catch::Approx(u_full).epsilon(1.0e-6));
  CHECK(second.wall_displacement_m > first.wall_displacement_m);
}

TEST_CASE("SaltCreepTimeBridge still rejects decreasing time with dynamic pressure") {
  lss::salt::SaltCreepTimeBridge bridge(dynamic_bridge_config());

  CHECK(bridge.advance_to(120.0, kPressure).valid);
  CHECK_THROWS_AS(bridge.advance_to(60.0, 0.5 * kPressure),
                  std::invalid_argument);
}

TEST_CASE("SaltCreepTimeBridge rejects negative dynamic pressure") {
  lss::salt::SaltCreepTimeBridge bridge(dynamic_bridge_config());

  CHECK_THROWS_AS(bridge.advance_to(60.0, -1.0), std::invalid_argument);
}

TEST_CASE("SaltCreepTimeBridge rejects non-finite dynamic pressure") {
  lss::salt::SaltCreepTimeBridge bridge(dynamic_bridge_config());

  CHECK_THROWS_AS(
      bridge.advance_to(60.0, std::numeric_limits<double>::quiet_NaN()),
      std::invalid_argument);
}
