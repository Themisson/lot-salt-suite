#pragma once

#include <string>
#include <vector>

namespace lss::lot {

struct PennyShapedDiagnosticOutputInput {
  std::string case_id = "penny_diagnostic_fixture";
  std::string phase = "11.10G";
  std::string track = "PENNY_SHAPED";
  std::string model = "PennyShapedDiagnosticWriter";

  bool diagnostic_only = true;
  bool physically_validated = false;
  bool legacy_equivalent = false;
  bool active_simulation_case = false;
  bool runtime_writer_implemented = true;
  bool implementation_allowed = false;

  double axisymmetric_angle_rad = 1.0;
  std::string axisymmetric_basis = "axisymmetric_1rad";
  double volume_conversion_factor_1rad_to_2pi = 6.283185307179586;

  double volume_multiplier = 1.0;
  std::string volume_multiplier_semantics = "VOLUME_MULTIPLIER_EMPIRICAL";
  std::string volume_multiplier_interpretation =
      "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI";
  bool volume_multiplier_is_2pi = false;

  double fracture_volume_proxy_1rad_m3 = 0.0;
  double solid_volume_1rad_m3 = 0.0;

  std::string fracture_volume_equivalent_2pi_source =
      "computed_from_1rad_proxy";
  std::string solid_volume_equivalent_2pi_source =
      "computed_from_1rad_domain_volume";
  std::string volume_interpretation =
      "axisymmetric_1rad_with_2pi_equivalent";

  std::string source_contract =
      "docs/77_axisymmetric_1rad_2pi_output_contract.md";
  std::string source_phase = "11.10D";
  std::string recommended_next_phase =
      "PHASE11_10H_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER_GATE";

  std::vector<std::string> required_caveats{
      "PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED",
      "AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED",
      "VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI",
      "NOT_PHYSICALLY_VALIDATED",
      "NOT_LEGACY_EQUIVALENT",
      "NOT_ACTIVE_SIMULATION_CASE",
      "DIAGNOSTIC_ONLY"};
};

struct PennyShapedDiagnosticOutputRecord {
  double fracture_volume_equivalent_2pi_m3 = 0.0;
  double solid_volume_equivalent_2pi_m3 = 0.0;
};

[[nodiscard]] std::vector<std::string>
required_penny_shaped_diagnostic_writer_caveats();

[[nodiscard]] PennyShapedDiagnosticOutputRecord
compute_penny_shaped_diagnostic_output_record(
    const PennyShapedDiagnosticOutputInput& input);

[[nodiscard]] std::string write_penny_shaped_diagnostic_json_string(
    const PennyShapedDiagnosticOutputInput& input);

[[nodiscard]] std::string write_penny_shaped_diagnostic_csv_header();

[[nodiscard]] std::string write_penny_shaped_diagnostic_csv_row(
    const PennyShapedDiagnosticOutputInput& input);

void validate_penny_shaped_diagnostic_output_input(
    const PennyShapedDiagnosticOutputInput& input);

}  // namespace lss::lot
