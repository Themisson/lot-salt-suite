#include <algorithm>
#include <cmath>
#include <iterator>
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
  REQUIRE(result.time_series_s.size() == result.initial_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() == result.wellbore_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_delta_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_effective_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_injected_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_fracture_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_leakoff_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiation_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiation_sigma_theta_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiation_margin_series_Pa.size());
  REQUIRE(result.time_series_s.size() == result.fracture_initiated_series.size());

  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    CHECK(std::isfinite(result.time_series_s[i]));
    CHECK(std::isfinite(result.injected_volume_series_m3[i]));
    CHECK(std::isfinite(result.fracture_length_series_m[i]));
    CHECK(std::isfinite(result.fracture_width_series_m[i]));
    CHECK(std::isfinite(result.net_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.leakoff_volume_series_m3[i]));
    CHECK(std::isfinite(result.fracture_volume_series_m3[i]));
    CHECK(std::isfinite(result.initial_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.wellbore_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.balance_delta_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.balance_effective_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.balance_injected_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.balance_fracture_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.balance_leakoff_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.fracture_initiation_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.fracture_initiation_sigma_theta_series_Pa[i]));
    CHECK(std::isfinite(result.fracture_initiation_margin_series_Pa[i]));
    CHECK(result.injected_volume_series_m3[i] >= 0.0);
    CHECK(result.fracture_length_series_m[i] >= 0.0);
    CHECK(result.fracture_width_series_m[i] >= 0.0);
    CHECK(result.net_pressure_series_Pa[i] >= 0.0);
    CHECK(result.leakoff_volume_series_m3[i] >= 0.0);
    CHECK(result.fracture_volume_series_m3[i] >= 0.0);
    CHECK(result.initial_pressure_series_Pa[i] >= 0.0);
    CHECK(result.wellbore_pressure_series_Pa[i] >= 0.0);
  }
}

lss::lot::PknInput sigma_theta_input(double sigma_theta_Pa) {
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 1.0e12;
  input.fracture_initiation =
      lss::lot::FractureInitiationCriterion::SigmaThetaStatic;
  input.sigma_theta_fracture.enabled = true;
  input.sigma_theta_fracture.layer_id = "legacy_layer_16";
  input.sigma_theta_fracture.influence_depth_m = 4374.0;
  input.sigma_theta_fracture.sigma_theta_compression_positive_Pa =
      sigma_theta_Pa;
  input.sigma_theta_fracture.source = "diagnostic_static";
  input.sigma_theta_fracture.pressure_source = "wellbore_pressure_Pa";
  input.sigma_theta_fracture.comparison = "legacy_algebra";
  input.sigma_theta_fracture.mapping_status = "STATIC_FROM_LEGACY_AUDIT";
  return input;
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
  CHECK(first.initial_pressure_series_Pa == second.initial_pressure_series_Pa);
  CHECK(first.leakoff_volume_series_m3 == second.leakoff_volume_series_m3);
  CHECK(first.fracture_volume_series_m3 == second.fracture_volume_series_m3);
  CHECK(first.wellbore_pressure_series_Pa == second.wellbore_pressure_series_Pa);
}

TEST_CASE("Volumetric balance pressure model increases pressure with injection") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 1.0e12;

  const auto result = model.simulate(input);

  check_finite_non_negative_series(result);
  CHECK(result.pressure_model == "volumetric_balance");
  CHECK(result.wellbore_pressure_Pa > 0.0);
  CHECK(is_monotonic_non_decreasing(result.wellbore_pressure_series_Pa));
  CHECK(result.balance_injected_volume_increment_m3 > 0.0);
  CHECK(result.balance_fracture_volume_increment_m3 == Catch::Approx(0.0));
}

TEST_CASE("Volumetric balance leaves fracture sinks inactive without breakdown pressure") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 0.0;

  const auto result = model.simulate(input);

  check_finite_non_negative_series(result);
  CHECK(result.fracture_volume_m3 > 0.0);
  CHECK(result.balance_fracture_volume_increment_m3 == Catch::Approx(0.0));
  for (const double increment : result.balance_fracture_volume_increment_series_m3) {
    CHECK(increment == Catch::Approx(0.0));
  }
}

TEST_CASE("Volumetric balance consumes fracture volume on threshold crossing step") {
  const lss::lot::PknModel model;
  auto closed_input = synthetic_input();
  closed_input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  closed_input.annular_volume_m3 = 10.0;
  closed_input.fluid_compressibility_per_Pa = 1.0e-9;
  closed_input.breakdown.pressure_Pa = 1.0e12;

  auto opened_input = closed_input;
  opened_input.breakdown.pressure_Pa = 1.0;

  const auto closed_result = model.simulate(closed_input);
  const auto opened_result = model.simulate(opened_input);

  check_finite_non_negative_series(opened_result);
  CHECK(opened_result.balance_fracture_volume_increment_m3 > 0.0);
  CHECK(opened_result.wellbore_pressure_Pa < closed_result.wellbore_pressure_Pa);
  CHECK(opened_result.balance_effective_volume_increment_m3 <=
        opened_result.balance_injected_volume_increment_m3);
}

TEST_CASE("Sigma theta static criterion opens when wellbore pressure exceeds sigma theta") {
  const lss::lot::PknModel model;
  auto input = sigma_theta_input(5.0e5);

  const auto result = model.simulate(input);

  check_finite_non_negative_series(result);
  CHECK(result.fracture_initiated);
  CHECK(result.fracture_initiation_type == "sigma_theta_static");
  CHECK(result.fracture_initiation_layer_id == "legacy_layer_16");
  CHECK(result.fracture_initiation_depth_m == Catch::Approx(4374.0));
  CHECK(result.fracture_initiation_sigma_theta_Pa == Catch::Approx(5.0e5));
  CHECK(result.fracture_initiation_pressure_Pa > 5.0e5);
  CHECK(result.fracture_initiation_margin_Pa ==
        Catch::Approx(result.fracture_initiation_pressure_Pa - 5.0e5));
  CHECK(result.balance_fracture_volume_increment_m3 > 0.0);
}

TEST_CASE("Sigma theta static criterion remains closed below sigma theta") {
  const lss::lot::PknModel model;
  auto input = sigma_theta_input(1.0e12);

  const auto result = model.simulate(input);

  check_finite_non_negative_series(result);
  CHECK_FALSE(result.fracture_initiated);
  CHECK(result.fracture_initiation_type == "sigma_theta_static");
  CHECK(result.fracture_initiation_pressure_Pa == Catch::Approx(0.0));
  CHECK(result.fracture_initiation_sigma_theta_Pa == Catch::Approx(0.0));
  CHECK(result.balance_fracture_volume_increment_m3 == Catch::Approx(0.0));
}

TEST_CASE("Sigma theta static criterion uses wellbore pressure") {
  const lss::lot::PknModel model;
  auto input = sigma_theta_input(1.5e6);
  input.initial_pressure_Pa = 1.0e6;
  input.injection.total_time_s = 10.0;

  const auto result = model.simulate(input);

  REQUIRE(result.fracture_initiated);
  CHECK(result.fracture_initiation_pressure_Pa == Catch::Approx(2.0e6));
  CHECK(result.fracture_initiation_margin_Pa == Catch::Approx(5.0e5));
  CHECK(result.net_pressure_series_Pa.front() !=
        Catch::Approx(result.fracture_initiation_pressure_Pa));
}

TEST_CASE("Sigma theta static criterion is opt-in") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 0.0;
  input.sigma_theta_fracture.enabled = true;
  input.sigma_theta_fracture.sigma_theta_compression_positive_Pa = 1.0;

  const auto result = model.simulate(input);

  CHECK_FALSE(result.fracture_initiated);
  CHECK(result.fracture_initiation_type == "constant_pressure");
  CHECK(result.balance_fracture_volume_increment_m3 == Catch::Approx(0.0));
}

TEST_CASE("Constant pressure criterion remains supported") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 1.0;

  const auto result = model.simulate(input);

  CHECK(result.fracture_initiated);
  CHECK(result.fracture_initiation_type == "constant_pressure");
  CHECK(result.fracture_initiation_sigma_theta_Pa == Catch::Approx(0.0));
  CHECK(result.balance_fracture_volume_increment_m3 > 0.0);
}

TEST_CASE("pkn_direct behavior is preserved with sigma theta input present") {
  const lss::lot::PknModel model;
  auto direct = synthetic_input();
  auto with_sigma = direct;
  with_sigma.fracture_initiation =
      lss::lot::FractureInitiationCriterion::SigmaThetaStatic;
  with_sigma.sigma_theta_fracture.enabled = true;
  with_sigma.sigma_theta_fracture.layer_id = "legacy_layer_16";
  with_sigma.sigma_theta_fracture.influence_depth_m = 4374.0;
  with_sigma.sigma_theta_fracture.sigma_theta_compression_positive_Pa = 5.0e5;
  with_sigma.sigma_theta_fracture.source = "diagnostic_static";
  with_sigma.sigma_theta_fracture.pressure_source = "wellbore_pressure_Pa";
  with_sigma.sigma_theta_fracture.comparison = "legacy_algebra";

  const auto direct_result = model.simulate(direct);
  const auto sigma_result = model.simulate(with_sigma);

  CHECK(sigma_result.pressure_model == "pkn_direct");
  CHECK(sigma_result.injected_volume_series_m3 ==
        direct_result.injected_volume_series_m3);
  CHECK(sigma_result.net_pressure_series_Pa == direct_result.net_pressure_series_Pa);
  CHECK(sigma_result.fracture_volume_series_m3 ==
        direct_result.fracture_volume_series_m3);
}

TEST_CASE("Initial pressure shifts volumetric wellbore pressure") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.initial_pressure_Pa = 13.0e6;
  input.breakdown.pressure_Pa = 1.0e12;

  const auto result = model.simulate(input);

  REQUIRE_FALSE(result.wellbore_pressure_series_Pa.empty());
  CHECK(result.initial_pressure_Pa == Catch::Approx(13.0e6));
  CHECK(result.initial_pressure_series_Pa.front() == Catch::Approx(13.0e6));
  CHECK(result.wellbore_pressure_series_Pa.front() == Catch::Approx(13.0e6));
  CHECK(result.wellbore_pressure_Pa > 13.0e6);
}

TEST_CASE("Schedule phases preserve single phase injection volume") {
  const lss::lot::PknModel model;
  auto legacy = synthetic_input();
  auto phased = synthetic_input();
  phased.injection.phases.push_back({"injection", 100.0, 0.001});

  const auto legacy_result = model.simulate(legacy);
  const auto phased_result = model.simulate(phased);

  CHECK(phased_result.time_s == Catch::Approx(legacy_result.time_s));
  CHECK(phased_result.injected_volume_m3 ==
        Catch::Approx(legacy_result.injected_volume_m3));
  CHECK(phased_result.injected_volume_series_m3 ==
        legacy_result.injected_volume_series_m3);
}

TEST_CASE("Schedule phases keep injected volume constant during shutin") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.injection.total_time_s = 130.0;
  input.injection.phases.push_back({"injection", 100.0, 0.001});
  input.injection.phases.push_back({"shutin", 30.0, 0.0});

  const auto result = model.simulate(input);

  REQUIRE(result.time_series_s.size() >= 2);
  CHECK(result.time_s == Catch::Approx(130.0));
  CHECK(result.injected_volume_m3 == Catch::Approx(0.1));
  CHECK(result.injected_volume_series_m3.back() ==
        Catch::Approx(result.injected_volume_series_m3[result.injected_volume_series_m3.size() - 2]));
}

TEST_CASE("Shutin pressure does not increase without leakoff") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 1.0e12;
  input.injection.total_time_s = 130.0;
  input.injection.phases.push_back({"injection", 100.0, 0.001});
  input.injection.phases.push_back({"shutin", 30.0, 0.0});

  const auto result = model.simulate(input);

  REQUIRE(result.time_series_s.size() >= 2);
  CHECK(result.wellbore_pressure_series_Pa.back() ==
        Catch::Approx(result.wellbore_pressure_series_Pa[result.wellbore_pressure_series_Pa.size() - 2]));
}

TEST_CASE("Shutin pressure decreases during leakoff") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  input.annular_volume_m3 = 10.0;
  input.fluid_compressibility_per_Pa = 1.0e-9;
  input.breakdown.pressure_Pa = 1.0;
  input.leakoff.enabled = true;
  input.leakoff.model = lss::lot::LeakoffModel::ConstantRate;
  input.leakoff.constant_rate_m3_s = 1.0e-4;
  input.injection.total_time_s = 130.0;
  input.injection.phases.push_back({"injection", 100.0, 0.001});
  input.injection.phases.push_back({"shutin", 30.0, 0.0});

  const auto result = model.simulate(input);

  REQUIRE(result.time_series_s.size() >= 2);
  const auto shutin_start = std::find(result.time_series_s.begin(),
                                      result.time_series_s.end(), 100.0);
  REQUIRE(shutin_start != result.time_series_s.end());
  const auto shutin_index =
      static_cast<std::size_t>(std::distance(result.time_series_s.begin(), shutin_start));
  CHECK(result.balance_leakoff_volume_increment_series_m3.back() > 0.0);
  CHECK(result.wellbore_pressure_series_Pa.back() <
        result.wellbore_pressure_series_Pa[shutin_index]);
}

TEST_CASE("Volumetric balance responds to annular volume and compressibility") {
  const lss::lot::PknModel model;
  auto smaller_annulus = synthetic_input();
  smaller_annulus.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  smaller_annulus.annular_volume_m3 = 5.0;
  smaller_annulus.fluid_compressibility_per_Pa = 1.0e-9;
  smaller_annulus.breakdown.pressure_Pa = 1.0e12;

  auto larger_annulus = smaller_annulus;
  larger_annulus.annular_volume_m3 = 10.0;

  auto higher_compressibility = smaller_annulus;
  higher_compressibility.fluid_compressibility_per_Pa = 2.0e-9;

  CHECK(model.simulate(smaller_annulus).wellbore_pressure_Pa >
        model.simulate(larger_annulus).wellbore_pressure_Pa);
  CHECK(model.simulate(smaller_annulus).wellbore_pressure_Pa >
        model.simulate(higher_compressibility).wellbore_pressure_Pa);
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

  auto bad_initial_pressure = synthetic_input();
  bad_initial_pressure.initial_pressure_Pa = -1.0;
  CHECK_THROWS_AS(model.simulate(bad_initial_pressure), std::invalid_argument);

  auto bad_phase_rate = synthetic_input();
  bad_phase_rate.injection.phases.push_back({"shutin", 10.0, -1.0});
  CHECK_THROWS_AS(model.simulate(bad_phase_rate), std::invalid_argument);

  auto bad_balance_volume = synthetic_input();
  bad_balance_volume.pressure_model = lss::lot::PknPressureModel::VolumetricBalance;
  bad_balance_volume.annular_volume_m3 = 0.0;
  bad_balance_volume.fluid_compressibility_per_Pa = 1.0e-9;
  CHECK_THROWS_AS(model.simulate(bad_balance_volume), std::invalid_argument);

  auto bad_balance_compressibility = synthetic_input();
  bad_balance_compressibility.pressure_model =
      lss::lot::PknPressureModel::VolumetricBalance;
  bad_balance_compressibility.annular_volume_m3 = 1.0;
  bad_balance_compressibility.fluid_compressibility_per_Pa = 0.0;
  CHECK_THROWS_AS(model.simulate(bad_balance_compressibility),
                  std::invalid_argument);
}
