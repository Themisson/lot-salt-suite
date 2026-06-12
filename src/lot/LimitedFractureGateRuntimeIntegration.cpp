#include "lot/LimitedFractureGateRuntimeIntegration.hpp"

#include <stdexcept>

namespace lss::lot {

bool is_limited_fracture_gate_mode_supported(const std::string& mode) {
  return mode == "pre_runner" || mode == "diagnostic_only" ||
         mode == "limited_gate";
}

LimitedFractureGateRuntimeIntegrationResult
evaluate_limited_fracture_gate_runtime_integration(
    const LimitedFractureGateRuntimeIntegrationInput& input) {
  LimitedFractureGateRuntimeIntegrationResult result;

  if (!input.diagnostics_enabled) {
    return result;
  }

  result.diagnostic_output_required = true;
  if (input.dispatch_runtime_enabled) {
    result.blocking_reasons.emplace_back(
        "LIMITED_FRACTURE_GATE_BLOCKED_RUNTIME_DISPATCH_ENABLED");
    throw std::runtime_error(
        "fracture_gate_diagnostics.dispatch_runtime_enabled must be false "
        "for limited fracture gate runtime integration");
  }

  if (!is_limited_fracture_gate_mode_supported(input.mode)) {
    result.blocking_reasons.emplace_back(
        "LIMITED_FRACTURE_GATE_BLOCKED_UNSUPPORTED_MODE");
    throw std::runtime_error(
        "fracture_gate_diagnostics.mode must be pre_runner, diagnostic_only "
        "or limited_gate");
  }

  result.evaluated = true;
  result.runtime_dispatch_enabled = false;
  result.gate_result = evaluate_fracture_gate_runtime(input.gate_input);
  result.blocking_reasons = result.gate_result.blocking_reasons;
  return result;
}

}  // namespace lss::lot
