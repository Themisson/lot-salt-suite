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
constexpr const char* kBuz67dSigmaThetaStaticCasePath =
    "cases/validation/buz67d_pkn_legacy_sigma_theta_static.yaml";
constexpr const char* kBuz67dComplianceCasePath =
    "cases/validation/buz67d_pkn_legacy_compliance.yaml";
constexpr const char* kBuz67dNextStepSinkCasePath =
    "cases/validation/buz67d_pkn_legacy_compliance_next_step_sink.yaml";

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
  REQUIRE(result.time_series_s.size() ==
          result.sink_deferred_this_step_series.size());
  REQUIRE(result.time_series_s.size() ==
          result.sink_active_this_step_series.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiated_before_step_series.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiated_after_step_series.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_started_this_step_series.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_sink_applied_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.leakoff_sink_applied_series_m3.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiation_pressure_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiation_sigma_theta_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.fracture_initiation_margin_series_Pa.size());
  REQUIRE(result.time_series_s.size() ==
          result.sigma_theta_lookup_time_series_s.size());
  REQUIRE(result.time_series_s.size() == result.fracture_initiated_series.size());

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
    CHECK(std::isfinite(result.fracture_sink_applied_series_m3[i]));
    CHECK(std::isfinite(result.leakoff_sink_applied_series_m3[i]));
    CHECK(std::isfinite(result.fracture_initiation_pressure_series_Pa[i]));
    CHECK(std::isfinite(result.fracture_initiation_sigma_theta_series_Pa[i]));
    CHECK(std::isfinite(result.fracture_initiation_margin_series_Pa[i]));
    CHECK(std::isfinite(result.sigma_theta_lookup_time_series_s[i]));
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

std::size_t single_started_step_index(const lss::lot::PknResult& result) {
  std::size_t found = result.time_series_s.size();
  for (std::size_t i = 0; i < result.fracture_started_this_step_series.size(); ++i) {
    if (result.fracture_started_this_step_series[i] != 0) {
      REQUIRE(found == result.time_series_s.size());
      found = i;
    }
  }
  REQUIRE(found < result.time_series_s.size());
  return found;
}

}  // namespace

TEST_CASE("PknRunner executes minimal LOT PKN case") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.mode == "lot-pkn");
  CHECK(data.lot.pressure_model == "pkn_direct");
  CHECK(data.lot.fracture_sink_timing == "same_step");
  CHECK(run.input.pressure_model == lss::lot::PknPressureModel::PknDirect);
  CHECK(run.input.sink_timing == lss::lot::FractureSinkTiming::SameStep);
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
  CHECK(data.lot.fracture_sink_timing == "same_step");
  CHECK(run.input.pressure_model == lss::lot::PknPressureModel::VolumetricBalance);
  CHECK(run.input.sink_timing == lss::lot::FractureSinkTiming::SameStep);
  CHECK(run.input.annular_volume_m3 ==
        Catch::Approx(run.result.initial_annular_volume_m3));
  CHECK(run.input.fluid_compressibility_per_Pa == Catch::Approx(6.40e-10));
  CHECK(run.input.initial_pressure_Pa == Catch::Approx(26732215.17314985));
  REQUIRE(run.input.injection.phases.size() == 2);
  CHECK(run.input.injection.scheduled_total_time_s() == Catch::Approx(1320.0));
  CHECK(run.result.pressure_model == "volumetric_balance");
  CHECK(run.result.initial_pressure_Pa == Catch::Approx(run.input.initial_pressure_Pa));
  CHECK(run.result.wellbore_pressure_Pa >= run.input.initial_pressure_Pa);
  CHECK_FALSE(run.result.wellbore_pressure_series_Pa.empty());
  CHECK(run.result.time_series_s.back() == Catch::Approx(1320.0));
  CHECK(run.result.wellbore_pressure_series_Pa.back() ==
        Catch::Approx(run.result.wellbore_pressure_Pa));
}

TEST_CASE("PknRunner enables opt-in sigma theta static criterion") {
  const auto data = lss::io::parse_yaml(kBuz67dSigmaThetaStaticCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.lot.sigma_theta_fracture.enabled);
  CHECK(run.input.pressure_model == lss::lot::PknPressureModel::VolumetricBalance);
  CHECK(run.input.fracture_initiation ==
        lss::lot::FractureInitiationCriterion::SigmaThetaStatic);
  CHECK(run.input.sigma_theta_fracture.pressure_source == "wellbore_pressure_Pa");
  CHECK(run.input.sigma_theta_fracture.comparison == "legacy_algebra");
  CHECK(run.input.sigma_theta_fracture.sigma_theta_compression_positive_Pa ==
        Catch::Approx(67342521.84592447));
  CHECK(run.result.pressure_model == "volumetric_balance");
  CHECK(run.result.fracture_initiation_type == "sigma_theta_static");
  CHECK(run.result.fracture_initiation_layer_id == "legacy_layer_16");
  CHECK(run.result.fracture_initiation_sigma_theta_Pa ==
        Catch::Approx(67342521.84592447));
  CHECK(run.result.fracture_initiation_pressure_Pa >
        run.result.fracture_initiation_sigma_theta_Pa);
  CHECK(run.result.fracture_initiation_margin_Pa > 0.0);
}

TEST_CASE("PknRunner enables opt-in geometric compliance") {
  const auto data = lss::io::parse_yaml(kBuz67dComplianceCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.name == "buz67d_pkn_legacy_compliance");
  CHECK(data.lot.volumetric_compliance.enabled);
  CHECK(data.lot.volumetric_compliance.model == "constant_geometric");
  CHECK(run.input.pressure_model == lss::lot::PknPressureModel::VolumetricBalance);
  CHECK(run.input.volumetric_compliance.geometric_compressibility_per_Pa ==
        Catch::Approx(1.8571966938610005e-8));
  CHECK(run.result.compliance_model == "constant_geometric");
  CHECK(run.result.compliance_source == "DIAGNOSTIC_FROM_LEGACY_FIRST_STEP");
  CHECK(run.result.geometric_compressibility_per_Pa ==
        Catch::Approx(1.8571966938610005e-8));
  CHECK(run.result.effective_compressibility_per_Pa ==
        Catch::Approx(1.9211966938610006e-8));
  CHECK(run.result.sink_timing == "same_step");
  REQUIRE(run.result.balance_delta_pressure_series_Pa.size() > 1);
  CHECK(run.result.balance_delta_pressure_series_Pa[1] ==
        Catch::Approx(1845417.2017930523).epsilon(1.0e-6));
}

TEST_CASE("PknRunner defaults fracture sink timing to same step") {
  const auto data = lss::io::parse_yaml(kBuz67dComplianceCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(run.input.sink_timing == lss::lot::FractureSinkTiming::SameStep);
  CHECK(run.result.sink_timing == "same_step");
  const std::size_t opened = single_started_step_index(run.result);
  CHECK(run.result.sink_deferred_this_step_series[opened] == 0);
  CHECK(run.result.sink_active_this_step_series[opened] == 1);
  CHECK(run.result.fracture_initiated_before_step_series[opened] == 0);
  CHECK(run.result.fracture_initiated_after_step_series[opened] == 1);
  CHECK(run.result.fracture_sink_applied_series_m3[opened] ==
        Catch::Approx(run.result.balance_fracture_volume_increment_series_m3[opened]));
  CHECK(run.result.leakoff_sink_applied_series_m3[opened] ==
        Catch::Approx(run.result.balance_leakoff_volume_increment_series_m3[opened]));
  CHECK(run.result.fracture_sink_applied_series_m3[opened] +
            run.result.leakoff_sink_applied_series_m3[opened] >
        0.0);
}

TEST_CASE("PknRunner supports opt-in next-step fracture sink timing") {
  const auto data = lss::io::parse_yaml(kBuz67dNextStepSinkCasePath);
  const auto run = lss::lot::run_pkn_case(data);

  CHECK(data.name == "buz67d_pkn_legacy_compliance_next_step_sink");
  CHECK(data.lot.fracture_sink_timing == "next_step");
  CHECK(run.input.sink_timing == lss::lot::FractureSinkTiming::NextStep);
  CHECK(run.result.sink_timing == "next_step");
  const std::size_t opened = single_started_step_index(run.result);
  REQUIRE(opened + 1 < run.result.time_series_s.size());
  CHECK(run.result.fracture_started_this_step_series[opened] == 1);
  CHECK(run.result.sink_deferred_this_step_series[opened] == 1);
  CHECK(run.result.sink_active_this_step_series[opened] == 0);
  CHECK(run.result.fracture_sink_applied_series_m3[opened] == 0.0);
  CHECK(run.result.leakoff_sink_applied_series_m3[opened] == 0.0);
  CHECK(run.result.fracture_initiated_before_step_series[opened + 1] == 1);
  CHECK(run.result.sink_deferred_this_step_series[opened + 1] == 0);
  CHECK(run.result.sink_active_this_step_series[opened + 1] == 1);
  CHECK(run.result.fracture_sink_applied_series_m3[opened + 1] +
            run.result.leakoff_sink_applied_series_m3[opened + 1] >
        0.0);
  CHECK(run.result.fracture_initiation_time_s ==
        Catch::Approx(run.result.time_series_s[opened]));
}

TEST_CASE("CaseParser rejects unsupported fracture sink timing") {
  const auto path = std::filesystem::temp_directory_path() /
                    "lss_invalid_sink_timing_case.yaml";
  {
    std::ifstream in(kBuz67dComplianceCasePath);
    REQUIRE(in.good());
    std::ofstream out(path);
    REQUIRE(out.good());
    std::string line;
    while (std::getline(in, line)) {
      out << line << '\n';
      if (line == "        mapping_status: STATIC_FROM_LEGACY_AUDIT") {
        out << "    balance:\n";
        out << "      sink_timing: previous_step\n";
      }
    }
  }

  CHECK_THROWS_AS(lss::io::parse_yaml(path), std::runtime_error);
  std::filesystem::remove(path);
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
