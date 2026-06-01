#include <cmath>
#include <vector>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PknModel.hpp"

namespace {

lss::lot::PknInput synthetic_input() {
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

bool is_monotonic_non_decreasing(const std::vector<double>& values) {
  for (std::size_t i = 1; i < values.size(); ++i) {
    if (values[i] < values[i - 1]) {
      return false;
    }
  }
  return true;
}

void check_finite_non_negative_series(const lss::lot::PknResult& result) {
  REQUIRE(result.time_series_s.size() == result.injected_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.fracture_length_series_m.size());
  REQUIRE(result.time_series_s.size() == result.fracture_width_series_m.size());
  REQUIRE(result.time_series_s.size() == result.net_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() == result.leakoff_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.fracture_volume_series_m3.size());

  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    CHECK(std::isfinite(result.time_series_s[i]));
    CHECK(std::isfinite(result.injected_volume_series_m3[i]));
    CHECK(std::isfinite(result.fracture_length_series_m[i]));
    CHECK(std::isfinite(result.fracture_width_series_m[i]));
    CHECK(std::isfinite(result.net_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.leakoff_volume_series_m3[i]));
    CHECK(std::isfinite(result.fracture_volume_series_m3[i]));
    CHECK(result.injected_volume_series_m3[i] >= 0.0);
    CHECK(result.fracture_length_series_m[i] >= 0.0);
    CHECK(result.fracture_width_series_m[i] >= 0.0);
    CHECK(result.net_pressure_series_Pa[i] >= 0.0);
    CHECK(result.leakoff_volume_series_m3[i] >= 0.0);
    CHECK(result.fracture_volume_series_m3[i] >= 0.0);
  }
}

}  // namespace

TEST_CASE("Minimal SI PKN model returns non-negative finite values") {
  const lss::lot::PknModel model;
  const auto result = model.evaluate(synthetic_input(), 100.0);

  CHECK(result.width_m >= 0.0);
  CHECK(result.length_m >= 0.0);
  CHECK(result.volume_m3 >= 0.0);
  CHECK(result.fracture_volume_m3 >= 0.0);
  CHECK(result.injected_volume_m3 >= 0.0);
  CHECK(result.leakoff_volume_m3 >= 0.0);
  CHECK(result.net_pressure_Pa >= 0.0);
  CHECK(std::isfinite(result.width_m));
  CHECK(std::isfinite(result.length_m));
  CHECK(std::isfinite(result.volume_m3));
  CHECK(std::isfinite(result.fracture_volume_m3));
  CHECK(std::isfinite(result.injected_volume_m3));
  CHECK(std::isfinite(result.leakoff_volume_m3));
  CHECK(std::isfinite(result.net_pressure_Pa));
}

TEST_CASE("Minimal SI PKN model volume is monotonic with elapsed time") {
  const lss::lot::PknModel model;
  const auto input = synthetic_input();

  const auto early = model.evaluate(input, 10.0);
  const auto late = model.evaluate(input, 100.0);

  CHECK(late.volume_m3 >= early.volume_m3);
  CHECK(late.length_m >= early.length_m);
}

TEST_CASE("Minimal SI PKN model simulates a closed case without leakoff") {
  const lss::lot::PknModel model;
  const auto result = model.simulate(synthetic_input());

  REQUIRE_FALSE(result.time_series_s.empty());
  check_finite_non_negative_series(result);
  CHECK(is_monotonic_non_decreasing(result.injected_volume_series_m3));
  CHECK(is_monotonic_non_decreasing(result.fracture_volume_series_m3));
  CHECK(result.leakoff_volume_m3 == Catch::Approx(0.0));
  for (const double leakoff : result.leakoff_volume_series_m3) {
    CHECK(leakoff == Catch::Approx(0.0));
  }
  CHECK(result.fracture_volume_m3 == Catch::Approx(result.injected_volume_m3));
}

TEST_CASE("Minimal SI PKN model honors accommodation time") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.injection.accommodation_time_s = 30.0;

  const auto before_loading = model.evaluate(input, 20.0);
  const auto after_loading = model.evaluate(input, 100.0);

  CHECK(before_loading.injected_volume_m3 == Catch::Approx(0.0));
  CHECK(before_loading.fracture_volume_m3 == Catch::Approx(0.0));
  CHECK(before_loading.length_m == Catch::Approx(0.0));
  CHECK(after_loading.injected_volume_m3 == Catch::Approx(0.07));
  CHECK(after_loading.fracture_volume_m3 == Catch::Approx(0.07));
}

TEST_CASE("Minimal SI PKN model supports simplified leakoff") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.leakoff.enabled = true;
  input.leakoff.model = lss::lot::LeakoffModel::SyntheticConstant;
  input.leakoff_coefficient_m_sqrt_s = 1.0e-6;

  const auto result = model.simulate(input);

  check_finite_non_negative_series(result);
  CHECK(is_monotonic_non_decreasing(result.leakoff_volume_series_m3));
  CHECK(result.leakoff_volume_m3 >= 0.0);
  CHECK(result.fracture_volume_m3 <= result.injected_volume_m3);
}

TEST_CASE("Minimal SI PKN model is deterministic") {
  const lss::lot::PknModel model;
  const auto input = synthetic_input();

  const auto first = model.simulate(input);
  const auto second = model.simulate(input);

  CHECK(first.time_series_s == second.time_series_s);
  CHECK(first.injected_volume_series_m3 == second.injected_volume_series_m3);
  CHECK(first.fracture_length_series_m == second.fracture_length_series_m);
  CHECK(first.fracture_width_series_m == second.fracture_width_series_m);
  CHECK(first.net_pressure_series_Pa == second.net_pressure_series_Pa);
  CHECK(first.leakoff_volume_series_m3 == second.leakoff_volume_series_m3);
  CHECK(first.fracture_volume_series_m3 == second.fracture_volume_series_m3);
}

TEST_CASE("Minimal SI PKN model rejects invalid inputs") {
  const lss::lot::PknModel model;

  auto bad_height = synthetic_input();
  bad_height.fracture_height_m = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_height), std::invalid_argument);

  auto bad_modulus = synthetic_input();
  bad_modulus.plane_strain_modulus_Pa = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_modulus), std::invalid_argument);

  auto bad_viscosity = synthetic_input();
  bad_viscosity.fluid_viscosity_Pa_s = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_viscosity), std::invalid_argument);

  auto bad_rate = synthetic_input();
  bad_rate.injection.rate_m3_s = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_rate), std::invalid_argument);

  auto bad_dt = synthetic_input();
  bad_dt.injection.dt_s = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_dt), std::invalid_argument);

  auto bad_total = synthetic_input();
  bad_total.injection.total_time_s = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_total), std::invalid_argument);

  auto bad_dt_gt_total = synthetic_input();
  bad_dt_gt_total.injection.dt_s = 200.0;
  CHECK_THROWS_AS(model.simulate(bad_dt_gt_total), std::invalid_argument);
}
