#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PennyShapedDiagnosticWriter.hpp"

namespace {

lss::lot::PennyShapedDiagnosticOutputInput fixture_input() {
  lss::lot::PennyShapedDiagnosticOutputInput input;
  input.case_id = "phase11_10e_penny_fixture";
  input.phase = "11.10E";
  input.model = "PennyShapedDiagnosticAdapter";
  input.runtime_writer_implemented = false;
  input.implementation_allowed = false;
  input.volume_multiplier = 10.0;
  input.fracture_volume_proxy_1rad_m3 = 0.5;
  input.solid_volume_1rad_m3 = 10.0;
  input.recommended_next_phase =
      "PHASE11_10F_SPECIFY_PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION";
  input.required_caveats.push_back("IMPLEMENTATION_NOT_ALLOWED_IN_11_10E");
  return input;
}

std::string read_text(const std::string& path) {
  std::ifstream input(path);
  std::ostringstream buffer;
  buffer << input.rdbuf();
  return buffer.str();
}

}  // namespace

TEST_CASE("PennyShapedDiagnosticWriter converts 1rad fracture volume to 2pi") {
  const auto input = fixture_input();

  const auto record =
      lss::lot::compute_penny_shaped_diagnostic_output_record(input);

  CHECK(record.fracture_volume_equivalent_2pi_m3 ==
        Catch::Approx(input.fracture_volume_proxy_1rad_m3 * std::acos(-1.0) *
                      2.0));
}

TEST_CASE("PennyShapedDiagnosticWriter converts 1rad solid volume to 2pi") {
  const auto input = fixture_input();

  const auto record =
      lss::lot::compute_penny_shaped_diagnostic_output_record(input);

  CHECK(record.solid_volume_equivalent_2pi_m3 ==
        Catch::Approx(input.solid_volume_1rad_m3 * std::acos(-1.0) * 2.0));
}

TEST_CASE("PennyShapedDiagnosticWriter emits required JSON fields") {
  const auto json =
      lss::lot::write_penny_shaped_diagnostic_json_string(fixture_input());

  CHECK(json.find("\"case_id\": \"phase11_10e_penny_fixture\"") !=
        std::string::npos);
  CHECK(json.find("\"axisymmetric_angle_rad\"") != std::string::npos);
  CHECK(json.find("\"fracture_volume_proxy_1rad_m3\"") !=
        std::string::npos);
  CHECK(json.find("\"fracture_volume_equivalent_2pi_m3\"") !=
        std::string::npos);
  CHECK(json.find("\"solid_volume_equivalent_2pi_m3\"") !=
        std::string::npos);
  CHECK(json.find("\"physically_validated\": false") != std::string::npos);
  CHECK(json.find("\"legacy_equivalent\": false") != std::string::npos);
  CHECK(json.find("\"active_simulation_case\": false") != std::string::npos);
  CHECK(json.find("VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI") !=
        std::string::npos);
}

TEST_CASE("PennyShapedDiagnosticWriter emits CSV header contract") {
  const auto header = lss::lot::write_penny_shaped_diagnostic_csv_header();

  CHECK(header.find("case_id,phase,track,model") == 0);
  CHECK(header.find("fracture_volume_proxy_1rad_m3") != std::string::npos);
  CHECK(header.find("fracture_volume_equivalent_2pi_source") !=
        std::string::npos);
  CHECK(header.find("solid_volume_equivalent_2pi_source") !=
        std::string::npos);
  CHECK(header.find("recommended_next_phase") != std::string::npos);
}

TEST_CASE("PennyShapedDiagnosticWriter emits fixture-compatible CSV row") {
  const auto csv_path =
      "tests/fixtures/comparison/phase11_10e/"
      "penny_diagnostic_output_expected.csv";
  const auto expected_csv = read_text(csv_path);
  const auto expected_row = expected_csv.substr(expected_csv.find('\n') + 1);
  const auto row =
      lss::lot::write_penny_shaped_diagnostic_csv_row(fixture_input());

  CHECK(row == expected_row.substr(0, expected_row.find_last_not_of("\r\n") + 1));
}

TEST_CASE("PennyShapedDiagnosticWriter rejects forbidden flag states") {
  auto input = fixture_input();
  input.volume_multiplier_is_2pi = true;
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);

  input = fixture_input();
  input.physically_validated = true;
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);

  input = fixture_input();
  input.legacy_equivalent = true;
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);

  input = fixture_input();
  input.active_simulation_case = true;
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);
}

TEST_CASE("PennyShapedDiagnosticWriter requires caveats and 2pi sources") {
  auto input = fixture_input();
  input.required_caveats.clear();
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);

  input = fixture_input();
  input.fracture_volume_equivalent_2pi_source.clear();
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);

  input = fixture_input();
  input.solid_volume_equivalent_2pi_source.clear();
  CHECK_THROWS_AS(lss::lot::write_penny_shaped_diagnostic_json_string(input),
                  std::invalid_argument);
}

TEST_CASE("PennyShapedDiagnosticWriter rejects invalid angular and volume data") {
  auto input = fixture_input();
  input.axisymmetric_angle_rad = 0.0;
  CHECK_THROWS_AS(lss::lot::compute_penny_shaped_diagnostic_output_record(input),
                  std::invalid_argument);

  input = fixture_input();
  input.volume_conversion_factor_1rad_to_2pi = 0.0;
  CHECK_THROWS_AS(lss::lot::compute_penny_shaped_diagnostic_output_record(input),
                  std::invalid_argument);

  input = fixture_input();
  input.fracture_volume_proxy_1rad_m3 = -1.0;
  CHECK_THROWS_AS(lss::lot::compute_penny_shaped_diagnostic_output_record(input),
                  std::invalid_argument);
}
