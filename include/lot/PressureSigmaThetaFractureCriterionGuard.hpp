#pragma once

#include <string>
#include <vector>

#include "lot/SigmaThetaInitialStateGuard.hpp"

namespace lss::lot {

enum class FractureCriterionStatus {
  Ready,
  BlockedSigmaThetaGuardNotReady,
  BlockedPressureSemanticsUnknown,
  BlockedSignConventionUnknown,
  BlockedReferenceFrameMismatch,
  BlockedInvalidTensileStrength,
  BlockedInvalidSigmaTheta,
  BlockedInvalidPressure,
  NotInitiated,
  Initiated,
};

struct PressureSigmaThetaCriterionInput {
  bool sigma_theta_guard_ready = false;

  double sigma_theta_current_compression_positive_Pa = 0.0;
  double tensile_strength_Pa = 0.0;

  bool use_threshold_pressure_form = false;
  double wellbore_pressure_Pa = 0.0;
  double fracture_threshold_pressure_Pa = 0.0;

  PressureSemantics pressure_semantics = PressureSemantics::Unknown;
  SigmaThetaReferenceFrame sigma_theta_reference_frame =
      SigmaThetaReferenceFrame::Unknown;
  SigmaThetaSignConvention sigma_theta_sign_convention =
      SigmaThetaSignConvention::Unknown;
};

struct PressureSigmaThetaCriterionResult {
  FractureCriterionStatus status =
      FractureCriterionStatus::BlockedSigmaThetaGuardNotReady;
  bool criterion_ready = false;
  bool fracture_initiated = false;
  double tensile_condition_Pa = 0.0;
  double fracture_margin_Pa = 0.0;
  std::vector<std::string> blocking_reasons;
};

[[nodiscard]] const char* to_string(FractureCriterionStatus status);

[[nodiscard]] PressureSigmaThetaCriterionResult
evaluate_pressure_sigma_theta_fracture_criterion(
    const PressureSigmaThetaCriterionInput& input);

}  // namespace lss::lot
