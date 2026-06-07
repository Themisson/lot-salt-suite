#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "lot/PknRunner.hpp"

#ifndef LSS_ENABLE_CLI_SUBPROCESS_TESTS
#define LSS_ENABLE_CLI_SUBPROCESS_TESTS 1
#endif

namespace {

constexpr const char* kPknMinimalCasePath = "cases/validation/lot_pkn_minimal.yaml";
constexpr const char* kPknLeakoffCasePath = "cases/validation/lot_pkn_with_leakoff.yaml";
constexpr const char* kBuz67dPknCasePath = "cases/lot_tese_migrated/buz67d_pkn.yaml";
constexpr const char* kBuz67dLegacyAlignedCasePath =
    "cases/validation/buz67d_pkn_legacy_aligned.yaml";

void check_finite_series(const lss::lot::PknResult& result) {
  REQUIRE_FALSE(result.time_series_s.empty());
  REQUIRE(result.time_series_s.size() == result.injected_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.fracture_length_series_m.size());
  REQUIRE(result.time_series_s.size() == result.fracture_width_series_m.size());
  REQUIRE(result.time_series_s.size() == result.fracture_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.leakoff_volume_series_m3.size());
  REQUIRE(result.time_series_s.size() == result.net_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() == result.wellbore_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_delta_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_effective_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_injected_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_fracture_volume_increment_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.balance_leakoff_volume_increment_series_m3.size());

  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    CHECK(std::isfinite(result.time_series_s[i]));
    CHECK(std::isfinite(result.injected_volume_series_m3[i]));
    CHECK(std::isfinite(result.fracture_length_series_m[i]));
    CHECK(std::isfinite(result.fracture_width_series_m[i]));
    CHECK(std::isfinite(result.fracture_volume_series_m3[i]));
    CHECK(std::isfinite(result.leakoff_volume_series_m3[i]));
    CHECK(std::isfinite(result.net_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.wellbore_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.balance_delta_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.balance_effective_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.balance_injected_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.balance_fracture_volume_increment_series_m3[i]));
    CHECK(std::isfinite(result.balance_leakoff_volume_increment_series_m3[i]));
  }
}

std::string quote(const std::filesystem::path& path) {
  return "\"" + path.string() + "\"";
}

std::filesystem::path lot_sim_executable() {
#ifdef LSS_LOT_SIM_EXECUTABLE
  // Set by CMake via $<TARGET_FILE:lot-sim>; resolves correctly for both
  // single-config (Ninja/Make) and multi-config (Visual Studio) generators.
  return std::filesystem::path(LSS_LOT_SIM_EXECUTABLE);
#else
  // Fallback: probe multi-config subdirs then single-config root.
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

}  // namespace

TEST_CASE("PknRunner executes minimal LOT PKN case") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.mode == "lot-pkn");
  CHECK(data.lot.pressure_model == "pkn_direct");
  CHECK(run.input.pressure_model == lss::lot::PknPressureModel::PknDirect);
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

TEST_CASE("PknRunner exports legacy-aligned annular volume with drill pipe") {
  const auto data = lss::io::parse_yaml(kBuz67dLegacyAlignedCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  const double outer_radius_m = 0.5 * 12.376 * 0.0254;
  const double inner_radius_m = 0.5 * 5.5 * 0.0254;
  const double length_m = 18.0;
  const double per_radian =
      0.5 * (outer_radius_m * outer_radius_m - inner_radius_m * inner_radius_m) *
      length_m;

  CHECK(run.result.annular_outer_radius_m == Catch::Approx(outer_radius_m));
  CHECK(run.result.annular_inner_radius_m == Catch::Approx(inner_radius_m));
  CHECK(run.result.annular_length_m == Catch::Approx(length_m));
  CHECK(run.result.initial_annular_volume_per_radian_m3 ==
        Catch::Approx(per_radian));
  CHECK(run.result.initial_annular_volume_m3 ==
        Catch::Approx(2.0 * 3.14159265358979323846 * per_radian));
  CHECK(run.result.annular_volume_convention ==
        "PER_RADIAN_INTERNAL_TOTAL_EXPORTED");
}

TEST_CASE("PknRunner enables opt-in volumetric balance for legacy-aligned case") {
  const auto data = lss::io::parse_yaml(kBuz67dLegacyAlignedCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.lot.pressure_model == "volumetric_balance");
  CHECK(run.input.pressure_model == lss::lot::PknPressureModel::VolumetricBalance);
  CHECK(run.input.annular_volume_m3 ==
        Catch::Approx(run.result.initial_annular_volume_m3));
  CHECK(run.input.fluid_compressibility_per_Pa == Catch::Approx(6.40e-10));
  CHECK(run.result.pressure_model == "volumetric_balance");
  CHECK(run.result.wellbore_pressure_Pa >= 0.0);
  CHECK_FALSE(run.result.wellbore_pressure_series_Pa.empty());
  CHECK(run.result.wellbore_pressure_series_Pa.back() ==
        Catch::Approx(run.result.wellbore_pressure_Pa));
}

#if LSS_ENABLE_CLI_SUBPROCESS_TESTS
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
#else
TEST_CASE("CLI subprocess tests disabled by CMake option", "[cli][disabled]") {
  SUCCEED("CLI subprocess tests disabled with LSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF");
}
#endif
