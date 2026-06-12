#include "lot/FractureGateRuntimeWiring.hpp"

#include <exception>

namespace lss::lot {
namespace {

void append_reasons(std::vector<std::string>& target,
                    const std::vector<std::string>& source) {
  target.insert(target.end(), source.begin(), source.end());
}

}  // namespace

const char* to_string(const FractureGateStatus status) {
  switch (status) {
    case FractureGateStatus::NotEvaluated:
      return "FRACTURE_GATE_NOT_EVALUATED";
    case FractureGateStatus::BlockedSigmaThetaInitialState:
      return "FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE";
    case FractureGateStatus::BlockedPressureSigmaThetaCriterion:
      return "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_CRITERION";
    case FractureGateStatus::ReadyNotReached:
      return "FRACTURE_GATE_READY_NOT_REACHED";
    case FractureGateStatus::Reached:
      return "FRACTURE_GATE_REACHED";
  }
  return "FRACTURE_GATE_UNKNOWN_STATUS";
}

const char* to_string(const FractureDispatchStatus status) {
  switch (status) {
    case FractureDispatchStatus::NotAllowed:
      return "FRACTURE_DISPATCH_NOT_ALLOWED";
    case FractureDispatchStatus::NotExecuted:
      return "FRACTURE_DISPATCH_NOT_EXECUTED";
    case FractureDispatchStatus::PknEligible:
      return "FRACTURE_DISPATCH_PKN_ELIGIBLE";
    case FractureDispatchStatus::PennyDiagnosticEligible:
      return "FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE";
  }
  return "FRACTURE_DISPATCH_UNKNOWN_STATUS";
}

FractureGateRuntimeResult evaluate_fracture_gate_runtime(
    const FractureGateRuntimeInput& input) {
  FractureGateRuntimeResult result;

  FractureModelSelectionResult selection;
  try {
    selection = select_fracture_model(input.model_selection);
  } catch (const std::exception& error) {
    result.gate_status = FractureGateStatus::NotEvaluated;
    result.dispatch_status = FractureDispatchStatus::NotAllowed;
    result.blocking_reasons.emplace_back(error.what());
    return result;
  }

  result.selected_fracture_model = selection.canonical_name;

  const auto sigma_theta_guard =
      validate_sigma_theta_initial_state(input.sigma_theta_initial_state);
  if (!sigma_theta_guard.gate_ready) {
    result.gate_status = FractureGateStatus::BlockedSigmaThetaInitialState;
    result.dispatch_status = FractureDispatchStatus::NotAllowed;
    append_reasons(result.blocking_reasons,
                   sigma_theta_guard.blocking_reasons);
    return result;
  }

  auto criterion_input = input.pressure_sigma_theta_criterion;
  criterion_input.sigma_theta_guard_ready = sigma_theta_guard.gate_ready;

  const auto criterion =
      evaluate_pressure_sigma_theta_fracture_criterion(criterion_input);
  result.fracture_initiated = criterion.fracture_initiated;
  result.fracture_margin_Pa = criterion.fracture_margin_Pa;

  if (!criterion.criterion_ready) {
    result.gate_status =
        FractureGateStatus::BlockedPressureSigmaThetaCriterion;
    result.dispatch_status = FractureDispatchStatus::NotAllowed;
    append_reasons(result.blocking_reasons, criterion.blocking_reasons);
    return result;
  }

  if (!criterion.fracture_initiated) {
    result.gate_status = FractureGateStatus::ReadyNotReached;
    result.dispatch_status = FractureDispatchStatus::NotExecuted;
    return result;
  }

  result.gate_status = FractureGateStatus::Reached;
  result.dispatch_status =
      selection.kind == FractureModelKind::Pkn
          ? FractureDispatchStatus::PknEligible
          : FractureDispatchStatus::PennyDiagnosticEligible;
  return result;
}

}  // namespace lss::lot
