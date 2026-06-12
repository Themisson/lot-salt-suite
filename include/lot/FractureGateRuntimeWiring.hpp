#pragma once

#include <string>
#include <vector>

#include "lot/FractureModelSelector.hpp"
#include "lot/PressureSigmaThetaFractureCriterionGuard.hpp"
#include "lot/SigmaThetaInitialStateGuard.hpp"

namespace lss::lot {

enum class FractureGateStatus {
  NotEvaluated,
  BlockedSigmaThetaInitialState,
  BlockedPressureSigmaThetaCriterion,
  ReadyNotReached,
  Reached,
};

enum class FractureDispatchStatus {
  NotAllowed,
  NotExecuted,
  PknEligible,
  PennyDiagnosticEligible,
};

struct FractureGateRuntimeInput {
  FractureModelSelectionInput model_selection;
  SigmaThetaInitialStateInput sigma_theta_initial_state;
  PressureSigmaThetaCriterionInput pressure_sigma_theta_criterion;
};

struct FractureGateRuntimeResult {
  FractureGateStatus gate_status = FractureGateStatus::NotEvaluated;
  FractureDispatchStatus dispatch_status =
      FractureDispatchStatus::NotAllowed;
  std::string selected_fracture_model;
  bool fracture_initiated = false;
  double fracture_margin_Pa = 0.0;
  std::vector<std::string> blocking_reasons;
};

[[nodiscard]] const char* to_string(FractureGateStatus status);

[[nodiscard]] const char* to_string(FractureDispatchStatus status);

[[nodiscard]] FractureGateRuntimeResult evaluate_fracture_gate_runtime(
    const FractureGateRuntimeInput& input);

}  // namespace lss::lot
