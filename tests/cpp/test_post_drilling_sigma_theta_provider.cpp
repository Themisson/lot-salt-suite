#include <fstream>
#include <iterator>
#include <limits>
#include <string>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PostDrillingSigmaThetaProvider.hpp"
#include "lot/PressureSigmaThetaFractureCriterionGuard.hpp"

namespace {

lss::lot::PostDrillingSigmaThetaProviderInput valid_input(
    lss::lot::PostDrillingSigmaThetaSource source =
        lss::lot::PostDrillingSigmaThetaSource::ExplicitDiagnosticInput) {
  lss::lot::PostDrillingSigmaThetaProviderInput input;
  input.source = source;
  input.sigma_theta_initial_compression_positive_Pa = 5.0e6;
  input.sigma_theta_current_compression_positive_Pa = 4.5e6;
  input.far_field_stress_compression_positive_Pa = 5.0e6;
  input.wellbore_pressure_Pa = 6.0e6;
  input.tensile_strength_Pa = 0.0;
  input.physically_validated = false;
  input.legacy_equivalent = false;
  return input;
}

std::string read_text_file(const std::string& path) {
  std::ifstream in(path);
  return {std::istreambuf_iterator<char>(in),
          std::istreambuf_iterator<char>()};
}

bool contains(const std::vector<std::string>& values, const std::string& value) {
  for (const auto& item : values) {
    if (item == value) {
      return true;
    }
  }
  return false;
}

}  // namespace

struct ElasticAnalyticCase {
  const char* id;
  double far_field_stress_compression_positive_Pa;
  double wellbore_pressure_Pa;
  double tensile_strength_Pa;
  double expected_sigma_theta_initial_compression_positive_Pa;
  double expected_sigma_theta_current_compression_positive_Pa;
  double expected_tensile_condition_Pa;
  double expected_fracture_margin_Pa;
  lss::lot::FractureCriterionStatus expected_status;
  bool expected_fracture_initiated;
};

TEST_CASE("PostDrillingSigmaThetaProvider accepts explicit diagnostic input") {
  const auto result =
      lss::lot::evaluate_post_drilling_sigma_theta(valid_input());

  CHECK(result.available);
  CHECK(result.source == "EXPLICIT_DIAGNOSTIC_INPUT");
  CHECK(result.state_time == "POST_DRILLING_BEFORE_LOT");
  CHECK(result.sign_convention == "COMPRESSION_POSITIVE");
  CHECK(result.reference_frame == "WELLBORE_WALL_TOTAL_STRESS");
  CHECK_FALSE(result.physically_validated);
  CHECK_FALSE(result.legacy_equivalent);
  CHECK(contains(result.caveats, "DIAGNOSTIC_SOURCE_ONLY"));
}

TEST_CASE("PostDrillingSigmaThetaProvider accepts synthetic fixture source") {
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(
      valid_input(lss::lot::PostDrillingSigmaThetaSource::SyntheticFixture));

  CHECK(result.available);
  CHECK(result.source == "SYNTHETIC_FIXTURE");
  CHECK(contains(result.caveats, "DIAGNOSTIC_SOURCE_ONLY"));
}

TEST_CASE("PostDrillingSigmaThetaProvider marks elastic source as semi physical") {
  auto input = valid_input(
      lss::lot::PostDrillingSigmaThetaSource::ElasticInitialWellboreState);
  input.far_field_stress_compression_positive_Pa = 5.0e6;
  input.wellbore_pressure_Pa = 6.0e6;
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(input);

  CHECK(result.available);
  CHECK(result.source == "ELASTIC_INITIAL_WELLBORE_STATE");
  CHECK(result.sigma_theta_initial_compression_positive_Pa ==
        Catch::Approx(5.0e6));
  CHECK(result.sigma_theta_current_compression_positive_Pa ==
        Catch::Approx(-1.0e6));
  CHECK(result.far_field_stress_compression_positive_Pa ==
        Catch::Approx(5.0e6));
  CHECK(contains(result.caveats, "ELASTIC_INITIAL_WELLBORE_APPROXIMATION"));
  CHECK(contains(result.caveats, "ELASTIC_WELLBORE_APPROXIMATION_SIMPLIFIED"));
  CHECK(contains(result.caveats, "SEMI_PHYSICAL_ELASTIC_APPROXIMATION"));
  CHECK(contains(result.caveats, "NOT_PHYSICALLY_VALIDATED"));
  CHECK(contains(result.caveats, "NOT_LEGACY_EQUIVALENT"));
}

TEST_CASE("PostDrillingSigmaThetaProvider elastic source can remain compressive") {
  auto input = valid_input(
      lss::lot::PostDrillingSigmaThetaSource::ElasticInitialWellboreState);
  input.far_field_stress_compression_positive_Pa = 8.0e6;
  input.wellbore_pressure_Pa = 3.0e6;
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(input);

  CHECK(result.sigma_theta_initial_compression_positive_Pa ==
        Catch::Approx(8.0e6));
  CHECK(result.sigma_theta_current_compression_positive_Pa ==
        Catch::Approx(5.0e6));
}

TEST_CASE("PostDrillingSigmaThetaProvider accepts axisymmetric elastic source") {
  auto input = valid_input(
      lss::lot::PostDrillingSigmaThetaSource::AxisymmetricElasticWellboreState);
  input.far_field_stress_compression_positive_Pa = 9.0e6;
  input.wellbore_pressure_Pa = 11.0e6;
  input.tensile_strength_Pa = 1.0e6;
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(input);

  CHECK(result.available);
  CHECK(result.source == "AXISYMMETRIC_ELASTIC_WELLBORE_STATE");
  CHECK(result.sigma_theta_initial_compression_positive_Pa ==
        Catch::Approx(9.0e6));
  CHECK(result.sigma_theta_current_compression_positive_Pa ==
        Catch::Approx(-2.0e6));
  CHECK(result.tensile_strength_Pa == Catch::Approx(1.0e6));
  CHECK(contains(result.caveats,
                 "AXISYMMETRIC_ELASTIC_WELLBORE_APPROXIMATION"));
  CHECK(contains(result.caveats,
                 "AXISYMMETRIC_WALL_STRESS_DIAGNOSTIC_SOURCE"));
  CHECK(contains(result.caveats, "SEMI_PHYSICAL_ELASTIC_APPROXIMATION"));
  CHECK(contains(result.caveats, "NOT_PHYSICALLY_VALIDATED"));
  CHECK(contains(result.caveats, "NOT_LEGACY_EQUIVALENT"));
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects unknown source") {
  auto input = valid_input();
  input.source = lss::lot::PostDrillingSigmaThetaSource::Unknown;

  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects invalid initial sigma theta") {
  auto input = valid_input();
  input.sigma_theta_initial_compression_positive_Pa = 0.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider accepts tensile current sigma theta") {
  auto input = valid_input();
  input.sigma_theta_current_compression_positive_Pa = -1.0;
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(input);

  CHECK(result.sigma_theta_current_compression_positive_Pa == -1.0);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects nonfinite current sigma theta") {
  auto input = valid_input();
  input.sigma_theta_current_compression_positive_Pa =
      std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects invalid pressure values") {
  auto input = valid_input();
  input.wellbore_pressure_Pa = -1.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);

  input = valid_input();
  input.tensile_strength_Pa = -1.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects invalid elastic far field") {
  auto input = valid_input(
      lss::lot::PostDrillingSigmaThetaSource::ElasticInitialWellboreState);
  input.far_field_stress_compression_positive_Pa = 0.0;

  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);

  input = valid_input(
      lss::lot::PostDrillingSigmaThetaSource::AxisymmetricElasticWellboreState);
  input.far_field_stress_compression_positive_Pa = 0.0;

  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects physical validation flags") {
  auto input = valid_input();
  input.physically_validated = true;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);

  input = valid_input();
  input.legacy_equivalent = true;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider preserves numeric inputs") {
  const auto result =
      lss::lot::evaluate_post_drilling_sigma_theta(valid_input());

  CHECK(result.sigma_theta_initial_compression_positive_Pa == 5.0e6);
  CHECK(result.sigma_theta_current_compression_positive_Pa == 4.5e6);
  CHECK(result.far_field_stress_compression_positive_Pa == 5.0e6);
  CHECK(result.wellbore_pressure_Pa == 6.0e6);
  CHECK(result.tensile_strength_Pa == 0.0);
}

TEST_CASE("PostDrillingSigmaThetaProvider remains isolated from physical dispatch") {
  const auto header = read_text_file("include/lot/PostDrillingSigmaThetaProvider.hpp");
  const auto source = read_text_file("src/lot/PostDrillingSigmaThetaProvider.cpp");

  CHECK(header.find("PknModel") == std::string::npos);
  CHECK(header.find("PknRunner") == std::string::npos);
  CHECK(header.find("PennyShapedDiagnosticAdapter") == std::string::npos);
  CHECK(source.find("PknModel") == std::string::npos);
  CHECK(source.find("PknRunner") == std::string::npos);
  CHECK(source.find("PennyShapedDiagnosticAdapter") == std::string::npos);
}

TEST_CASE("PostDrillingSigmaThetaProvider matches elastic analytic cases") {
  const ElasticAnalyticCase cases[] = {
      {"compressive_not_reached",
       10000000.0,
       6000000.0,
       1000000.0,
       10000000.0,
       4000000.0,
       -4000000.0,
       -5000000.0,
       lss::lot::FractureCriterionStatus::NotInitiated,
       false},
      {"zero_hoop_not_reached",
       8000000.0,
       8000000.0,
       1000000.0,
       8000000.0,
       0.0,
       -0.0,
       -1000000.0,
       lss::lot::FractureCriterionStatus::NotInitiated,
       false},
      {"tension_below_strength_not_reached",
       8000000.0,
       8500000.0,
       1000000.0,
       8000000.0,
       -500000.0,
       500000.0,
       -500000.0,
       lss::lot::FractureCriterionStatus::NotInitiated,
       false},
      {"tension_above_strength_reached",
       8000000.0,
       9500000.0,
       1000000.0,
       8000000.0,
       -1500000.0,
       1500000.0,
       500000.0,
       lss::lot::FractureCriterionStatus::Initiated,
       true},
      {"exact_threshold_reached",
       8000000.0,
       9000000.0,
       1000000.0,
       8000000.0,
       -1000000.0,
       1000000.0,
       0.0,
       lss::lot::FractureCriterionStatus::Initiated,
       true},
  };

  for (const auto& analytic_case : cases) {
    INFO(analytic_case.id);
    auto input = valid_input(
        lss::lot::PostDrillingSigmaThetaSource::ElasticInitialWellboreState);
    input.far_field_stress_compression_positive_Pa =
        analytic_case.far_field_stress_compression_positive_Pa;
    input.wellbore_pressure_Pa = analytic_case.wellbore_pressure_Pa;
    input.tensile_strength_Pa = analytic_case.tensile_strength_Pa;
    input.physically_validated = false;
    input.legacy_equivalent = false;

    const auto provider_result =
        lss::lot::evaluate_post_drilling_sigma_theta(input);

    CHECK(provider_result.available);
    CHECK(provider_result.sigma_theta_initial_compression_positive_Pa ==
          Catch::Approx(
              analytic_case.expected_sigma_theta_initial_compression_positive_Pa));
    CHECK(provider_result.sigma_theta_current_compression_positive_Pa ==
          Catch::Approx(
              analytic_case.expected_sigma_theta_current_compression_positive_Pa));
    CHECK_FALSE(provider_result.physically_validated);
    CHECK_FALSE(provider_result.legacy_equivalent);
    CHECK(contains(provider_result.caveats,
                   "SEMI_PHYSICAL_ELASTIC_APPROXIMATION"));

    lss::lot::PressureSigmaThetaCriterionInput criterion_input;
    criterion_input.sigma_theta_guard_ready = true;
    criterion_input.sigma_theta_current_compression_positive_Pa =
        provider_result.sigma_theta_current_compression_positive_Pa;
    criterion_input.tensile_strength_Pa = provider_result.tensile_strength_Pa;
    criterion_input.pressure_semantics =
        lss::lot::PressureSemantics::WellborePressureAbsolute;
    criterion_input.sigma_theta_reference_frame =
        lss::lot::SigmaThetaReferenceFrame::TotalStress;
    criterion_input.sigma_theta_sign_convention =
        lss::lot::SigmaThetaSignConvention::CompressionPositive;

    const auto criterion_result =
        lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(
            criterion_input);

    CHECK(criterion_result.criterion_ready);
    CHECK(criterion_result.tensile_condition_Pa ==
          Catch::Approx(analytic_case.expected_tensile_condition_Pa));
    CHECK(criterion_result.fracture_margin_Pa ==
          Catch::Approx(analytic_case.expected_fracture_margin_Pa));
    CHECK(criterion_result.status == analytic_case.expected_status);
    CHECK(criterion_result.fracture_initiated ==
          analytic_case.expected_fracture_initiated);
  }
}

TEST_CASE("PostDrillingSigmaThetaProvider axisymmetric source matches analytic cases") {
  const ElasticAnalyticCase cases[] = {
      {"compressive_not_reached",
       10000000.0,
       6000000.0,
       1000000.0,
       10000000.0,
       4000000.0,
       -4000000.0,
       -5000000.0,
       lss::lot::FractureCriterionStatus::NotInitiated,
       false},
      {"tension_above_strength_reached",
       8000000.0,
       9500000.0,
       1000000.0,
       8000000.0,
       -1500000.0,
       1500000.0,
       500000.0,
       lss::lot::FractureCriterionStatus::Initiated,
       true},
      {"exact_threshold_reached",
       8000000.0,
       9000000.0,
       1000000.0,
       8000000.0,
       -1000000.0,
       1000000.0,
       0.0,
       lss::lot::FractureCriterionStatus::Initiated,
       true},
  };

  for (const auto& analytic_case : cases) {
    INFO(analytic_case.id);
    auto input = valid_input(
        lss::lot::PostDrillingSigmaThetaSource::
            AxisymmetricElasticWellboreState);
    input.far_field_stress_compression_positive_Pa =
        analytic_case.far_field_stress_compression_positive_Pa;
    input.wellbore_pressure_Pa = analytic_case.wellbore_pressure_Pa;
    input.tensile_strength_Pa = analytic_case.tensile_strength_Pa;

    const auto provider_result =
        lss::lot::evaluate_post_drilling_sigma_theta(input);

    CHECK(provider_result.sigma_theta_initial_compression_positive_Pa ==
          Catch::Approx(
              analytic_case.expected_sigma_theta_initial_compression_positive_Pa));
    CHECK(provider_result.sigma_theta_current_compression_positive_Pa ==
          Catch::Approx(
              analytic_case.expected_sigma_theta_current_compression_positive_Pa));
    CHECK(contains(provider_result.caveats,
                   "AXISYMMETRIC_WALL_STRESS_DIAGNOSTIC_SOURCE"));

    lss::lot::PressureSigmaThetaCriterionInput criterion_input;
    criterion_input.sigma_theta_guard_ready = true;
    criterion_input.sigma_theta_current_compression_positive_Pa =
        provider_result.sigma_theta_current_compression_positive_Pa;
    criterion_input.tensile_strength_Pa = provider_result.tensile_strength_Pa;
    criterion_input.pressure_semantics =
        lss::lot::PressureSemantics::WellborePressureAbsolute;
    criterion_input.sigma_theta_reference_frame =
        lss::lot::SigmaThetaReferenceFrame::TotalStress;
    criterion_input.sigma_theta_sign_convention =
        lss::lot::SigmaThetaSignConvention::CompressionPositive;

    const auto criterion_result =
        lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(
            criterion_input);

    CHECK(criterion_result.status == analytic_case.expected_status);
    CHECK(criterion_result.fracture_initiated ==
          analytic_case.expected_fracture_initiated);
  }
}
