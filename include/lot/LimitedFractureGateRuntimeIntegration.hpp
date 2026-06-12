#pragma once

#include <string>
#include <vector>

#include "lot/FractureGateRuntimeWiring.hpp"

namespace lss::lot {

struct LimitedFractureGateRuntimeIntegrationInput {
  bool diagnostics_enabled = false;
  std::string mode = "pre_runner";
  bool dispatch_runtime_enabled = false;
  FractureGateRuntimeInput gate_input;
};

struct LimitedFractureGateRuntimeIntegrationResult {
  bool evaluated = false;
  bool diagnostic_output_required = false;
  bool runtime_dispatch_enabled = false;
  FractureGateRuntimeResult gate_result;
  std::vector<std::string> blocking_reasons;
};

[[nodiscard]] bool is_limited_fracture_gate_mode_supported(
    const std::string& mode);

[[nodiscard]] LimitedFractureGateRuntimeIntegrationResult
evaluate_limited_fracture_gate_runtime_integration(
    const LimitedFractureGateRuntimeIntegrationInput& input);

}  // namespace lss::lot
