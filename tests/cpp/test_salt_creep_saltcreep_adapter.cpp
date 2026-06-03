#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepSaltcreepAdapter.hpp"

namespace {

lss::salt::SaltCreepQuery valid_query() {
  return {
      3600.0,    // time_s
      35.0e6,    // wall_pressure_Pa
      363.15,    // temperature_K
      0.155575,  // radial_position_m
  };
}

}  // namespace

TEST_CASE("SaltCreepSaltcreepAdapter compiles as a SaltCreepInterface") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter;
  const lss::salt::SaltCreepInterface& interface = adapter;

  CHECK_FALSE(interface.is_available());
}

TEST_CASE("SaltCreepSaltcreepAdapter documents unavailable backend") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter;

  CHECK_FALSE(adapter.is_available());
}

TEST_CASE("SaltCreepSaltcreepAdapter returns neutral response while backend is disconnected") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter;

  const auto response = adapter.evaluate_wall_response(valid_query());

  CHECK(response.valid);
  CHECK(response.radial_displacement_m == Catch::Approx(0.0));
  CHECK(response.radial_closure_m == Catch::Approx(0.0));
  CHECK(response.radial_strain == Catch::Approx(0.0));
  CHECK(response.effective_closure_pressure_Pa == Catch::Approx(0.0));
}

TEST_CASE("SaltCreepSaltcreepAdapter rejects invalid query values") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter;

  auto query = valid_query();
  query.time_s = -1.0;
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query), std::invalid_argument);

  query = valid_query();
  query.wall_pressure_Pa = -1.0;
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query), std::invalid_argument);

  query = valid_query();
  query.temperature_K = 0.0;
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query), std::invalid_argument);

  query = valid_query();
  query.radial_position_m = -1.0e-3;
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query), std::invalid_argument);

  query = valid_query();
  query.wall_pressure_Pa = std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(adapter.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("SaltCreepSaltcreepAdapter maps inward displacement to positive closure") {
  CHECK(lss::salt::SaltCreepSaltcreepAdapter::radial_closure_from_displacement(
            -2.0e-3) == Catch::Approx(2.0e-3));
}

TEST_CASE("SaltCreepSaltcreepAdapter maps outward or neutral displacement to zero closure") {
  CHECK(lss::salt::SaltCreepSaltcreepAdapter::radial_closure_from_displacement(
            0.0) == Catch::Approx(0.0));
  CHECK(lss::salt::SaltCreepSaltcreepAdapter::radial_closure_from_displacement(
            1.0e-3) == Catch::Approx(0.0));
}

TEST_CASE("SaltCreepSaltcreepAdapter does not expose LOT PKN dependencies") {
  const lss::salt::SaltCreepSaltcreepAdapter adapter;

  CHECK_FALSE(adapter.is_available());
  CHECK(adapter.evaluate_wall_response(valid_query()).valid);
}
