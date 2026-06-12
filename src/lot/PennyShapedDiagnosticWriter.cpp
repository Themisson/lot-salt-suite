#include "lot/PennyShapedDiagnosticWriter.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace lss::lot {
namespace {

constexpr double kTolerance = 1e-12;

const std::vector<std::string> kCsvFields{
    "case_id",
    "phase",
    "track",
    "model",
    "axisymmetric_angle_rad",
    "axisymmetric_basis",
    "volume_conversion_factor_1rad_to_2pi",
    "volume_multiplier",
    "volume_multiplier_semantics",
    "volume_multiplier_interpretation",
    "volume_multiplier_is_2pi",
    "fracture_volume_proxy_1rad_m3",
    "fracture_volume_equivalent_2pi_m3",
    "fracture_volume_equivalent_2pi_source",
    "solid_volume_1rad_m3",
    "solid_volume_equivalent_2pi_m3",
    "solid_volume_equivalent_2pi_source",
    "volume_interpretation",
    "physically_validated",
    "legacy_equivalent",
    "active_simulation_case",
    "diagnostic_only",
    "runtime_writer_implemented",
    "implementation_allowed",
    "source_contract",
    "source_phase",
    "recommended_next_phase"};

[[nodiscard]] bool contains(const std::vector<std::string>& values,
                            const std::string& needle) {
  return std::find(values.begin(), values.end(), needle) != values.end();
}

void require_finite_non_negative(double value, const std::string& field) {
  if (!std::isfinite(value) || value < 0.0) {
    throw std::invalid_argument("PennyShapedDiagnosticWriter: " + field +
                                " must be finite and non-negative");
  }
}

void require_positive(double value, const std::string& field) {
  if (!std::isfinite(value) || value <= 0.0) {
    throw std::invalid_argument("PennyShapedDiagnosticWriter: " + field +
                                " must be finite and positive");
  }
}

[[nodiscard]] std::string bool_text(bool value) {
  return value ? "true" : "false";
}

[[nodiscard]] std::string number_text(double value) {
  std::ostringstream out;
  out << std::setprecision(16) << value;
  if (std::isfinite(value) && std::floor(value) == value &&
      out.str().find('.') == std::string::npos) {
    out << ".0";
  }
  return out.str();
}

[[nodiscard]] std::string json_escape(const std::string& value) {
  std::ostringstream out;
  for (const char character : value) {
    switch (character) {
      case '\\':
        out << "\\\\";
        break;
      case '"':
        out << "\\\"";
        break;
      case '\n':
        out << "\\n";
        break;
      case '\r':
        out << "\\r";
        break;
      case '\t':
        out << "\\t";
        break;
      default:
        out << character;
        break;
    }
  }
  return out.str();
}

void append_json_string(std::ostringstream& out, const std::string& key,
                        const std::string& value, bool comma = true) {
  out << "  \"" << key << "\": \"" << json_escape(value) << "\"";
  if (comma) {
    out << ",";
  }
  out << "\n";
}

void append_json_number(std::ostringstream& out, const std::string& key,
                        double value) {
  out << "  \"" << key << "\": " << number_text(value) << ",\n";
}

void append_json_bool(std::ostringstream& out, const std::string& key,
                      bool value) {
  out << "  \"" << key << "\": " << bool_text(value) << ",\n";
}

void append_csv_value(std::ostringstream& out, const std::string& value,
                      bool first) {
  if (!first) {
    out << ",";
  }
  out << value;
}

}  // namespace

std::vector<std::string> required_penny_shaped_diagnostic_writer_caveats() {
  return {
      "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED",
      "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED",
      "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI",
      "NOT_PHYSICALLY_VALIDATED",
      "NOT_LEGACY_EQUIVALENT",
      "NOT_ACTIVE_SIMULATION_CASE",
      "DIAGNOSTIC_ONLY"};
}

void validate_penny_shaped_diagnostic_output_input(
    const PennyShapedDiagnosticOutputInput& input) {
  require_positive(input.axisymmetric_angle_rad, "axisymmetric_angle_rad");
  require_positive(input.volume_conversion_factor_1rad_to_2pi,
                   "volume_conversion_factor_1rad_to_2pi");
  require_finite_non_negative(input.volume_multiplier, "volume_multiplier");
  require_finite_non_negative(input.fracture_volume_proxy_1rad_m3,
                              "fracture_volume_proxy_1rad_m3");
  require_finite_non_negative(input.solid_volume_1rad_m3,
                              "solid_volume_1rad_m3");

  if (input.axisymmetric_basis.empty()) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: axisymmetric_basis is required");
  }
  if (input.volume_multiplier_semantics != "VOLUME_MULTIPLIER_EMPIRICAL") {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: volume_multiplier_semantics must be "
        "VOLUME_MULTIPLIER_EMPIRICAL");
  }
  if (input.volume_multiplier_interpretation !=
      "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI") {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: volume_multiplier_interpretation must "
        "be VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI");
  }
  if (input.volume_multiplier_is_2pi) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: volume_multiplier_is_2pi must be false");
  }
  if (std::isfinite(input.volume_multiplier) &&
      std::abs(input.volume_multiplier -
               input.volume_conversion_factor_1rad_to_2pi) <= kTolerance) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: volume_multiplier must not be the 2pi "
        "conversion factor");
  }
  if (input.physically_validated) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: physically_validated must be false");
  }
  if (input.legacy_equivalent) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: legacy_equivalent must be false");
  }
  if (input.active_simulation_case) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: active_simulation_case must be false");
  }
  if (!input.diagnostic_only) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: diagnostic_only must be true");
  }
  if (input.fracture_volume_equivalent_2pi_source.empty()) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: fracture_volume_equivalent_2pi_source "
        "is required");
  }
  if (input.solid_volume_equivalent_2pi_source.empty()) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: solid_volume_equivalent_2pi_source is "
        "required");
  }
  if (input.source_contract.empty() || input.source_phase.empty() ||
      input.recommended_next_phase.empty()) {
    throw std::invalid_argument(
        "PennyShapedDiagnosticWriter: source metadata is required");
  }

  for (const auto& caveat : required_penny_shaped_diagnostic_writer_caveats()) {
    if (!contains(input.required_caveats, caveat)) {
      throw std::invalid_argument(
          "PennyShapedDiagnosticWriter: missing required caveat " + caveat);
    }
  }
}

PennyShapedDiagnosticOutputRecord compute_penny_shaped_diagnostic_output_record(
    const PennyShapedDiagnosticOutputInput& input) {
  validate_penny_shaped_diagnostic_output_input(input);
  PennyShapedDiagnosticOutputRecord record;
  record.fracture_volume_equivalent_2pi_m3 =
      input.fracture_volume_proxy_1rad_m3 *
      input.volume_conversion_factor_1rad_to_2pi;
  record.solid_volume_equivalent_2pi_m3 =
      input.solid_volume_1rad_m3 *
      input.volume_conversion_factor_1rad_to_2pi;
  return record;
}

std::string write_penny_shaped_diagnostic_json_string(
    const PennyShapedDiagnosticOutputInput& input) {
  const auto record = compute_penny_shaped_diagnostic_output_record(input);

  std::ostringstream out;
  out << "{\n";
  append_json_string(out, "case_id", input.case_id);
  append_json_string(out, "phase", input.phase);
  append_json_string(out, "track", input.track);
  append_json_string(out, "model", input.model);
  append_json_number(out, "axisymmetric_angle_rad",
                     input.axisymmetric_angle_rad);
  append_json_string(out, "axisymmetric_basis", input.axisymmetric_basis);
  append_json_number(out, "volume_conversion_factor_1rad_to_2pi",
                     input.volume_conversion_factor_1rad_to_2pi);
  append_json_number(out, "volume_multiplier", input.volume_multiplier);
  append_json_string(out, "volume_multiplier_semantics",
                     input.volume_multiplier_semantics);
  append_json_string(out, "volume_multiplier_interpretation",
                     input.volume_multiplier_interpretation);
  append_json_bool(out, "volume_multiplier_is_2pi",
                   input.volume_multiplier_is_2pi);
  append_json_number(out, "fracture_volume_proxy_1rad_m3",
                     input.fracture_volume_proxy_1rad_m3);
  append_json_number(out, "fracture_volume_equivalent_2pi_m3",
                     record.fracture_volume_equivalent_2pi_m3);
  append_json_string(out, "fracture_volume_equivalent_2pi_source",
                     input.fracture_volume_equivalent_2pi_source);
  append_json_number(out, "solid_volume_1rad_m3",
                     input.solid_volume_1rad_m3);
  append_json_number(out, "solid_volume_equivalent_2pi_m3",
                     record.solid_volume_equivalent_2pi_m3);
  append_json_string(out, "solid_volume_equivalent_2pi_source",
                     input.solid_volume_equivalent_2pi_source);
  append_json_string(out, "volume_interpretation",
                     input.volume_interpretation);
  append_json_bool(out, "physically_validated",
                   input.physically_validated);
  append_json_bool(out, "legacy_equivalent", input.legacy_equivalent);
  append_json_bool(out, "active_simulation_case",
                   input.active_simulation_case);
  append_json_bool(out, "diagnostic_only", input.diagnostic_only);
  append_json_bool(out, "runtime_writer_implemented",
                   input.runtime_writer_implemented);
  append_json_bool(out, "implementation_allowed", input.implementation_allowed);
  append_json_string(out, "source_contract", input.source_contract);
  append_json_string(out, "source_phase", input.source_phase);
  append_json_string(out, "recommended_next_phase",
                     input.recommended_next_phase);
  out << "  \"required_caveats\": [\n";
  for (std::size_t index = 0; index < input.required_caveats.size(); ++index) {
    out << "    \"" << json_escape(input.required_caveats[index]) << "\"";
    if (index + 1 < input.required_caveats.size()) {
      out << ",";
    }
    out << "\n";
  }
  out << "  ]\n";
  out << "}\n";
  return out.str();
}

std::string write_penny_shaped_diagnostic_csv_header() {
  std::ostringstream out;
  for (std::size_t index = 0; index < kCsvFields.size(); ++index) {
    if (index > 0) {
      out << ",";
    }
    out << kCsvFields[index];
  }
  return out.str();
}

std::string write_penny_shaped_diagnostic_csv_row(
    const PennyShapedDiagnosticOutputInput& input) {
  const auto record = compute_penny_shaped_diagnostic_output_record(input);
  std::ostringstream out;
  bool first = true;
  append_csv_value(out, input.case_id, first);
  first = false;
  append_csv_value(out, input.phase, first);
  append_csv_value(out, input.track, first);
  append_csv_value(out, input.model, first);
  append_csv_value(out, number_text(input.axisymmetric_angle_rad), first);
  append_csv_value(out, input.axisymmetric_basis, first);
  append_csv_value(out, number_text(input.volume_conversion_factor_1rad_to_2pi),
                   first);
  append_csv_value(out, number_text(input.volume_multiplier), first);
  append_csv_value(out, input.volume_multiplier_semantics, first);
  append_csv_value(out, input.volume_multiplier_interpretation, first);
  append_csv_value(out, bool_text(input.volume_multiplier_is_2pi), first);
  append_csv_value(out, number_text(input.fracture_volume_proxy_1rad_m3),
                   first);
  append_csv_value(out,
                   number_text(record.fracture_volume_equivalent_2pi_m3),
                   first);
  append_csv_value(out, input.fracture_volume_equivalent_2pi_source, first);
  append_csv_value(out, number_text(input.solid_volume_1rad_m3), first);
  append_csv_value(out, number_text(record.solid_volume_equivalent_2pi_m3),
                   first);
  append_csv_value(out, input.solid_volume_equivalent_2pi_source, first);
  append_csv_value(out, input.volume_interpretation, first);
  append_csv_value(out, bool_text(input.physically_validated), first);
  append_csv_value(out, bool_text(input.legacy_equivalent), first);
  append_csv_value(out, bool_text(input.active_simulation_case), first);
  append_csv_value(out, bool_text(input.diagnostic_only), first);
  append_csv_value(out, bool_text(input.runtime_writer_implemented), first);
  append_csv_value(out, bool_text(input.implementation_allowed), first);
  append_csv_value(out, input.source_contract, first);
  append_csv_value(out, input.source_phase, first);
  append_csv_value(out, input.recommended_next_phase, first);
  return out.str();
}

}  // namespace lss::lot
