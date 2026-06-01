#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "lot/PknRunner.hpp"

namespace {

constexpr const char* kPknMinimalCasePath = "cases/validation/lot_pkn_minimal.yaml";
constexpr const char* kPknLeakoffCasePath = "cases/validation/lot_pkn_with_leakoff.yaml";
constexpr const char* kBuz67dPknCasePath = "cases/lot_tese_migrated/buz67d_pkn.yaml";

void check_finite_series(const lss::lot::PknResult& result) {
  REQUIRE_FALSE(result.time_series_s.empty());
  REQUIRE(result.time_series_s.size() == result.injected_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.fracture_length_series_m.size());
  REQUIRE(result.time_series_s.size() == result.fracture_width_series_m.size());
  REQUIRE(result.time_series_s.size() == result.fracture_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.leakoff_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.net_pressure_series_Pa.size());

  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    CHECK(std::isfinite(result.time_series_s[i]));
    CHECK(std::isfinite(result.injected_volume_series_m3[i]));
    CHECK(std::isfinite(result.fracture_length_series_m[i]));
    CHECK(std::isfinite(result.fracture_width_series_m[i]));
    CHECK(std::isfinite(result.fracture_volume_series_m3[i]));
    CHECK(std::isfinite(result.leakoff_volume_series_m3[i]));
    CHECK(std::isfinite(result.net_pressure_series_Pa[i]));
  }
}

std::string quote(const std::filesystem::path& path) {
  return "\"" + path.string() + "\"";
}

std::filesystem::path lot_sim_executable() {
#ifdef _WIN32
  return std::filesystem::current_path() / "build" / "lot-sim.exe";
#else
  return std::filesystem::current_path() / "build" / "lot-sim";
#endif
}

std::string command_prefix() {
#ifdef _WIN32
  return "call " + quote(lot_sim_executable());
#else
  return quote(lot_sim_executable());
#endif
}

}  // namespace

TEST_CASE("PknRunner executes minimal LOT PKN case") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.mode == "lot-pkn");
  CHECK(run.input.fracture_height_m > 0.0);
  CHECK(run.input.fluid_viscosity_Pa_s > 0.0);
  CHECK(run.input.plane_strain_modulus_Pa > 0.0);
  CHECK(run.result.leakoff_volume_m3 == 0.0);
  check_finite_series(run.result);
}

TEST_CASE("PknRunner executes simplified leakoff LOT PKN case") {
  const auto data = lss::io::parse_yaml(kPknLeakoffCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(run.input.leakoff.enabled);
  CHECK(run.input.leakoff_coefficient_m_sqrt_s > 0.0);
  CHECK(run.result.leakoff_volume_m3 > 0.0);
  CHECK(run.result.fracture_volume_m3 <= run.result.injected_volume_m3);
  check_finite_series(run.result);
}

TEST_CASE("Migrated BUZ67D PKN case remains validation-only contract") {
  const auto data = lss::io::parse_yaml(kBuz67dPknCasePath);

  CHECK(data.name == "buz67d_pkn_migrated_contract");
  CHECK(data.mode == "lot-pkn");
  CHECK(data.legacy_source.find("LOT_Tese") != std::string::npos);
}

TEST_CASE("CLI run succeeds for minimal LOT PKN case") {
  const auto output_dir = std::filesystem::temp_directory_path() / "lss_cli_lot_pkn_minimal";
  std::filesystem::remove_all(output_dir);
  const std::string command = command_prefix() +
                              " run --case " + kPknMinimalCasePath +
                              " --mode lot-pkn --output " + quote(output_dir);
  CAPTURE(command);

  const int rc = std::system(command.c_str());

  CHECK(rc == 0);
  CHECK(std::filesystem::exists(output_dir / "result.json"));
  CHECK(std::filesystem::exists(output_dir / "timeseries.csv"));
  std::filesystem::remove_all(output_dir);
}

TEST_CASE("CLI run succeeds for simplified leakoff LOT PKN case") {
  const auto output_dir = std::filesystem::temp_directory_path() / "lss_cli_lot_pkn_leakoff";
  std::filesystem::remove_all(output_dir);
  const std::string command = command_prefix() +
                              " run --case " + kPknLeakoffCasePath +
                              " --mode lot-pkn --output " + quote(output_dir);
  CAPTURE(command);

  const int rc = std::system(command.c_str());

  CHECK(rc == 0);
  CHECK(std::filesystem::exists(output_dir / "result.json"));
  CHECK(std::filesystem::exists(output_dir / "timeseries.csv"));
  std::filesystem::remove_all(output_dir);
}
