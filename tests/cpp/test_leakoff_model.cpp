#include <cmath>
#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/LeakoffModel.hpp"
#include "lot/PknModel.hpp"

namespace {

lss::lot::LeakoffState state(double time_s = 0.0, double dt_s = 10.0,
                             double previous_m3 = 0.0) {
  lss::lot::LeakoffState value;
  value.time_s = time_s;
  value.dt_s = dt_s;
  value.previous_cumulative_volume_m3 = previous_m3;
  return value;
}

lss::lot::PknInput pkn_input() {
  lss::lot::PknInput input;
  input.injection.rate_m3_s = 0.001;
  input.injection.total_time_s = 100.0;
  input.injection.dt_s = 10.0;
  input.fracture_height_m = 20.0;
  input.initial_width_m = 0.0;
  input.plane_strain_modulus_Pa = 25.0e9;
  input.fluid_viscosity_Pa_s = 0.003;
  return input;
}

}  // namespace

TEST_CASE("LeakoffModel none preserves cumulative volume with zero increment") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::None;

  const auto result = lss::lot::compute_leakoff_step(input, state(0.0, 10.0, 1.25));

  CHECK(result.incremental_volume_m3 == Catch::Approx(0.0));
  CHECK(result.cumulative_volume_m3 == Catch::Approx(1.25));
}

TEST_CASE("LeakoffModel constant rate computes increment and cumulative volume") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::ConstantRate;
  input.constant_rate_m3_s = 0.002;

  const auto result = lss::lot::compute_leakoff_step(input, state(0.0, 20.0, 0.5));

  CHECK(result.incremental_volume_m3 == Catch::Approx(0.04));
  CHECK(result.cumulative_volume_m3 == Catch::Approx(0.54));
}

TEST_CASE("LeakoffModel constant rate rejects negative rate") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::ConstantRate;
  input.constant_rate_m3_s = -1.0e-6;

  CHECK_THROWS_AS(lss::lot::compute_leakoff_step(input, state()), std::invalid_argument);
}

TEST_CASE("LeakoffModel Carter is non-negative and monotonic") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::Carter;
  input.coefficient_m_sqrt_s = 1.0e-6;
  input.area_m2 = 100.0;

  const auto first = lss::lot::compute_leakoff_step(input, state(0.0, 10.0, 0.0));
  const auto second =
      lss::lot::compute_leakoff_step(input, state(10.0, 10.0, first.cumulative_volume_m3));

  CHECK(first.incremental_volume_m3 >= 0.0);
  CHECK(second.incremental_volume_m3 >= 0.0);
  CHECK(second.cumulative_volume_m3 >= first.cumulative_volume_m3);
}

TEST_CASE("LeakoffModel Carter rejects negative coefficient") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::Carter;
  input.coefficient_m_sqrt_s = -1.0e-6;
  input.area_m2 = 100.0;

  CHECK_THROWS_AS(lss::lot::compute_leakoff_step(input, state()), std::invalid_argument);
}

TEST_CASE("LeakoffModel rejects non-positive dt") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::None;

  CHECK_THROWS_AS(lss::lot::compute_leakoff_step(input, state(0.0, 0.0, 0.0)),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::lot::compute_leakoff_step(input, state(0.0, -1.0, 0.0)),
                  std::invalid_argument);
}

TEST_CASE("LeakoffModel rejects NaN and infinity") {
  lss::lot::LeakoffInput input;
  input.model = lss::lot::LeakoffModel::Carter;
  input.coefficient_m_sqrt_s = std::numeric_limits<double>::quiet_NaN();
  input.area_m2 = 100.0;
  CHECK_THROWS_AS(lss::lot::compute_leakoff_step(input, state()), std::invalid_argument);

  input.coefficient_m_sqrt_s = 1.0e-6;
  input.area_m2 = std::numeric_limits<double>::infinity();
  CHECK_THROWS_AS(lss::lot::compute_leakoff_step(input, state()), std::invalid_argument);
}

TEST_CASE("PknModel integration keeps no-leakoff case closed") {
  const auto result = lss::lot::PknModel{}.simulate(pkn_input());

  REQUIRE_FALSE(result.leakoff_volume_series_m3.empty());
  for (const double leakoff : result.leakoff_volume_series_m3) {
    CHECK(leakoff == Catch::Approx(0.0));
  }
}

TEST_CASE("PknModel integration accumulates structured leakoff") {
  auto input = pkn_input();
  input.leakoff.enabled = true;
  input.leakoff.model = lss::lot::LeakoffModel::Carter;
  input.leakoff_coefficient_m_sqrt_s = 1.0e-6;

  const auto result = lss::lot::PknModel{}.simulate(input);

  REQUIRE_FALSE(result.leakoff_volume_series_m3.empty());
  CHECK(result.leakoff_volume_m3 > 0.0);
  for (std::size_t i = 1; i < result.leakoff_volume_series_m3.size(); ++i) {
    CHECK(result.leakoff_volume_series_m3[i] >= result.leakoff_volume_series_m3[i - 1]);
  }
}
