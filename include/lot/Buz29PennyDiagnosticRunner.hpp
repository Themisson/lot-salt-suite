#pragma once

#include <string>
#include <vector>

namespace lss::lot {

struct Buz29PennyDiagnosticRunnerInput {
  bool diagnostic_only = true;
  bool physically_validated = false;
  bool legacy_equivalent = false;
  bool runtime_dispatch_enabled = false;

  std::string case_id = "buz29_penny_diagnostic_fixture";
  std::string fracture_model = "PENNY_SHAPED";

  double young_modulus_Pa = 0.0;
  double poisson_ratio = 0.0;
  double viscosity_Pa_min = 0.0;
  double flow_rate_m3_min = 0.0;
  double elapsed_since_opening_min = 0.0;
  double wellbore_pressure_Pa = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  double volume_multiplier = 10.0;

  bool adapter_inputs_complete = false;
  std::vector<std::string> missing_adapter_fields;
};

struct Buz29PennyDiagnosticRunnerResult {
  std::string run_status =
      "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED_BY_PARTIAL_INPUTS";
  bool execution_completed = false;
  bool diagnostic_only = true;
  bool physically_validated = false;
  bool legacy_equivalent = false;
  bool runtime_dispatch_enabled = false;
  bool penny_shaped_runtime_enabled = false;
  bool pkn_behavior_changed = false;
  bool physical_validation_claimed = false;
  bool legacy_equivalence_claimed = false;

  std::vector<std::string> blocking_reasons;
  std::vector<std::string> caveats;
  std::string diagnostic_json;
  std::string diagnostic_csv;
};

[[nodiscard]] std::vector<std::string>
required_buz29_penny_diagnostic_runner_caveats();

[[nodiscard]] Buz29PennyDiagnosticRunnerResult
run_buz29_penny_diagnostic(const Buz29PennyDiagnosticRunnerInput& input);

}  // namespace lss::lot
