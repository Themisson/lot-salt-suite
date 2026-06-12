#include "lot/SigmaThetaInitialStateGuard.hpp"

#include <cmath>

namespace lss::lot {

namespace {

constexpr const char* kReady = "SIGMATHETA_INITIAL_STATE_READY";
constexpr const char* kMissing =
    "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA";
constexpr const char* kInvalid =
    "FRACTURE_GATE_BLOCKED_INVALID_INITIAL_SIGMATHETA";
constexpr const char* kUnknownSource =
    "FRACTURE_GATE_BLOCKED_UNKNOWN_SOURCE";
constexpr const char* kWrongStateTime =
    "FRACTURE_GATE_BLOCKED_WRONG_STATE_TIME";
constexpr const char* kUnknownReferenceFrame =
    "FRACTURE_GATE_BLOCKED_UNKNOWN_REFERENCE_FRAME";
constexpr const char* kUnknownSignConvention =
    "FRACTURE_GATE_BLOCKED_UNKNOWN_SIGN_CONVENTION";
constexpr const char* kUnknownPressureSemantics =
    "FRACTURE_GATE_BLOCKED_UNKNOWN_PRESSURE_SEMANTICS";
constexpr const char* kPressureSigmaThetaMismatch =
    "FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH";

void add_reason(SigmaThetaInitialStateGuardResult& result,
                const char* reason) {
  if (result.status.empty()) {
    result.status = reason;
  }
  result.blocking_reasons.emplace_back(reason);
}

}  // namespace

bool is_pressure_sigma_theta_compatible(
    const PressureSemantics pressure_semantics,
    const SigmaThetaReferenceFrame sigma_theta_reference_frame) {
  if (pressure_semantics == PressureSemantics::Unknown ||
      sigma_theta_reference_frame == SigmaThetaReferenceFrame::Unknown) {
    return false;
  }

  if (pressure_semantics == PressureSemantics::WellborePressureAbsolute) {
    return sigma_theta_reference_frame == SigmaThetaReferenceFrame::TotalStress ||
           sigma_theta_reference_frame ==
               SigmaThetaReferenceFrame::EffectiveStress;
  }

  if (pressure_semantics == PressureSemantics::PressureIncrement) {
    return sigma_theta_reference_frame ==
           SigmaThetaReferenceFrame::IncrementalStress;
  }

  if (pressure_semantics == PressureSemantics::NetPressure) {
    return sigma_theta_reference_frame ==
           SigmaThetaReferenceFrame::EffectiveStress;
  }

  return false;
}

SigmaThetaInitialStateGuardResult validate_sigma_theta_initial_state(
    const SigmaThetaInitialStateInput& input) {
  SigmaThetaInitialStateGuardResult result;

  if (!input.sigma_theta_initialized ||
      !input.sigma_theta_initial_state_valid) {
    add_reason(result, kMissing);
  }

  if (!std::isfinite(input.sigma_theta_initial_compression_positive_Pa) ||
      input.sigma_theta_initial_compression_positive_Pa <= 0.0) {
    add_reason(result, kInvalid);
  }

  if (input.sigma_theta_source == SigmaThetaSource::Unknown) {
    add_reason(result, kUnknownSource);
  }

  if (input.sigma_theta_state_time !=
      SigmaThetaStateTime::AfterDrillingBeforeLot) {
    add_reason(result, kWrongStateTime);
  }

  if (input.sigma_theta_reference_frame ==
      SigmaThetaReferenceFrame::Unknown) {
    add_reason(result, kUnknownReferenceFrame);
  }

  if (input.sigma_theta_sign_convention ==
      SigmaThetaSignConvention::Unknown) {
    add_reason(result, kUnknownSignConvention);
  }

  if (input.pressure_semantics == PressureSemantics::Unknown) {
    add_reason(result, kUnknownPressureSemantics);
  }

  if (input.pressure_semantics != PressureSemantics::Unknown &&
      input.sigma_theta_reference_frame != SigmaThetaReferenceFrame::Unknown &&
      !is_pressure_sigma_theta_compatible(input.pressure_semantics,
                                          input.sigma_theta_reference_frame)) {
    add_reason(result, kPressureSigmaThetaMismatch);
  }

  result.gate_ready = result.blocking_reasons.empty();
  if (result.gate_ready) {
    result.status = kReady;
  }

  return result;
}

}  // namespace lss::lot
