#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepAdapterState.hpp"

namespace {

lss::salt::SaltCreepResponse valid_response() {
  lss::salt::SaltCreepResponse response;
  response.radial_displacement_m = -1.0e-3;
  response.radial_closure_m = 1.0e-3;
  response.radial_strain = -2.0e-4;
  response.effective_closure_pressure_Pa = 2.0e6;
  response.valid = true;
  return response;
}

}  // namespace

TEST_CASE("SaltCreepAdapterState starts uninitialized") {
  const lss::salt::SaltCreepAdapterState state;

  CHECK_FALSE(state.initialized());
  CHECK(state.current_time_s() == Catch::Approx(0.0));
  CHECK(state.last_wall_pressure_Pa() == Catch::Approx(0.0));
  CHECK(state.last_radial_displacement_m() == Catch::Approx(0.0));
  CHECK(state.last_radial_closure_m() == Catch::Approx(0.0));
  CHECK(state.step_count() == 0);
}

TEST_CASE("SaltCreepAdapterState initializes from SI time and wall pressure") {
  lss::salt::SaltCreepAdapterState state;

  state.initialize(60.0, 10.0e6);

  CHECK(state.initialized());
  CHECK(state.current_time_s() == Catch::Approx(60.0));
  CHECK(state.last_wall_pressure_Pa() == Catch::Approx(10.0e6));
  CHECK(state.last_radial_displacement_m() == Catch::Approx(0.0));
  CHECK(state.last_radial_closure_m() == Catch::Approx(0.0));
  CHECK(state.step_count() == 0);
}

TEST_CASE("SaltCreepAdapterState records valid responses in nondecreasing time") {
  lss::salt::SaltCreepAdapterState state;
  state.initialize(0.0, 0.0);

  state.record_response(60.0, 8.0e6, valid_response());

  CHECK(state.initialized());
  CHECK(state.current_time_s() == Catch::Approx(60.0));
  CHECK(state.last_wall_pressure_Pa() == Catch::Approx(8.0e6));
  CHECK(state.last_radial_displacement_m() == Catch::Approx(-1.0e-3));
  CHECK(state.last_radial_closure_m() == Catch::Approx(1.0e-3));
  CHECK(state.step_count() == 1);
}

TEST_CASE("SaltCreepAdapterState resets to uninitialized neutral state") {
  lss::salt::SaltCreepAdapterState state;
  state.initialize(0.0, 0.0);
  state.record_response(60.0, 8.0e6, valid_response());

  state.reset();

  CHECK_FALSE(state.initialized());
  CHECK(state.current_time_s() == Catch::Approx(0.0));
  CHECK(state.last_wall_pressure_Pa() == Catch::Approx(0.0));
  CHECK(state.last_radial_displacement_m() == Catch::Approx(0.0));
  CHECK(state.last_radial_closure_m() == Catch::Approx(0.0));
  CHECK(state.step_count() == 0);
}

TEST_CASE("SaltCreepAdapterState rejects invalid initialization and responses") {
  lss::salt::SaltCreepAdapterState state;

  CHECK_THROWS_AS(state.initialize(-1.0, 0.0), std::invalid_argument);
  CHECK_THROWS_AS(state.initialize(0.0, -1.0), std::invalid_argument);
  CHECK_THROWS_AS(state.record_response(0.0, 0.0, valid_response()),
                  std::logic_error);

  state.initialize(10.0, 0.0);
  CHECK_THROWS_AS(state.record_response(9.0, 0.0, valid_response()),
                  std::invalid_argument);
  CHECK_THROWS_AS(state.record_response(10.0, -1.0, valid_response()),
                  std::invalid_argument);

  auto response = valid_response();
  response.radial_closure_m = -1.0;
  CHECK_THROWS_AS(state.record_response(10.0, 0.0, response),
                  std::invalid_argument);

  response = valid_response();
  response.radial_displacement_m =
      std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(state.record_response(10.0, 0.0, response),
                  std::invalid_argument);

  response = valid_response();
  response.valid = false;
  CHECK_THROWS_AS(state.record_response(10.0, 0.0, response),
                  std::invalid_argument);
}
