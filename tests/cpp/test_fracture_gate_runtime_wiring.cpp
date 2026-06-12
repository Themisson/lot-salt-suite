#include <algorithm>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/FractureGateRuntimeWiring.hpp"

namespace {

lss::lot::SigmaThetaInitialStateInput valid_sigma_theta_initial_state() {
  lss::lot::SigmaThetaInitialStateInput input;
  input.sigma_theta_initialized = true;
  input.sigma_theta_initial_state_valid = true;
  input.sigma_theta_initial_compression_positive_Pa = 5.0e6;
  input.sigma_theta_source = lss::lot::SigmaThetaSource::SyntheticFixture;
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

lss::lot::PressureSigmaThetaCriterionInput criterion_not_initiated() {
  lss::lot::PressureSigmaThetaCriterionInput input;
  input.sigma_theta_guard_ready = false;
  input.sigma_theta_current_compression_positive_Pa = 5.0e6;
  input.tensile_strength_Pa = 1.0e6;
  input.use_threshold_pressure_form = true;
  input.wellbore_pressure_Pa = 10.0e6;
  input.fracture_threshold_pressure_Pa = 11.0e6;
  input.pressure_semantics =
      lss::lot::PressureSemantics::WellborePressureAbsolute;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::CompressionPositive;
  return input;
}

lss::lot::PressureSigmaThetaCriterionInput criterion_initiated() {
  auto input = criterion_not_initiated();
  input.wellbore_pressure_Pa = 12.0e6;
  return input;
}

lss::lot::FractureGateRuntimeInput valid_runtime_input() {
  lss::lot::FractureGateRuntimeInput input;
  input.sigma_theta_initial_state = valid_sigma_theta_initial_state();
  input.pressure_sigma_theta_criterion = criterion_not_initiated();
  return input;
}

bool has_reason(const lss::lot::FractureGateRuntimeResult& result,
                const std::string& reason) {
  return std::any_of(result.blocking_reasons.begin(),
                     result.blocking_reasons.end(),
                     [&](const std::string& item) {
                       return item.find(reason) != std::string::npos;
                     });
}

}  // namespace

TEST_CASE("FractureGateRuntimeWiring covers missing_model_defaults_pkn_not_reached") {
  const auto result =
      lss::lot::evaluate_fracture_gate_runtime(valid_runtime_input());

  CHECK(result.selected_fracture_model == "PKN");
  CHECK(result.gate_status == lss::lot::FractureGateStatus::ReadyNotReached);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotExecuted);
  CHECK_FALSE(result.fracture_initiated);
}

TEST_CASE("FractureGateRuntimeWiring covers explicit_pkn_initiated_dispatch_eligible") {
  auto input = valid_runtime_input();
  input.model_selection.has_fracture_model_field = true;
  input.model_selection.fracture_model_value = "PKN";
  input.pressure_sigma_theta_criterion = criterion_initiated();

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.selected_fracture_model == "PKN");
  CHECK(result.gate_status == lss::lot::FractureGateStatus::Reached);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PknEligible);
  CHECK(result.fracture_initiated);
}

TEST_CASE("FractureGateRuntimeWiring covers explicit_penny_initiated_diagnostic_eligible") {
  auto input = valid_runtime_input();
  input.model_selection.has_fracture_model_field = true;
  input.model_selection.fracture_model_value = "PENNY_SHAPED";
  input.pressure_sigma_theta_criterion = criterion_initiated();

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.selected_fracture_model == "PENNY_SHAPED");
  CHECK(result.gate_status == lss::lot::FractureGateStatus::Reached);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PennyDiagnosticEligible);
  CHECK(result.fracture_initiated);
}

TEST_CASE("FractureGateRuntimeWiring covers sigmatheta_guard_blocks_dispatch") {
  auto input = valid_runtime_input();
  input.sigma_theta_initial_state.sigma_theta_initialized = false;

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.gate_status ==
        lss::lot::FractureGateStatus::BlockedSigmaThetaInitialState);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  CHECK_FALSE(result.fracture_initiated);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"));
}

TEST_CASE("FractureGateRuntimeWiring covers pressure_sigmatheta_criterion_blocks_dispatch") {
  auto input = valid_runtime_input();
  input.pressure_sigma_theta_criterion.pressure_semantics =
      lss::lot::PressureSemantics::Unknown;

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.gate_status ==
        lss::lot::FractureGateStatus::BlockedPressureSigmaThetaCriterion);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  CHECK_FALSE(result.fracture_initiated);
  CHECK(has_reason(
      result, "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN"));
}

TEST_CASE("FractureGateRuntimeWiring covers unsupported_kgd_model_blocked") {
  auto input = valid_runtime_input();
  input.model_selection.has_fracture_model_field = true;
  input.model_selection.fracture_model_value = "KGD";

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.selected_fracture_model.empty());
  CHECK(result.gate_status == lss::lot::FractureGateStatus::NotEvaluated);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  CHECK(has_reason(result, "UNSUPPORTED_FRACTURE_MODEL"));
}

TEST_CASE("FractureGateRuntimeWiring covers explicit_empty_model_blocked") {
  auto input = valid_runtime_input();
  input.model_selection.has_fracture_model_field = true;
  input.model_selection.fracture_model_value = "";

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.selected_fracture_model.empty());
  CHECK(result.gate_status == lss::lot::FractureGateStatus::NotEvaluated);
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  CHECK(has_reason(result, "EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED"));
}

TEST_CASE("FractureGateRuntimeWiring marks PENNY_SHAPED eligible but not executed") {
  auto input = valid_runtime_input();
  input.model_selection.has_fracture_model_field = true;
  input.model_selection.fracture_model_value = "penny";
  input.pressure_sigma_theta_criterion = criterion_initiated();

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.selected_fracture_model == "PENNY_SHAPED");
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PennyDiagnosticEligible);
  CHECK(result.blocking_reasons.empty());
}

TEST_CASE("FractureGateRuntimeWiring marks PKN eligible but not executed") {
  auto input = valid_runtime_input();
  input.model_selection.has_fracture_model_field = true;
  input.model_selection.fracture_model_value = "lot-pkn";
  input.pressure_sigma_theta_criterion = criterion_initiated();

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.selected_fracture_model == "PKN");
  CHECK(result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PknEligible);
  CHECK(result.blocking_reasons.empty());
}

TEST_CASE("FractureGateRuntimeWiring preserves multiple blocking reasons") {
  auto input = valid_runtime_input();
  input.sigma_theta_initial_state.sigma_theta_initialized = false;
  input.sigma_theta_initial_state.sigma_theta_initial_state_valid = false;
  input.sigma_theta_initial_state.sigma_theta_source =
      lss::lot::SigmaThetaSource::Unknown;

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.blocking_reasons.size() >= 2);
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"));
  CHECK(has_reason(result, "FRACTURE_GATE_BLOCKED_UNKNOWN_SOURCE"));
}

TEST_CASE("FractureGateRuntimeWiring propagates fracture margin") {
  auto input = valid_runtime_input();
  input.pressure_sigma_theta_criterion = criterion_initiated();

  const auto result = lss::lot::evaluate_fracture_gate_runtime(input);

  CHECK(result.fracture_margin_Pa == Catch::Approx(1.0e6));
}

TEST_CASE("FractureGateRuntimeWiring exposes canonical status strings") {
  CHECK(std::string(lss::lot::to_string(
            lss::lot::FractureGateStatus::ReadyNotReached)) ==
        "FRACTURE_GATE_READY_NOT_REACHED");
  CHECK(std::string(lss::lot::to_string(
            lss::lot::FractureDispatchStatus::PennyDiagnosticEligible)) ==
        "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE");
}
