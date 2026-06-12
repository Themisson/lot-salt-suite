#include <algorithm>
#include <limits>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "lot/SigmaThetaInitialStateGuard.hpp"

namespace {

lss::lot::SigmaThetaInitialStateInput valid_input() {
  lss::lot::SigmaThetaInitialStateInput input;
  input.sigma_theta_initialized = true;
  input.sigma_theta_initial_state_valid = true;
  input.sigma_theta_initial_compression_positive_Pa = 6.6e7;
  input.sigma_theta_source =
      lss::lot::SigmaThetaSource::ElasticInitialWellboreState;
  input.sigma_theta_state_time =
      lss::lot::SigmaThetaStateTime::AfterDrillingBeforeLot;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::CompressionPositive;
  input.pressure_semantics =
      lss::lot::PressureSemantics::WellborePressureAbsolute;
  return input;
}

bool has_reason(const lss::lot::SigmaThetaInitialStateGuardResult& result,
                const std::string& reason) {
  return std::find(result.blocking_reasons.begin(),
                   result.blocking_reasons.end(),
                   reason) != result.blocking_reasons.end();
}

}  // namespace

TEST_CASE("SigmaThetaInitialStateGuard accepts a complete initial state") {
  const auto result = lss::lot::validate_sigma_theta_initial_state(valid_input());

  CHECK(result.gate_ready);
  CHECK(result.status == "SIGMATHETA_INITIAL_STATE_READY");
  CHECK(result.blocking_reasons.empty());
}

TEST_CASE("SigmaThetaInitialStateGuard blocks missing initialization") {
  auto input = valid_input();
  input.sigma_theta_initialized = false;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks invalid initial state flag") {
  auto input = valid_input();
  input.sigma_theta_initial_state_valid = false;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks unknown source") {
  auto input = valid_input();
  input.sigma_theta_source = lss::lot::SigmaThetaSource::Unknown;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_SOURCE"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks unknown state time") {
  auto input = valid_input();
  input.sigma_theta_state_time = lss::lot::SigmaThetaStateTime::Unknown;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_WRONG_STATE_TIME"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks LOT-step sigma theta") {
  auto input = valid_input();
  input.sigma_theta_state_time = lss::lot::SigmaThetaStateTime::DuringLotStep;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_WRONG_STATE_TIME"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks unknown reference frame") {
  auto input = valid_input();
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::Unknown;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_REFERENCE_FRAME"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks unknown sign convention") {
  auto input = valid_input();
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::Unknown;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_SIGN_CONVENTION"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks unknown pressure semantics") {
  auto input = valid_input();
  input.pressure_semantics = lss::lot::PressureSemantics::Unknown;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_PRESSURE_SEMANTICS"));
}

TEST_CASE("SigmaThetaInitialStateGuard blocks nonfinite sigma theta") {
  for (const double value : {std::numeric_limits<double>::quiet_NaN(),
                             std::numeric_limits<double>::infinity()}) {
    auto input = valid_input();
    input.sigma_theta_initial_compression_positive_Pa = value;

    const auto result = lss::lot::validate_sigma_theta_initial_state(input);

    CHECK_FALSE(result.gate_ready);
    CHECK(has_reason(result,
                     "FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA"));
  }
}

TEST_CASE("SigmaThetaInitialStateGuard blocks nonpositive sigma theta") {
  for (const double value : {0.0, -1.0}) {
    auto input = valid_input();
    input.sigma_theta_initial_compression_positive_Pa = value;

    const auto result = lss::lot::validate_sigma_theta_initial_state(input);

    CHECK_FALSE(result.gate_ready);
    CHECK(has_reason(result,
                     "FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA"));
  }
}

TEST_CASE("SigmaThetaInitialStateGuard blocks pressure increment against total stress") {
  auto input = valid_input();
  input.pressure_semantics = lss::lot::PressureSemantics::PressureIncrement;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result,
                   "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH"));
}

TEST_CASE("SigmaThetaInitialStateGuard accepts absolute pressure with total stress") {
  auto input = valid_input();
  input.pressure_semantics =
      lss::lot::PressureSemantics::WellborePressureAbsolute;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK(result.gate_ready);
}

TEST_CASE("SigmaThetaInitialStateGuard accepts net pressure with effective stress") {
  auto input = valid_input();
  input.pressure_semantics = lss::lot::PressureSemantics::NetPressure;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::EffectiveStress;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK(result.gate_ready);
}

TEST_CASE("SigmaThetaInitialStateGuard accumulates blocking reasons") {
  lss::lot::SigmaThetaInitialStateInput input;

  const auto result = lss::lot::validate_sigma_theta_initial_state(input);

  CHECK_FALSE(result.gate_ready);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_SOURCE"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_WRONG_STATE_TIME"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_REFERENCE_FRAME"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_SIGN_CONVENTION"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_PRESSURE_SEMANTICS"));
}
