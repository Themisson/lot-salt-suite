#pragma once

#include <filesystem>
#include <string>

#include "core/types.hpp"
#include "lot/FractureGateRuntimeWiring.hpp"

namespace lss::lot {

struct FractureGateDiagnosticPreRunnerResult {
  bool fracture_gate_diagnostics_enabled = false;
  std::string mode = "pre_runner";
  bool dispatch_runtime_enabled = false;
  FractureGateRuntimeResult runtime_result;
  bool physically_validated = false;
  bool legacy_equivalent = false;
  bool buz29_execution_allowed = false;
  bool pkn_model_called_by_diagnostic = false;
  bool penny_adapter_called_by_diagnostic = false;
};

[[nodiscard]] FractureGateRuntimeInput
make_fracture_gate_runtime_input_from_case(const lss::core::CaseData& data);

[[nodiscard]] FractureGateDiagnosticPreRunnerResult
evaluate_fracture_gate_diagnostic_pre_runner(
    const lss::core::CaseData& data);

void write_fracture_gate_diagnostic_pre_runner_json(
    const std::filesystem::path& output_dir,
    const FractureGateDiagnosticPreRunnerResult& result);

}  // namespace lss::lot
