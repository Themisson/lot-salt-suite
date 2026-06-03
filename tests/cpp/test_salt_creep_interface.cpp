#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepInterface.hpp"

namespace {

lss::salt::SaltCreepQuery valid_query() {
  return {
      3600.0,     // time_s
      35.0e6,     // wall_pressure_Pa
      363.15,     // temperature_K
      0.155575,   // radial_position_m
  };
}

}  // namespace

TEST_CASE("NullSaltCreepInterface reports unavailable solver") {
  const lss::salt::NullSaltCreepInterface salt;

  CHECK_FALSE(salt.is_available());
}

TEST_CASE("NullSaltCreepInterface returns neutral response for valid SI query") {
  const lss::salt::NullSaltCreepInterface salt;

  const auto response = salt.evaluate_wall_response(valid_query());

  CHECK(response.valid);
  CHECK(response.radial_displacement_m == Catch::Approx(0.0));
  CHECK(response.radial_closure_m == Catch::Approx(0.0));
  CHECK(response.radial_strain == Catch::Approx(0.0));
  CHECK(response.effective_closure_pressure_Pa == Catch::Approx(0.0));
}

TEST_CASE("NullSaltCreepInterface rejects NaN query values") {
  const lss::salt::NullSaltCreepInterface salt;
  auto query = valid_query();
  query.wall_pressure_Pa = std::numeric_limits<double>::quiet_NaN();

  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("NullSaltCreepInterface rejects infinite query values") {
  const lss::salt::NullSaltCreepInterface salt;
  auto query = valid_query();
  query.temperature_K = std::numeric_limits<double>::infinity();

  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("NullSaltCreepInterface rejects negative time") {
  const lss::salt::NullSaltCreepInterface salt;
  auto query = valid_query();
  query.time_s = -1.0;

  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("NullSaltCreepInterface rejects negative wall pressure") {
  const lss::salt::NullSaltCreepInterface salt;
  auto query = valid_query();
  query.wall_pressure_Pa = -1.0;

  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("NullSaltCreepInterface rejects non-positive temperature") {
  const lss::salt::NullSaltCreepInterface salt;
  auto query = valid_query();
  query.temperature_K = 0.0;

  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);

  query.temperature_K = -273.15;
  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("NullSaltCreepInterface rejects negative radial position") {
  const lss::salt::NullSaltCreepInterface salt;
  auto query = valid_query();
  query.radial_position_m = -1.0e-3;

  CHECK_THROWS_AS(salt.evaluate_wall_response(query), std::invalid_argument);
}

TEST_CASE("Salt creep contract stores wall pressure samples in SI units") {
  const lss::salt::WallPressureSample sample{120.0, 12.5e6};
  const auto query = valid_query();

  CHECK(sample.time_s == Catch::Approx(120.0));
  CHECK(sample.pressure_Pa == Catch::Approx(12.5e6));
  CHECK(query.time_s == Catch::Approx(3600.0));
  CHECK(query.wall_pressure_Pa == Catch::Approx(35.0e6));
  CHECK(query.temperature_K == Catch::Approx(363.15));
  CHECK(query.radial_position_m == Catch::Approx(0.155575));
}

TEST_CASE("Salt creep response sign convention separates displacement from closure") {
  lss::salt::SaltCreepResponse inward;
  inward.radial_displacement_m = -2.0e-3;
  inward.radial_closure_m = 2.0e-3;
  inward.radial_strain = -1.0e-2;
  inward.effective_closure_pressure_Pa = 5.0e6;
  inward.valid = true;

  CHECK(inward.valid);
  CHECK(inward.radial_displacement_m < 0.0);
  CHECK(inward.radial_closure_m == Catch::Approx(-inward.radial_displacement_m));
  CHECK(inward.radial_strain < 0.0);
  CHECK(inward.effective_closure_pressure_Pa >= 0.0);

  lss::salt::SaltCreepResponse outward;
  outward.radial_displacement_m = 1.0e-3;
  outward.radial_closure_m = 0.0;
  outward.radial_strain = 5.0e-3;
  outward.effective_closure_pressure_Pa = 0.0;
  outward.valid = true;

  CHECK(outward.valid);
  CHECK(outward.radial_displacement_m > 0.0);
  CHECK(outward.radial_closure_m == Catch::Approx(0.0));
  CHECK(outward.radial_strain > 0.0);
  CHECK(outward.effective_closure_pressure_Pa == Catch::Approx(0.0));
}
