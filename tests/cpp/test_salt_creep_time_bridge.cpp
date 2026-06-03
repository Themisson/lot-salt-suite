#include <cmath>
#include <stdexcept>
#include <type_traits>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepTimeBridge.hpp"

#if __has_include("solver/TimeIntegrator.hpp")
#error "SaltCreepTimeBridge public test target must not expose saltcreep headers"
#endif

namespace {

lss::salt::SaltCreepTimeBridgeConfig bridge_config() {
  lss::salt::SaltCreepTimeBridgeConfig config;
  config.inner_radius_m = 0.1556;
  config.outer_radius_m = 10.0 * config.inner_radius_m;
  config.height_m = 1.0;
  config.radial_elements = 40;
  config.elastic_modulus_Pa = 25.0e9;
  config.poisson_ratio = 0.30;
  config.temperature_K = 350.0;
  config.reference_temperature_K = 350.0;
  config.alpha_thermal_1_K = 0.0;
  config.wall_pressure_Pa = 10.0e6;
  return config;
}

}  // namespace

TEST_CASE("SaltCreepTimeBridge compiles behind clean public header") {
  STATIC_REQUIRE(!std::is_copy_constructible_v<lss::salt::SaltCreepTimeBridge>);
  STATIC_REQUIRE(std::is_move_constructible_v<lss::salt::SaltCreepTimeBridge>);

  const lss::salt::SaltCreepTimeBridge bridge(bridge_config());

  CHECK(bridge.is_available());
  CHECK(bridge.config().radial_elements == 40);
}

TEST_CASE("SaltCreepTimeBridge exposes initial finite TimeIntegrator result") {
  const lss::salt::SaltCreepTimeBridge bridge(bridge_config());

  const auto result = bridge.result();

  CHECK(result.valid);
  CHECK(result.current_time_s == Catch::Approx(0.0));
  CHECK(result.step_count == 0);
  CHECK(std::isfinite(result.wall_displacement_m));
  CHECK(std::isfinite(result.radial_closure_m));
  CHECK(result.radial_closure_m >= 0.0);
}

TEST_CASE("SaltCreepTimeBridge advances TimeIntegrator with neutral thermal field") {
  lss::salt::SaltCreepTimeBridge bridge(bridge_config());

  const auto initial = bridge.result();
  const auto after_first = bridge.advance_by(60.0);
  const auto after_second = bridge.advance_to(120.0);

  CHECK(after_first.valid);
  CHECK(after_second.valid);
  CHECK(after_first.current_time_s == Catch::Approx(60.0));
  CHECK(after_second.current_time_s == Catch::Approx(120.0));
  CHECK(after_second.step_count == 2);
  CHECK(std::isfinite(after_second.wall_displacement_m));
  CHECK(after_second.radial_closure_m >= 0.0);
  CHECK(after_second.wall_displacement_m ==
        Catch::Approx(initial.wall_displacement_m).epsilon(1.0e-12));
}

TEST_CASE("SaltCreepTimeBridge rejects decreasing target time") {
  lss::salt::SaltCreepTimeBridge bridge(bridge_config());

  CHECK(bridge.advance_to(120.0).valid);
  CHECK_THROWS_AS(bridge.advance_to(60.0), std::invalid_argument);
  CHECK(bridge.result().current_time_s == Catch::Approx(120.0));
  CHECK(bridge.result().step_count == 1);
}

TEST_CASE("SaltCreepTimeBridge rejects invalid SI configuration") {
  auto config = bridge_config();
  config.outer_radius_m = config.inner_radius_m;

  CHECK_THROWS_AS(lss::salt::SaltCreepTimeBridge(config),
                  std::invalid_argument);
}

TEST_CASE("SaltCreepTimeBridge remains independent from LOT PKN types") {
  lss::salt::SaltCreepTimeBridge bridge(bridge_config());
  const auto result = bridge.advance_by(30.0);

  CHECK(result.valid);
  CHECK(result.current_time_s == Catch::Approx(30.0));
  CHECK(result.step_count == 1);
}
