#pragma once

#include <string>
#include <vector>

namespace lss::lot {

enum class SigmaThetaStateTime {
  AfterDrillingBeforeLot,
  DuringLotStep,
  Unknown,
};

enum class SigmaThetaSource {
  ElasticInitialWellboreState,
  ApbSaltCoupledState,
  LegacyDiagnosticTrace,
  ExplicitDiagnosticInput,
  SyntheticFixture,
  Unknown,
};

enum class SigmaThetaReferenceFrame {
  TotalStress,
  EffectiveStress,
  IncrementalStress,
  Unknown,
};

enum class SigmaThetaSignConvention {
  CompressionPositive,
  TensionPositive,
  Unknown,
};

enum class PressureSemantics {
  WellborePressureAbsolute,
  NetPressure,
  PressureIncrement,
  Unknown,
};

struct SigmaThetaInitialStateInput {
  bool sigma_theta_initialized = false;
  bool sigma_theta_initial_state_valid = false;
  double sigma_theta_initial_compression_positive_Pa = 0.0;
  SigmaThetaSource sigma_theta_source = SigmaThetaSource::Unknown;
  SigmaThetaStateTime sigma_theta_state_time = SigmaThetaStateTime::Unknown;
  SigmaThetaReferenceFrame sigma_theta_reference_frame =
      SigmaThetaReferenceFrame::Unknown;
  SigmaThetaSignConvention sigma_theta_sign_convention =
      SigmaThetaSignConvention::Unknown;
  PressureSemantics pressure_semantics = PressureSemantics::Unknown;
};

struct SigmaThetaInitialStateGuardResult {
  bool gate_ready = false;
  std::string status;
  std::vector<std::string> blocking_reasons;
};

[[nodiscard]] SigmaThetaInitialStateGuardResult validate_sigma_theta_initial_state(
    const SigmaThetaInitialStateInput& input);

[[nodiscard]] bool is_pressure_sigma_theta_compatible(
    PressureSemantics pressure_semantics,
    SigmaThetaReferenceFrame sigma_theta_reference_frame);

}  // namespace lss::lot
