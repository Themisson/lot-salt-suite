#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "lot/ApbLotRunner.hpp"

namespace {

constexpr const char* kModernCase =
    "tests/fixtures/comparison/phase_apb_lot_real_runner/"
    "apb_lot_modern_controlled.yaml";
constexpr const char* kExplicitCase =
    "tests/fixtures/comparison/phase_apb_lot_real_runner/"
    "apb_lot_modern_explicit_output.yaml";
constexpr const char* kLegacyCase =
    "tests/fixtures/comparison/phase_apb_lot_real_runner/"
    "apb_lot_legacy_controlled.yaml";
constexpr const char* kInvalidCase =
    "tests/fixtures/comparison/phase_apb_lot_real_runner/"
    "apb_lot_invalid_mode.yaml";

std::string read_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  return {std::istreambuf_iterator<char>(in),
          std::istreambuf_iterator<char>()};
}

std::filesystem::path temp_dir(const std::string& name) {
  const auto path = std::filesystem::temp_directory_path() / name;
  std::filesystem::remove_all(path);
  std::filesystem::create_directories(path);
  return path;
}

}  // namespace

TEST_CASE("APB LOT runner writes controlled modern JSON output") {
  const auto output_dir = temp_dir("lss_apb_lot_runner_modern");
  const auto data = lss::io::parse_yaml(kModernCase);
  const auto input =
      lss::lot::make_apb_lot_runner_input(data, kModernCase, output_dir);

  const auto result = lss::lot::run_apb_lot_case(input);

  CHECK(result.run_status == "APB_LOT_REAL_CASE_RUNNER_IMPLEMENTED");
  CHECK(result.executed);
  CHECK(result.json_output_generated);
  CHECK(result.volume_balance_exercised);
  CHECK(result.pre_iterative_exercised);
  CHECK_FALSE(result.pkn_behavior_changed);
  CHECK_FALSE(result.buz29_penny_executed);
  REQUIRE(std::filesystem::exists(output_dir / "apb_lot_modern_controlled_out.json"));

  const auto json = read_file(output_dir / "apb_lot_modern_controlled_out.json");
  CHECK(json.find("\"time_series\"") != std::string::npos);
  CHECK(json.find("\"leakoff_coupling_mode\": \"volume_balance\"") !=
        std::string::npos);
  CHECK(json.find("\"salt_displacement_mode\": \"pre_iterative\"") !=
        std::string::npos);
  CHECK(json.find("\"dV_leakoff_m3\": 0.0015") != std::string::npos);
  CHECK(json.find("CONTROLLED_PRE_ITERATIVE_SALT_DISPLACEMENT") !=
        std::string::npos);

  std::filesystem::remove_all(output_dir);
}

TEST_CASE("APB LOT runner honors explicit output path") {
  const auto output_dir = temp_dir("lss_apb_lot_runner_explicit");
  const auto data = lss::io::parse_yaml(kExplicitCase);
  const auto input =
      lss::lot::make_apb_lot_runner_input(data, kExplicitCase, output_dir);

  const auto result = lss::lot::run_apb_lot_case(input);

  CHECK(result.json_output_generated);
  CHECK(result.output_file == output_dir / "custom/apb_lot_modern_explicit_out.json");
  CHECK(std::filesystem::exists(result.output_file));

  std::filesystem::remove_all(output_dir);
}

TEST_CASE("APB LOT runner preserves legacy DAT mode without JSON generation") {
  const auto output_dir = temp_dir("lss_apb_lot_runner_legacy");
  const auto data = lss::io::parse_yaml(kLegacyCase);
  const auto input =
      lss::lot::make_apb_lot_runner_input(data, kLegacyCase, output_dir);

  const auto result = lss::lot::run_apb_lot_case(input);

  CHECK(result.run_status == "APB_LOT_LEGACY_MODE_ACCEPTED");
  CHECK(result.executed);
  CHECK_FALSE(result.json_output_generated);
  CHECK(result.legacy_modes_preserved);
  CHECK_FALSE(std::filesystem::exists(output_dir / "apb_lot_legacy_controlled_out.json"));

  std::filesystem::remove_all(output_dir);
}

TEST_CASE("APB LOT parser rejects invalid modern mode") {
  CHECK_THROWS_AS(lss::io::parse_yaml(kInvalidCase), std::invalid_argument);
}

