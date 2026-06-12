#include "lot/PressureSigmaThetaFractureCriterionGuard.hpp"

#include <cmath>

namespace lss::lot {

namespace {

constexpr const char* kBlockedSigmaThetaGuardNotReady =
    "FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY";
constexpr const char* kBlockedPressureSemanticsUnknown =
    "FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN";
constexpr const char* kBlockedSignConventionUnknown =
    "FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN";
constexpr const char* kBlockedReferenceFrameMismatch =
    "FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH";
constexpr const char* kBlockedInvalidTensileStrength =
    "FRACTURE_CRITERION_BLOCKED_INVALID_TENSILE_STRENGTH";
constexpr const char* kBlockedInvalidSigmaTheta =
    "FRACTURE_CRITERION_BLOCKED_INVALID_SIGMATHETA";
constexpr const char* kBlockedInvalidPressure =
    "FRACTURE_CRITERION_BLOCKED_INVALID_PRESSURE";

void add_reason(PressureSigmaThetaCriterionResult& result,
                const char* reason,
                FractureCriterionStatus status) {
  if (result.blocking_reasons.empty()) {
    result.status = status;
  }
  result.blocking_reasons.emplace_back(reason);
}

}  // namespace

const char* to_string(const FractureCriterionStatus status) {
  switch (status) {
    case FractureCriterionStatus::Ready:
      return "FRACTURE_CRITERION_READY";
    case FractureCriterionStatus::BlockedSigmaThetaGuardNotReady:
      return kBlockedSigmaThetaGuardNotReady;
    case FractureCriterionStatus::BlockedPressureSemanticsUnknown:
      return kBlockedPressureSemanticsUnknown;
    case FractureCriterionStatus::BlockedSignConventionUnknown:
      return kBlockedSignConventionUnknown;
    case FractureCriterionStatus::BlockedReferenceFrameMismatch:
      return kBlockedReferenceFrameMismatch;
    case FractureCriterionStatus::BlockedInvalidTensileStrength:
      return kBlockedInvalidTensileStrength;
    case FractureCriterionStatus::BlockedInvalidSigmaTheta:
      return kBlockedInvalidSigmaTheta;
    case FractureCriterionStatus::BlockedInvalidPressure:
      return kBlockedInvalidPressure;
    case FractureCriterionStatus::NotInitiated:
      return "FRACTURE_CRITERION_READY_NOT_INITIATED";
    case FractureCriterionStatus::Initiated:
      return "FRACTURE_CRITERION_READY_INITIATED";
  }
  return "FRACTURE_CRITERION_UNKNOWN_STATUS";
}

PressureSigmaThetaCriterionResult
evaluate_pressure_sigma_theta_fracture_criterion(
    const PressureSigmaThetaCriterionInput& input) {
  PressureSigmaThetaCriterionResult result;

  if (!input.sigma_theta_guard_ready) {
    add_reason(result,
               kBlockedSigmaThetaGuardNotReady,
               FractureCriterionStatus::BlockedSigmaThetaGuardNotReady);
  }

  if (input.pressure_semantics == PressureSemantics::Unknown) {
    add_reason(result,
               kBlockedPressureSemanticsUnknown,
               FractureCriterionStatus::BlockedPressureSemanticsUnknown);
  }

  if (input.sigma_theta_reference_frame ==
      SigmaThetaReferenceFrame::Unknown) {
    add_reason(result,
               kBlockedReferenceFrameMismatch,
               FractureCriterionStatus::BlockedReferenceFrameMismatch);
  }

  if (input.sigma_theta_sign_convention ==
      SigmaThetaSignConvention::Unknown) {
    add_reason(result,
               kBlockedSignConventionUnknown,
               FractureCriterionStatus::BlockedSignConventionUnknown);
  } else if (input.sigma_theta_sign_convention !=
             SigmaThetaSignConvention::CompressionPositive) {
    add_reason(result,
               kBlockedSignConventionUnknown,
               FractureCriterionStatus::BlockedSignConventionUnknown);
  }

  if (input.tensile_strength_Pa < 0.0 ||
      !std::isfinite(input.tensile_strength_Pa)) {
    add_reason(result,
               kBlockedInvalidTensileStrength,
               FractureCriterionStatus::BlockedInvalidTensileStrength);
  }

  if (!std::isfinite(input.sigma_theta_current_compression_positive_Pa)) {
    add_reason(result,
               kBlockedInvalidSigmaTheta,
               FractureCriterionStatus::BlockedInvalidSigmaTheta);
  }

  if (input.use_threshold_pressure_form &&
      (!std::isfinite(input.wellbore_pressure_Pa) ||
       !std::isfinite(input.fracture_threshold_pressure_Pa))) {
    add_reason(result,
               kBlockedInvalidPressure,
               FractureCriterionStatus::BlockedInvalidPressure);
  }

  if (input.pressure_semantics != PressureSemantics::Unknown &&
      input.sigma_theta_reference_frame != SigmaThetaReferenceFrame::Unknown &&
      !is_pressure_sigma_theta_compatible(input.pressure_semantics,
                                          input.sigma_theta_reference_frame)) {
    add_reason(result,
               kBlockedReferenceFrameMismatch,
               FractureCriterionStatus::BlockedReferenceFrameMismatch);
  }

  if (!result.blocking_reasons.empty()) {
    return result;
  }

  result.criterion_ready = true;
  result.tensile_condition_Pa =
      -input.sigma_theta_current_compression_positive_Pa;

  if (input.use_threshold_pressure_form) {
    result.fracture_margin_Pa =
        input.wellbore_pressure_Pa - input.fracture_threshold_pressure_Pa;
  } else {
    result.fracture_margin_Pa =
        result.tensile_condition_Pa - input.tensile_strength_Pa;
  }

  result.fracture_initiated = result.fracture_margin_Pa >= 0.0;
  result.status = result.fracture_initiated
                      ? FractureCriterionStatus::Initiated
                      : FractureCriterionStatus::NotInitiated;
  return result;
}

}  // namespace lss::lot
