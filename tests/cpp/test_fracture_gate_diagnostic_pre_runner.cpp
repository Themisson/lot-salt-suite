#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "lot/FractureGateDiagnosticPreRunner.hpp"

#ifndef LSS_ENABLE_CLI_SUBPROCESS_TESTS
#define LSS_ENABLE_CLI_SUBPROCESS_TESTS 1
#endif

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
  return write_temp_case("lss_phase11_10y_" + suffix + ".yaml", yaml);
}

std::filesystem::path write_enabled_case(const std::string& suffix) {
  return write_case_with_diagnostics(
      "    fracture_gate_diagnostics:\n"
      "      enabled: true\n"
      "      mode: pre_runner\n"
      "      dispatch_runtime_enabled: false\n",
      suffix);
}

std::string sigma_theta_diagnostic_input_block(
    const double sigma_theta_current_compression_positive_Pa,
    const std::string& source = "EXPLICIT_DIAGNOSTIC_INPUT") {
  return "    sigma_theta_diagnostic_input:\n"
         "      enabled: true\n"
         "      source: " + source + "\n"
         "      sigma_theta_initial_compression_positive_Pa: 5000000.0\n"
         "      sigma_theta_current_compression_positive_Pa: " +
         std::to_string(sigma_theta_current_compression_positive_Pa) + "\n"
         "      sign_convention: COMPRESSION_POSITIVE\n"
         "      reference_frame: WELLBORE_WALL_TOTAL_STRESS\n"
         "      state_time: POST_DRILLING_BEFORE_LOT\n"
         "      physically_validated: false\n"
         "      legacy_equivalent: false\n";
}

std::filesystem::path write_enabled_case_with_sigma_theta(
    const std::string& suffix,
    const double sigma_theta_current_compression_positive_Pa,
    const std::string& fracture_model_line = "") {
  return write_case_with_diagnostics(
      fracture_model_line +
          "    fracture_gate_diagnostics:\n"
          "      enabled: true\n"
          "      mode: limited_gate\n"
          "      dispatch_runtime_enabled: false\n" +
          sigma_theta_diagnostic_input_block(
              sigma_theta_current_compression_positive_Pa),
      suffix);
}

std::string quote(const std::filesystem::path& path) {
  return "\"" + path.string() + "\"";
}

std::filesystem::path lot_sim_executable() {
#ifdef LSS_LOT_SIM_EXECUTABLE
  return std::filesystem::path(LSS_LOT_SIM_EXECUTABLE);
#else
  const auto base = std::filesystem::current_path() / "build";
  for (const char* cfg : {"Debug", "Release", "RelWithDebInfo", "MinSizeRel"}) {
#ifdef _WIN32
    auto p = base / cfg / "lot-sim.exe";
#else
    auto p = base / cfg / "lot-sim";
#endif
    if (std::filesystem::exists(p)) return p;
  }
#ifdef _WIN32
  return base / "lot-sim.exe";
#else
  return base / "lot-sim";
#endif
#endif
}

std::string command_prefix() {
#ifdef _WIN32
  return "call " + quote(lot_sim_executable());
#else
  return quote(lot_sim_executable());
#endif
}

bool contains(const std::string& text, const std::string& needle) {
  return text.find(needle) != std::string::npos;
}

}  // namespace

TEST_CASE("Diagnostic pre-runner is disabled by default") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  CHECK_FALSE(data.lot.fracture_gate_diagnostics.enabled);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK_FALSE(result.fracture_gate_diagnostics_enabled);
  CHECK(result.runtime_result.gate_status ==
        lss::lot::FractureGateStatus::NotEvaluated);
  CHECK_FALSE(result.pkn_model_called_by_diagnostic);
  CHECK_FALSE(result.penny_adapter_called_by_diagnostic);
}

TEST_CASE("Diagnostic pre-runner enabled false preserves disabled behavior") {
  const auto path = write_case_with_diagnostics(
      "    fracture_gate_diagnostics:\n"
      "      enabled: false\n"
      "      mode: pre_runner\n"
      "      dispatch_runtime_enabled: false\n",
      "disabled_false");
  const auto data = lss::io::parse_yaml(path);

  CHECK_FALSE(data.lot.fracture_gate_diagnostics.enabled);
  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);
  CHECK_FALSE(result.fracture_gate_diagnostics_enabled);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner accepts enabled true with dispatch disabled") {
  const auto path = write_enabled_case("enabled_true");
  const auto data = lss::io::parse_yaml(path);

  CHECK(data.lot.fracture_gate_diagnostics.enabled);
  CHECK(data.lot.fracture_gate_diagnostics.mode == "pre_runner");
  CHECK_FALSE(data.lot.fracture_gate_diagnostics.dispatch_runtime_enabled);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner rejects dispatch runtime enabled") {
  const auto path = write_case_with_diagnostics(
      "    fracture_gate_diagnostics:\n"
      "      enabled: true\n"
      "      mode: pre_runner\n"
      "      dispatch_runtime_enabled: true\n",
      "dispatch_true");

  CHECK_THROWS_AS(lss::io::parse_yaml(path), std::runtime_error);
  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner accepts pre_runner diagnostic_only and limited_gate modes") {
  for (const std::string mode :
       {"pre_runner", "diagnostic_only", "limited_gate"}) {
    const auto path = write_case_with_diagnostics(
        "    fracture_gate_diagnostics:\n"
        "      enabled: true\n"
        "      mode: " + mode + "\n"
        "      dispatch_runtime_enabled: false\n",
        mode);
    const auto data = lss::io::parse_yaml(path);
    CHECK(data.lot.fracture_gate_diagnostics.mode == mode);
    std::filesystem::remove(path);
  }
}

TEST_CASE("Diagnostic pre-runner rejects invalid mode") {
  const auto path = write_case_with_diagnostics(
      "    fracture_gate_diagnostics:\n"
      "      enabled: true\n"
      "      mode: runtime_dispatch\n"
      "      dispatch_runtime_enabled: false\n",
      "bad_mode");

  CHECK_THROWS_AS(lss::io::parse_yaml(path), std::runtime_error);
  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner blocks when initial sigma theta is absent") {
  const auto path = write_enabled_case("missing_sigmatheta");
  const auto data = lss::io::parse_yaml(path);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK(result.fracture_gate_diagnostics_enabled);
  CHECK(result.runtime_result.selected_fracture_model == "PKN");
  CHECK(result.runtime_result.gate_status ==
        lss::lot::FractureGateStatus::BlockedSigmaThetaInitialState);
  CHECK(result.runtime_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  CHECK_FALSE(result.runtime_result.fracture_initiated);
  REQUIRE_FALSE(result.runtime_result.blocking_reasons.empty());
  CHECK(contains(result.runtime_result.blocking_reasons.front(),
                 "FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA"));

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner fills sigma theta guards from diagnostic input") {
  const auto path = write_enabled_case_with_sigma_theta("sigmatheta_input",
                                                       5000000.0);
  const auto data = lss::io::parse_yaml(path);
  const auto input = lss::lot::make_fracture_gate_runtime_input_from_case(data);

  CHECK(input.sigma_theta_initial_state.sigma_theta_initialized);
  CHECK(input.sigma_theta_initial_state.sigma_theta_initial_state_valid);
  CHECK(input.sigma_theta_initial_state.sigma_theta_source ==
        lss::lot::SigmaThetaSource::ExplicitDiagnosticInput);
  CHECK(input.sigma_theta_initial_state.sigma_theta_state_time ==
        lss::lot::SigmaThetaStateTime::AfterDrillingBeforeLot);
  CHECK(input.sigma_theta_initial_state.sigma_theta_reference_frame ==
        lss::lot::SigmaThetaReferenceFrame::TotalStress);
  CHECK(input.sigma_theta_initial_state.sigma_theta_sign_convention ==
        lss::lot::SigmaThetaSignConvention::CompressionPositive);
  CHECK(input.pressure_sigma_theta_criterion
            .sigma_theta_current_compression_positive_Pa ==
        Catch::Approx(5000000.0));
  CHECK(input.pressure_sigma_theta_criterion.pressure_semantics ==
        lss::lot::PressureSemantics::WellborePressureAbsolute);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner reports ready not reached for compressive current sigma theta") {
  const auto path = write_enabled_case_with_sigma_theta("not_reached",
                                                       5000000.0);
  const auto data = lss::io::parse_yaml(path);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK(result.runtime_result.gate_status ==
        lss::lot::FractureGateStatus::ReadyNotReached);
  CHECK(result.runtime_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotExecuted);
  CHECK_FALSE(result.runtime_result.fracture_initiated);
  CHECK_FALSE(result.dispatch_runtime_enabled);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner reports PKN eligible when sigma theta criterion is reached") {
  const auto path =
      write_enabled_case_with_sigma_theta("pkn_reached", -2000000.0);
  const auto data = lss::io::parse_yaml(path);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK(result.runtime_result.gate_status ==
        lss::lot::FractureGateStatus::Reached);
  CHECK(result.runtime_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PknEligible);
  CHECK(result.runtime_result.fracture_initiated);
  CHECK_FALSE(result.pkn_model_called_by_diagnostic);
  CHECK_FALSE(result.dispatch_runtime_enabled);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner reports PENNY diagnostic eligible without adapter call") {
  const auto path = write_enabled_case_with_sigma_theta(
      "penny_reached", -2000000.0, "    fracture_model: PENNY_SHAPED\n");
  const auto data = lss::io::parse_yaml(path);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK(result.runtime_result.selected_fracture_model == "PENNY_SHAPED");
  CHECK(result.runtime_result.gate_status ==
        lss::lot::FractureGateStatus::Reached);
  CHECK(result.runtime_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::PennyDiagnosticEligible);
  CHECK(result.runtime_result.fracture_initiated);
  CHECK_FALSE(result.penny_adapter_called_by_diagnostic);
  CHECK_FALSE(result.dispatch_runtime_enabled);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner preserves PKN as default selected model") {
  const auto path = write_enabled_case("pkn_default");
  const auto data = lss::io::parse_yaml(path);
  const auto input = lss::lot::make_fracture_gate_runtime_input_from_case(data);

  CHECK_FALSE(input.model_selection.has_fracture_model_field);
  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);
  CHECK(result.runtime_result.selected_fracture_model == "PKN");

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner accepts explicit PENNY_SHAPED as diagnostic metadata") {
  const auto path = write_case_with_diagnostics(
      "    fracture_gate_diagnostics:\n"
      "      enabled: true\n"
      "      mode: pre_runner\n"
      "      dispatch_runtime_enabled: false\n",
      "penny",
      "    fracture_model: PENNY_SHAPED\n");
  const auto data = lss::io::parse_yaml(path);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK(result.runtime_result.selected_fracture_model == "PENNY_SHAPED");
  CHECK(result.runtime_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);
  CHECK_FALSE(result.penny_adapter_called_by_diagnostic);

  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner writes isolated JSON output") {
  const auto path = write_enabled_case("write_json");
  const auto data = lss::io::parse_yaml(path);
  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);
  const auto output_dir =
      std::filesystem::temp_directory_path() / "lss_phase11_10y_diagnostic_json";
  std::filesystem::remove_all(output_dir);

  lss::lot::write_fracture_gate_diagnostic_pre_runner_json(output_dir, result);

  const auto json = read_text_file(output_dir / "diagnostic_fracture_gate.json");
  CHECK(contains(json, "\"fracture_gate_diagnostics_enabled\": true"));
  CHECK(contains(json, "\"selected_fracture_model\": \"PKN\""));
  CHECK(contains(json,
                 "\"gate_status\": "
                 "\"FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE\""));
  CHECK(contains(json, "\"dispatch_status\": \"FRACTURE_DISPATCH_NOT_ALLOWED\""));
  CHECK(contains(json, "\"physically_validated\": false"));
  CHECK(contains(json, "\"legacy_equivalent\": false"));
  CHECK(contains(json, "\"buz29_execution_allowed\": false"));

  std::filesystem::remove_all(output_dir);
  std::filesystem::remove(path);
}

TEST_CASE("Diagnostic pre-runner does not call PknModel or Penny adapter") {
  const auto path = write_enabled_case("no_solver_calls");
  const auto data = lss::io::parse_yaml(path);

  const auto result =
      lss::lot::evaluate_fracture_gate_diagnostic_pre_runner(data);

  CHECK_FALSE(result.pkn_model_called_by_diagnostic);
  CHECK_FALSE(result.penny_adapter_called_by_diagnostic);
  CHECK(result.runtime_result.dispatch_status ==
        lss::lot::FractureDispatchStatus::NotAllowed);

  std::filesystem::remove(path);
}

#if LSS_ENABLE_CLI_SUBPROCESS_TESTS
TEST_CASE("CLI run writes isolated fracture gate diagnostic when opt-in") {
  const auto case_path = write_enabled_case("cli");
  const auto output_dir =
      std::filesystem::temp_directory_path() / "lss_phase11_10y_cli";
  std::filesystem::remove_all(output_dir);
  const std::string command = command_prefix() + " run --case " +
                              quote(case_path) +
                              " --mode lot-pkn --output " + quote(output_dir);
  CAPTURE(command);

  const int rc = std::system(command.c_str());

  CHECK(rc == 0);
  CHECK(std::filesystem::exists(output_dir / "result.json"));
  CHECK(std::filesystem::exists(output_dir / "timeseries.csv"));
  CHECK(std::filesystem::exists(output_dir / "diagnostic_fracture_gate.json"));

  const auto json = read_text_file(output_dir / "diagnostic_fracture_gate.json");
  CHECK(contains(json, "\"pkn_model_called_by_diagnostic\": false"));
  CHECK(contains(json, "\"penny_adapter_called_by_diagnostic\": false"));

  std::filesystem::remove_all(output_dir);
  std::filesystem::remove(case_path);
}
#endif
