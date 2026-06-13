#include "lot/Buz29PennyDiagnosticRunner.hpp"

#include <exception>
#include <sstream>

#include "lot/PennyShapedDiagnosticAdapter.hpp"
#include "lot/PennyShapedDiagnosticWriter.hpp"

namespace lss::lot {
namespace {

void append_reason(std::vector<std::string>& reasons,
                   const std::string& reason) {
  reasons.push_back(reason);
}

Buz29PennyDiagnosticRunnerResult base_result() {
  Buz29PennyDiagnosticRunnerResult result;
  result.diagnostic_only = true;
  result.physically_validated = false;
  result.legacy_equivalent = false;
  result.runtime_dispatch_enabled = false;
  result.penny_shaped_runtime_enabled = false;
  result.pkn_behavior_changed = false;
  result.physical_validation_claimed = false;
  result.legacy_equivalence_claimed = false;
  result.caveats = required_buz29_penny_diagnostic_runner_caveats();
  return result;
}

bool has_invalid_flags(const Buz29PennyDiagnosticRunnerInput& input,
                       Buz29PennyDiagnosticRunnerResult& result) {
  bool invalid = false;
  if (!input.diagnostic_only) {
    append_reason(result.blocking_reasons, "DIAGNOSTIC_ONLY_REQUIRED");
    invalid = true;
  }
  if (input.physically_validated) {
    append_reason(result.blocking_reasons, "PHYSICALLY_VALIDATED_FORBIDDEN");
    invalid = true;
  }
  if (input.legacy_equivalent) {
    append_reason(result.blocking_reasons, "LEGACY_EQUIVALENT_FORBIDDEN");
    invalid = true;
  }
  if (input.runtime_dispatch_enabled) {
    append_reason(result.blocking_reasons, "RUNTIME_DISPATCH_FORBIDDEN");
    invalid = true;
  }
  return invalid;
}

PennyShapedDiagnosticOutputInput make_writer_input(
    const Buz29PennyDiagnosticRunnerInput& input,
    const PennyShapedDiagnosticResult& adapter_result) {
  PennyShapedDiagnosticOutputInput writer_input;
  writer_input.case_id = input.case_id;
  writer_input.phase = "PHASE_FIX_BUZ29_PENNY_DIAGNOSTIC_RUNNER";
  writer_input.track = "PENNY_SHAPED";
  writer_input.model = "Buz29PennyDiagnosticRunner";
  writer_input.diagnostic_only = true;
  writer_input.physically_validated = false;
  writer_input.legacy_equivalent = false;
  writer_input.active_simulation_case = false;
  writer_input.runtime_writer_implemented = true;
  writer_input.implementation_allowed = true;
  writer_input.volume_multiplier = input.volume_multiplier;
  writer_input.fracture_volume_proxy_1rad_m3 =
      adapter_result.model_result.fracture_volume_proxy_m3;
  writer_input.solid_volume_1rad_m3 = 0.0;
  writer_input.source_phase =
      "PHASE_FIX_BUZ29_PENNY_DIAGNOSTIC_RUNNER";
  writer_input.recommended_next_phase =
      "PHASE_COMPLETE_BUZ29_PENNY_ADAPTER_INPUTS";
  return writer_input;
}

}  // namespace

std::vector<std::string> required_buz29_penny_diagnostic_runner_caveats() {
  return {"DIAGNOSTIC_ONLY",
          "NOT_PHYSICALLY_VALIDATED",
          "NOT_LEGACY_EQUIVALENT",
          "NO_RUNTIME_DISPATCH",
          "PENNY_SHAPED_DIAGNOSTIC_ONLY",
          "BUZ29_REAL_INPUTS_NOT_IMPROVISED"};
}

Buz29PennyDiagnosticRunnerResult run_buz29_penny_diagnostic(
    const Buz29PennyDiagnosticRunnerInput& input) {
  auto result = base_result();

  if (has_invalid_flags(input, result)) {
    result.run_status =
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_INVALID_FLAGS";
    return result;
  }

  if (input.fracture_model != "PENNY_SHAPED") {
    result.run_status =
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_UNSUPPORTED_MODEL";
    append_reason(result.blocking_reasons,
                  "ONLY_PENNY_SHAPED_DIAGNOSTIC_MODEL_SUPPORTED");
    return result;
  }

  if (!input.adapter_inputs_complete) {
    result.run_status =
        "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED_BY_PARTIAL_INPUTS";
    append_reason(result.blocking_reasons,
                  "BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL");
    for (const auto& field : input.missing_adapter_fields) {
      append_reason(result.blocking_reasons, "MISSING_FIELD:" + field);
    }
    return result;
  }

  try {
    PennyShapedDiagnosticInput adapter_input;
    adapter_input.young_modulus_Pa = input.young_modulus_Pa;
    adapter_input.poisson_ratio = input.poisson_ratio;
    adapter_input.viscosity_Pa_min = input.viscosity_Pa_min;
    adapter_input.flow_rate_m3_min = input.flow_rate_m3_min;
    adapter_input.elapsed_since_opening_min =
        input.elapsed_since_opening_min;
    adapter_input.wellbore_pressure_Pa = input.wellbore_pressure_Pa;
    adapter_input.sigma_theta_compression_positive_Pa =
        input.sigma_theta_compression_positive_Pa;
    adapter_input.volume_multiplier = input.volume_multiplier;
    adapter_input.source = "Buz29PennyDiagnosticRunner";
    adapter_input.caveat =
        "Diagnostic runner only. Not BUZ29 physical validation. Not legacy "
        "equivalence. No runtime dispatch.";

    const auto adapter_result = run_penny_shaped_diagnostic(adapter_input);
    const auto writer_input = make_writer_input(input, adapter_result);

    result.diagnostic_json =
        write_penny_shaped_diagnostic_json_string(writer_input);
    std::ostringstream csv;
    csv << write_penny_shaped_diagnostic_csv_header() << "\n"
        << write_penny_shaped_diagnostic_csv_row(writer_input) << "\n";
    result.diagnostic_csv = csv.str();
    result.run_status = "BUZ29_PENNY_DIAGNOSTIC_RUN_COMPLETED";
    result.execution_completed = true;
    return result;
  } catch (const std::exception& error) {
    result.run_status =
        "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED_BY_PARTIAL_INPUTS";
    append_reason(result.blocking_reasons,
                  std::string("ADAPTER_OR_WRITER_REJECTED_INPUT:") +
                      error.what());
    return result;
  }
}

}  // namespace lss::lot
