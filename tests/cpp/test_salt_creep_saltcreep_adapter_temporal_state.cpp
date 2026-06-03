#include <cmath>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepSaltcreepAdapter.hpp"

namespace {

constexpr double kInnerRadius = 0.1556;
constexpr double kOuterRadius = 10.0 * kInnerRadius;
constexpr double kPressure = 10.0e6;

lss::salt::SaltCreepAdapterConfig temporal_config() {
  auto config = lss::salt::make_default_salt_creep_adapter_config();
  config.geometry.inner_radius_m = kInnerRadius;
  config.geometry.outer_radius_m = kOuterRadius;
  config.mesh.radial_elements = 40;
  config.time.dt_s = 60.0;
  config.time.total_time_s = 240.0;
  config.time.max_steps = 4;
  config.wall_pressure.initial_wall_pressure_Pa = kPressure;
  return config;
}

lss::salt::SaltCreepQuery temporal_query(double time_s, double pressure_Pa) {
  return {
      time_s,
      pressure_Pa,
      350.0,
      kInnerRadius,
  };
}

}  // namespace

TEST_CASE("SaltCreepSaltcreepAdapter persists minimum backend objects across temporal queries") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(temporal_config());

  CHECK(adapter.is_available());
  CHECK(adapter.backend_build_count() == 0);

  const auto first = adapter.evaluate_wall_response(
      temporal_query(60.0, kPressure));
  const auto second = adapter.evaluate_wall_response(
      temporal_query(120.0, kPressure));

  CHECK(first.valid);
  CHECK(second.valid);
  CHECK(std::isfinite(first.radial_displacement_m));
  CHECK(std::isfinite(second.radial_displacement_m));
  CHECK(adapter.backend_build_count() == 1);
  CHECK(adapter.state().step_count() == 2);
  CHECK(adapter.state().current_time_s() == Catch::Approx(120.0));
  CHECK(adapter.state().last_wall_pressure_Pa() == Catch::Approx(kPressure));
}

TEST_CASE("SaltCreepSaltcreepAdapter preserves cached backend when state rejects decreasing time") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(temporal_config());

  CHECK(adapter.evaluate_wall_response(temporal_query(120.0, kPressure)).valid);
  CHECK(adapter.backend_build_count() == 1);

  CHECK_THROWS_AS(adapter.evaluate_wall_response(
                      temporal_query(60.0, kPressure)),
                  std::invalid_argument);

  CHECK(adapter.backend_build_count() == 1);
  CHECK(adapter.state().step_count() == 1);
  CHECK(adapter.state().current_time_s() == Catch::Approx(120.0));
}

TEST_CASE("SaltCreepSaltcreepAdapter does not build backend cache for unsupported temporal config") {
  auto config = temporal_config();
  config.mesh.axial_elements = 2;
  const lss::salt::SaltCreepSaltcreepAdapter adapter(config);

  CHECK_FALSE(adapter.is_available());
  CHECK(adapter.backend_build_count() == 0);

  CHECK_THROWS_AS(adapter.evaluate_wall_response(
                      temporal_query(60.0, kPressure)),
                  std::logic_error);

  CHECK(adapter.backend_build_count() == 0);
}

TEST_CASE("SaltCreepSaltcreepAdapter rejects dynamic wall pressure until bridge supports it") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter(temporal_config());

  CHECK_THROWS_AS(adapter.evaluate_wall_response(
                      temporal_query(60.0, 1.2 * kPressure)),
                  std::invalid_argument);
  CHECK(adapter.backend_build_count() == 0);
  CHECK(adapter.state().step_count() == 0);
}
