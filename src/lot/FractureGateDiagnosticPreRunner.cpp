#include "lot/FractureGateDiagnosticPreRunner.hpp"

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

#include "lot/LimitedFractureGateRuntimeIntegration.hpp"

namespace lss::lot {
namespace {

std::string json_bool(const bool value) {
  return value ? "true" : "false";
}

std::string json_escape(const std::string& value) {
  std::string escaped;
  escaped.reserve(value.size());
  for (const char ch : value) {
    switch (ch) {
      case '\\':
        escaped += "\\\\";
        break;
      case '"':
        escaped += "\\\"";
        break;
      case '\n':
        escaped += "\\n";
        break;
      case '\r':
        escaped += "\\r";
        break;
      case '\t':
        escaped += "\\t";
        break;
      default:
        escaped += ch;
        break;
    }
  }
  return escaped;
}

std::string json_string(const std::string& value) {
  return "\"" + json_escape(value) + "\"";
}

SigmaThetaSource sigma_theta_source_from_diagnostic_input(
    const std::string& source) {
  if (source == "EXPLICIT_DIAGNOSTIC_INPUT") {
    return SigmaThetaSource::ExplicitDiagnosticInput;
  }
  if (source == "SYNTHETIC_FIXTURE") {
    return SigmaThetaSource::SyntheticFixture;
  }
  return SigmaThetaSource::Unknown;
}

}  // namespace

FractureGateRuntimeInput make_fracture_gate_runtime_input_from_case(
    const lss::core::CaseData& data) {
  FractureGateRuntimeInput input;

  input.model_selection.has_fracture_model_field =
      data.lot.fracture_model_selection_source == "EXPLICIT";
  input.model_selection.fracture_model_value = data.lot.fracture_model;

  input.sigma_theta_initial_state.sigma_theta_initialized = false;
  input.sigma_theta_initial_state.sigma_theta_initial_state_valid = false;
  input.sigma_theta_initial_state.sigma_theta_source =
      SigmaThetaSource::Unknown;
  input.sigma_theta_initial_state.sigma_theta_state_time =
      SigmaThetaStateTime::Unknown;
  input.sigma_theta_initial_state.sigma_theta_reference_frame =
      SigmaThetaReferenceFrame::Unknown;
  input.sigma_theta_initial_state.sigma_theta_sign_convention =
      SigmaThetaSignConvention::Unknown;
  input.sigma_theta_initial_state.pressure_semantics =
      PressureSemantics::Unknown;

  input.pressure_sigma_theta_criterion.pressure_semantics =
      PressureSemantics::Unknown;
  input.pressure_sigma_theta_criterion.sigma_theta_reference_frame =
      SigmaThetaReferenceFrame::Unknown;
  input.pressure_sigma_theta_criterion.sigma_theta_sign_convention =
      SigmaThetaSignConvention::Unknown;

  const auto& diagnostic = data.lot.sigma_theta_diagnostic_input;
  if (diagnostic.enabled) {
    input.sigma_theta_initial_state.sigma_theta_initialized = true;
    input.sigma_theta_initial_state.sigma_theta_initial_state_valid = true;
    input.sigma_theta_initial_state.sigma_theta_initial_compression_positive_Pa =
        diagnostic.sigma_theta_initial_compression_positive_Pa;
    input.sigma_theta_initial_state.sigma_theta_source =
        sigma_theta_source_from_diagnostic_input(diagnostic.source);
    input.sigma_theta_initial_state.sigma_theta_state_time =
        SigmaThetaStateTime::AfterDrillingBeforeLot;
    input.sigma_theta_initial_state.sigma_theta_reference_frame =
        SigmaThetaReferenceFrame::TotalStress;
    input.sigma_theta_initial_state.sigma_theta_sign_convention =
        SigmaThetaSignConvention::CompressionPositive;
    input.sigma_theta_initial_state.pressure_semantics =
        PressureSemantics::WellborePressureAbsolute;

    input.pressure_sigma_theta_criterion
        .sigma_theta_current_compression_positive_Pa =
        diagnostic.sigma_theta_current_compression_positive_Pa;
    input.pressure_sigma_theta_criterion.tensile_strength_Pa = 0.0;
    input.pressure_sigma_theta_criterion.pressure_semantics =
        PressureSemantics::WellborePressureAbsolute;
    input.pressure_sigma_theta_criterion.sigma_theta_reference_frame =
        SigmaThetaReferenceFrame::TotalStress;
    input.pressure_sigma_theta_criterion.sigma_theta_sign_convention =
        SigmaThetaSignConvention::CompressionPositive;
  }

  return input;
}

FractureGateDiagnosticPreRunnerResult
evaluate_fracture_gate_diagnostic_pre_runner(
    const lss::core::CaseData& data) {
  FractureGateDiagnosticPreRunnerResult result;
  result.fracture_gate_diagnostics_enabled =
      data.lot.fracture_gate_diagnostics.enabled;
  result.mode = data.lot.fracture_gate_diagnostics.mode;
  result.dispatch_runtime_enabled =
      data.lot.fracture_gate_diagnostics.dispatch_runtime_enabled;
  result.physically_validated = false;
  result.legacy_equivalent = false;
  result.buz29_execution_allowed = false;
  result.pkn_model_called_by_diagnostic = false;
  result.penny_adapter_called_by_diagnostic = false;

  if (!result.fracture_gate_diagnostics_enabled) {
    return result;
  }

  LimitedFractureGateRuntimeIntegrationInput input;
  input.diagnostics_enabled = result.fracture_gate_diagnostics_enabled;
  input.mode = result.mode;
  input.dispatch_runtime_enabled = result.dispatch_runtime_enabled;
  input.gate_input = make_fracture_gate_runtime_input_from_case(data);

  const auto integration =
      evaluate_limited_fracture_gate_runtime_integration(input);
  result.runtime_result = integration.gate_result;
  return result;
}

void write_fracture_gate_diagnostic_pre_runner_json(
    const std::filesystem::path& output_dir,
    const FractureGateDiagnosticPreRunnerResult& result) {
  std::filesystem::create_directories(output_dir);
  const auto path = output_dir / "diagnostic_fracture_gate.json";
  std::ofstream out(path);
  if (!out) {
    throw std::runtime_error("cannot open fracture gate diagnostic output: " +
                             path.string());
  }

  out << "{\n";
  out << "  \"fracture_gate_diagnostics_enabled\": "
      << json_bool(result.fracture_gate_diagnostics_enabled) << ",\n";
  out << "  \"mode\": " << json_string(result.mode) << ",\n";
  out << "  \"dispatch_runtime_enabled\": "
      << json_bool(result.dispatch_runtime_enabled) << ",\n";
  out << "  \"selected_fracture_model\": "
      << json_string(result.runtime_result.selected_fracture_model) << ",\n";
  out << "  \"gate_status\": "
      << json_string(to_string(result.runtime_result.gate_status)) << ",\n";
  out << "  \"dispatch_status\": "
      << json_string(to_string(result.runtime_result.dispatch_status)) << ",\n";
  out << "  \"fracture_initiated\": "
      << json_bool(result.runtime_result.fracture_initiated) << ",\n";
  out << "  \"blocking_reasons\": [";
  for (std::size_t i = 0; i < result.runtime_result.blocking_reasons.size();
       ++i) {
    if (i != 0) {
      out << ", ";
    }
    out << json_string(result.runtime_result.blocking_reasons[i]);
  }
  out << "],\n";
  out << "  \"physically_validated\": "
      << json_bool(result.physically_validated) << ",\n";
  out << "  \"legacy_equivalent\": "
      << json_bool(result.legacy_equivalent) << ",\n";
  out << "  \"buz29_execution_allowed\": "
      << json_bool(result.buz29_execution_allowed) << ",\n";
  out << "  \"pkn_model_called_by_diagnostic\": "
      << json_bool(result.pkn_model_called_by_diagnostic) << ",\n";
  out << "  \"penny_adapter_called_by_diagnostic\": "
      << json_bool(result.penny_adapter_called_by_diagnostic) << "\n";
  out << "}\n";
}

}  // namespace lss::lot
