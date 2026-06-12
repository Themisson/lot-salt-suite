#include <fstream>
#include <filesystem>
#include <iterator>
#include <string>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "lot/LimitedFractureGateRuntimeIntegration.hpp"

namespace {

constexpr const char* kPknMinimalCasePath = "cases/validation/lot_pkn_minimal.yaml";

std::string read_text_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  return {std::istreambuf_iterator<char>(in),
          std::istreambuf_iterator<char>()};
}

std::filesystem::path write_temp_case(const std::string& name,
                                      const std::string& contents) {
  const auto path = std::filesystem::temp_directory_path() / name;
  std::ofstream out(path);
  REQUIRE(out.good());
  out << contents;
  return path;
}

std::filesystem::path write_case_with_diagnostics(
    const std::string& block, const std::string& suffix,
    const std::string& fracture_model_line = "") {
  auto yaml = read_text_file(kPknMinimalCasePath);
  const std::string geometry_line = "    geometry: pkn\n";
  const auto pos = yaml.find(geometry_line);
  REQUIRE(pos != std::string::npos);
  yaml.insert(pos + geometry_line.size(), fracture_model_line + block);
  return write_temp_case("lss_phase11_11e_" + suffix + ".yaml", yaml);
}

lss::lot::SigmaThetaInitialStateInput valid_sigma_theta_initial_state() {
  lss::lot::SigmaThetaInitialStateInput input;
  input.sigma_theta_initialized = true;
  input.sigma_theta_initial_state_valid = true;
  input.sigma_theta_initial_compression_positive_Pa = 5.0e6;
  input.sigma_theta_source = lss::lot::SigmaThetaSource::SyntheticFixture;
  input.sigma_theta_state_time =
      lss::lot::SigmaThetaStateTime::AfterDrillingBeforeLot;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::CompressionPositive;
  input.pressure_semantics =
      lss::lot::PressureSemantics::WellborePressureAbsolute;
  return input;
}

lss::lot::PressureSigmaThetaCriterionInput initiated_criterion() {
  lss::lot::PressureSigmaThetaCriterionInput input;
  input.sigma_theta_guard_ready = false;
  input.sigma_theta_current_compression_positive_Pa = 5.0e6;
  input.tensile_strength_Pa = 1.0e6;
  input.use_threshold_pressure_form = true;
  input.wellbore_pressure_Pa = 12.0e6;
  input.fracture_threshold_pressure_Pa = 11.0e6;
  input.pressure_semantics =
      lss::lot::PressureSemantics::WellborePressureAbsolute;
  input.sigma_theta_reference_frame =
      lss::lot::SigmaThetaReferenceFrame::TotalStress;
  input.sigma_theta_sign_convention =
      lss::lot::SigmaThetaSignConvention::CompressionPositive;
  return input;
}

lss::lot::FractureGateRuntimeInput valid_gate_input() {
  lss::lot::FractureGateRuntimeInput input;
  input.sigma_theta_initial_state = valid_sigma_theta_initial_state();
  input.pressure_sigma_theta_criterion = initiated_criterion();
  return input;
}

lss::lot::LimitedFractureGateRuntimeIntegrationInput enabled_input(
    const std::string& mode = "pre_runner") {
  lss::lot::LimitedFractureGateRuntimeIntegrationInput input;
  input.diagnostics_enabled = true;
  input.mode = mode;
  input.dispatch_runtime_enabled = false;
  input.gate_input = valid_gate_input();
  return input;
}

}  // namespace

TEST_CASE("Limited fracture gate runtime integration disabled by default does not evaluate") {
  const lss::lot::LimitedFractureGateRuntimeIntegrationInput input;

  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(input);

  CHECK_FALSE(result.evaluated);
  CHECK_FALSE(result.diagnostic_output_required);
  CHECK_FALSE(result.runtime_dispatch_enabled);
  CHECK(result.gate_result.gate_status ==
        lss::lot::FractureGateStatus::NotEvaluated);
}

TEST_CASE("Limited fracture gate runtime integration enabled false does not evaluate") {
  auto input = enabled_input();
  input.diagnostics_enabled = false;

  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(input);

  CHECK_FALSE(result.evaluated);
  CHECK_FALSE(result.diagnostic_output_required);
}

TEST_CASE("Limited fracture gate runtime integration evaluates pre_runner mode") {
  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(
          enabled_input("pre_runner"));

  CHECK(result.evaluated);
  CHECK(result.diagnostic_output_required);
  CHECK_FALSE(result.runtime_dispatch_enabled);
}

TEST_CASE("Limited fracture gate runtime integration evaluates diagnostic_only mode") {
  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(
          enabled_input("diagnostic_only"));

  CHECK(result.evaluated);
  CHECK(result.diagnostic_output_required);
  CHECK_FALSE(result.runtime_dispatch_enabled);
}

TEST_CASE("Limited fracture gate runtime integration evaluates limited_gate mode") {
  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(
          enabled_input("limited_gate"));

  CHECK(result.evaluated);
  CHECK(result.diagnostic_output_required);
  CHECK_FALSE(result.runtime_dispatch_enabled);
}

TEST_CASE("Limited fracture gate runtime integration rejects runtime dispatch") {
  auto input = enabled_input();
  input.dispatch_runtime_enabled = true;

  CHECK_THROWS_AS(
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(input),
      std::runtime_error);
}

TEST_CASE("Limited fracture gate runtime integration rejects invalid mode") {
  CHECK_FALSE(lss::lot::is_limited_fracture_gate_mode_supported("runtime"));
  CHECK_THROWS_AS(
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(
          enabled_input("runtime")),
      std::runtime_error);
}

TEST_CASE("Limited fracture gate runtime integration reports missing sigma theta as diagnostic block") {
  auto input = enabled_input("limited_gate");
  input.gate_input.sigma_theta_initial_state.sigma_theta_initialized = false;

  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(input);

  CHECK(result.evaluated);
  CHECK(result.gate_result.gate_status ==
        lss::lot::FractureGateStatus::BlockedSigmaThetaInitialState);
  CHECK(result.gate_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  REQUIRE_FALSE(result.blocking_reasons.empty());
}

TEST_CASE("Limited fracture gate runtime integration preserves PKN default as diagnostic eligibility only") {
  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(
          enabled_input("limited_gate"));

  CHECK(result.gate_result.selected_fracture_model == "PKN");
  CHECK(result.gate_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PknEligible);
  CHECK_FALSE(result.runtime_dispatch_enabled);
}

TEST_CASE("Limited fracture gate runtime integration keeps PENNY_SHAPED diagnostic only") {
  auto input = enabled_input("limited_gate");
  input.gate_input.model_selection.has_fracture_model_field = true;
  input.gate_input.model_selection.fracture_model_value = "PENNY_SHAPED";

  const auto result =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(input);

  CHECK(result.gate_result.selected_fracture_model == "PENNY_SHAPED");
  CHECK(result.gate_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PennyDiagnosticEligible);
  CHECK_FALSE(result.runtime_dispatch_enabled);
}

TEST_CASE("Limited fracture gate runtime integration header remains isolated from solver dispatch headers") {
  const auto header =
      read_text_file("include/lot/LimitedFractureGateRuntimeIntegration.hpp");

  CHECK(header.find("PknModel") == std::string::npos);
  CHECK(header.find("PknRunner") == std::string::npos);
  CHECK(header.find("PennyShapedDiagnosticAdapter") == std::string::npos);
}

TEST_CASE("Limited fracture gate runtime integration implementation remains isolated from solver dispatch headers") {
  const auto source =
      read_text_file("src/lot/LimitedFractureGateRuntimeIntegration.cpp");

  CHECK(source.find("PknModel") == std::string::npos);
  CHECK(source.find("PknRunner") == std::string::npos);
  CHECK(source.find("PennyShapedDiagnosticAdapter") == std::string::npos);
}

TEST_CASE("Limited fracture gate runtime integration requires diagnostic output only when enabled") {
  const auto disabled =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration({});
  const auto enabled =
      lss::lot::evaluate_limited_fracture_gate_runtime_integration(
          enabled_input("limited_gate"));

  CHECK_FALSE(disabled.diagnostic_output_required);
  CHECK(enabled.diagnostic_output_required);
}

TEST_CASE("Limited fracture gate runtime integration parser accepts limited_gate mode") {
  const auto path = write_case_with_diagnostics(
      "    fracture_gate_diagnostics:\n"
      "      enabled: true\n"
      "      mode: limited_gate\n"
      "      dispatch_runtime_enabled: false\n",
      "limited_gate");

  const auto data = lss::io::parse_yaml(path);

  CHECK(data.lot.fracture_gate_diagnostics.enabled);
  CHECK(data.lot.fracture_gate_diagnostics.mode == "limited_gate");
  std::filesystem::remove(path);
}
