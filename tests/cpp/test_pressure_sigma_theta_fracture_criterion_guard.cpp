#include <algorithm>
#include <limits>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PressureSigmaThetaFractureCriterionGuard.hpp"

namespace {

lss::lot::PressureSigmaThetaCriterionInput valid_input() {
  lss::lot::PressureSigmaThetaCriterionInput input;
  input.sigma_theta_guard_ready = true;
  input.sigma_theta_current_compression_positive_Pa = 5.0e6;
  input.tensile_strength_Pa = 1.0e6;
  input.pressure_semantics =
      lss::lot::PressureSemantics::WellborePressureAbsolute;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::CompressionPositive;
  return input;
}

bool has_reason(const lss::lot::PressureSigmaThetaCriterionResult& result,
                const std::string& reason) {
  return std::find(result.blocking_reasons.begin(),
                   result.blocking_reasons.end(),
                   reason) != result.blocking_reasons.end();
}

}  // namespace

TEST_CASE("PressureSigmaThetaCriterion blocks when sigma theta guard is not ready") {
  auto input = valid_input();
  input.sigma_theta_guard_ready = false;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(result.status ==
        lss::lot::FractureCriterionStatus::BlockedSigmaThetaGuardNotReady);
  CHECK(has_reason(
      result, "FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY"));
}

TEST_CASE("PressureSigmaThetaCriterion blocks unknown pressure semantics") {
  auto input = valid_input();
  input.pressure_semantics = lss::lot::PressureSemantics::Unknown;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(
      result, "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN"));
}

TEST_CASE("PressureSigmaThetaCriterion blocks unknown reference frame") {
  auto input = valid_input();
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::Unknown;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH"));
}

TEST_CASE("PressureSigmaThetaCriterion blocks unknown sign convention") {
  auto input = valid_input();
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::Unknown;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN"));
}

TEST_CASE("PressureSigmaThetaCriterion blocks non compression-positive sign convention") {
  auto input = valid_input();
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::TensionPositive;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN"));
}

TEST_CASE("PressureSigmaThetaCriterion blocks negative tensile strength") {
  auto input = valid_input();
  input.tensile_strength_Pa = -1.0;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_INVALID_TENSILE_STRENGTH"));
}

TEST_CASE("PressureSigmaThetaCriterion blocks nonfinite sigma theta") {
  for (const double value : {std::numeric_limits<double>::quiet_NaN(),
                             std::numeric_limits<double>::infinity()}) {
    auto input = valid_input();
    input.sigma_theta_current_compression_positive_Pa = value;

    const auto result =
        lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

    CHECK_FALSE(result.criterion_ready);
    CHECK(has_reason(result, "FRACTURE_CRITERION_BLOCKED_INVALID_SIGMATHETA"));
  }
}

TEST_CASE("PressureSigmaThetaCriterion reports not initiated under compression") {
  auto input = valid_input();
  input.sigma_theta_current_compression_positive_Pa = 5.0e6;
  input.tensile_strength_Pa = 1.0e6;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK(result.criterion_ready);
  CHECK_FALSE(result.fracture_initiated);
  CHECK(result.status == lss::lot::FractureCriterionStatus::NotInitiated);
  CHECK(result.tensile_condition_Pa == Catch::Approx(-5.0e6));
  CHECK(result.fracture_margin_Pa == Catch::Approx(-6.0e6));
}

TEST_CASE("PressureSigmaThetaCriterion reports initiated under tensile hoop state") {
  auto input = valid_input();
  input.sigma_theta_current_compression_positive_Pa = -2.0e6;
  input.tensile_strength_Pa = 1.0e6;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK(result.criterion_ready);
  CHECK(result.fracture_initiated);
  CHECK(result.status == lss::lot::FractureCriterionStatus::Initiated);
  CHECK(result.tensile_condition_Pa == Catch::Approx(2.0e6));
  CHECK(result.fracture_margin_Pa == Catch::Approx(1.0e6));
}

TEST_CASE("PressureSigmaThetaCriterion computes preferred margin explicitly") {
  auto input = valid_input();
  input.sigma_theta_current_compression_positive_Pa = -3.5e6;
  input.tensile_strength_Pa = 2.0e6;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK(result.tensile_condition_Pa == Catch::Approx(3.5e6));
  CHECK(result.fracture_margin_Pa == Catch::Approx(1.5e6));
}

TEST_CASE("PressureSigmaThetaCriterion threshold form reports not initiated") {
  auto input = valid_input();
  input.use_threshold_pressure_form = true;
  input.wellbore_pressure_Pa = 9.0e6;
  input.fracture_threshold_pressure_Pa = 10.0e6;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK(result.criterion_ready);
  CHECK_FALSE(result.fracture_initiated);
  CHECK(result.fracture_margin_Pa == Catch::Approx(-1.0e6));
}

TEST_CASE("PressureSigmaThetaCriterion threshold form reports initiated") {
  auto input = valid_input();
  input.use_threshold_pressure_form = true;
  input.wellbore_pressure_Pa = 11.5e6;
  input.fracture_threshold_pressure_Pa = 10.0e6;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK(result.criterion_ready);
  CHECK(result.fracture_initiated);
  CHECK(result.fracture_margin_Pa == Catch::Approx(1.5e6));
}

TEST_CASE("PressureSigmaThetaCriterion threshold form blocks invalid pressure") {
  auto input = valid_input();
  input.use_threshold_pressure_form = true;
  input.wellbore_pressure_Pa = std::numeric_limits<double>::quiet_NaN();
  input.fracture_threshold_pressure_Pa = 10.0e6;

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(result, "FRACTURE_CRITERION_BLOCKED_INVALID_PRESSURE"));
}

TEST_CASE("PressureSigmaThetaCriterion accumulates blocking reasons") {
  lss::lot::PressureSigmaThetaCriterionInput input;
  input.tensile_strength_Pa = -1.0;
  input.sigma_theta_current_compression_positive_Pa =
      std::numeric_limits<double>::quiet_NaN();

  const auto result =
      lss::lot::evaluate_pressure_sigma_theta_fracture_criterion(input);

  CHECK_FALSE(result.criterion_ready);
  CHECK(has_reason(
      result, "FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY"));
  CHECK(has_reason(
      result, "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN"));
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH"));
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN"));
  CHECK(has_reason(result,
                   "FRACTURE_CRITERION_BLOCKED_INVALID_TENSILE_STRENGTH"));
  CHECK(has_reason(result, "FRACTURE_CRITERION_BLOCKED_INVALID_SIGMATHETA"));
}
