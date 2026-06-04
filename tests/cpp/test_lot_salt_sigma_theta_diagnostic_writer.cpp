#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <filesystem>
#include <fstream>
#include <algorithm>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "coupling/LotSaltSigmaThetaDiagnosticWriter.hpp"

namespace {

std::filesystem::path temp_output_dir(const std::string& name) {
  const auto path = std::filesystem::temp_directory_path() /
                    ("lss_sigma_theta_writer_" + name);
  std::filesystem::remove_all(path);
  return path;
}

std::string read_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  REQUIRE(in);
  std::ostringstream buffer;
  buffer << in.rdbuf();
  return buffer.str();
}

std::size_t line_count(const std::string& text) {
  return static_cast<std::size_t>(
      std::count(text.begin(), text.end(), '\n'));
}

lss::coupling::LotSaltSigmaThetaDiagnosticPoint make_point(
    lss::coupling::SigmaThetaHoopState state,
    double sigma_theta_compression_positive_Pa,
    double margin_Pa,
    bool opened,
    int gp_id,
    double time_s,
    double pressure_Pa) {
  lss::coupling::LotSaltSigmaThetaDiagnosticPoint point;
  point.breakdown.layer_id = "salt";
  point.breakdown.influence_depth_m = 3000.0 + gp_id;
  point.breakdown.time_s = time_s;
  point.breakdown.pressure_Pa = pressure_Pa;
  point.breakdown.sigma_theta_compression_positive_Pa =
      sigma_theta_compression_positive_Pa;
  point.breakdown.margin_Pa = margin_Pa;
  point.breakdown.hoop_state = state;
  point.breakdown.tensile_hoop_state =
      state == lss::coupling::SigmaThetaHoopState::Tensile;
  point.breakdown.legacy_algebra_opened = opened && gp_id == 0;
  point.breakdown.opened = opened;
  point.breakdown.caveat = "experimental snapshot";

  point.pressure_map.wall_pressure_Pa = pressure_Pa;
  point.pressure_map.method =
      lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
  point.pressure_map.method_label = "hydrostatic_plus_net_pressure";
  point.pressure_map.physically_absolute = true;

  point.wall_stress_gp_id = gp_id;
  point.wall_stress_element_id = 10 + gp_id;
  point.wall_stress_local_gp_id = gp_id % 2;
  point.wall_stress_r_m = 0.1556;
  point.wall_stress_z_m = 10.0 * gp_id;
  point.wall_stress_depth_m = 3000.0 + gp_id;
  point.mean_stress_Pa = -1.0e6 * (gp_id + 1);
  point.j2_Pa2 = 2.0e12 * (gp_id + 1);
  point.von_mises_effective_stress_Pa = 3.0e6 * (gp_id + 1);
  return point;
}

lss::coupling::LotSaltSigmaThetaDriverResult make_driver_result() {
  lss::coupling::LotSaltSigmaThetaDriverResult result;
  result.valid = true;
  result.caveat = "driver is experimental";

  result.pkn_run.result.time_series_s = {0.0, 10.0};
  result.pkn_run.result.net_pressure_series_Pa = {1.0e6, 2.0e6};

  result.coupling_config.pressure_map_method =
      lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
  result.coupling_config.hydrostatic_pressure_Pa = 3.0e6;
  result.coupling_config.surface_pressure_Pa = 1.0e5;
  result.coupling_config.absolute_wellbore_pressure_Pa = 0.0;

  result.wall_stress.valid = true;
  result.wall_stress.wall_samples.resize(2);

  result.diagnostic.valid = true;
  result.diagnostic.pressure_source =
      "LotSaltPressureMap:hydrostatic_plus_net_pressure";
  result.diagnostic.stress_source = "SaltWallStressDiagnostics snapshot";
  result.diagnostic.points = {
      make_point(lss::coupling::SigmaThetaHoopState::Tensile, -1.0e6,
                 -2.0e6, false, 0, 0.0, 4.1e6),
      make_point(lss::coupling::SigmaThetaHoopState::Neutral, 0.0, -1.0e6,
                 false, 1, 0.0, 4.1e6),
      make_point(lss::coupling::SigmaThetaHoopState::Compressive, 2.0e6,
                 5.0e5, true, 0, 10.0, 5.1e6),
      make_point(lss::coupling::SigmaThetaHoopState::Compressive, 3.0e6,
                 1.0e6, false, 1, 10.0, 5.1e6),
  };
  result.diagnostic.any_opened = true;
  return result;
}

lss::coupling::LotSaltSigmaThetaExportOptions make_options(
    const std::filesystem::path& output_dir) {
  lss::coupling::LotSaltSigmaThetaExportOptions options;
  options.case_id = "case_minimal";
  options.input_case = "cases/validation/lot_pkn_minimal.yaml";
  options.output_dir = output_dir;
  options.caveats = {"experimental opt-in writer",
                     "not an official lot-sim runtime output"};
  return options;
}

lss::coupling::LotSaltSigmaThetaExportScenario make_scenario(
    std::string id = "scenario_a",
    std::string label = "Hydrostatic scenario") {
  lss::coupling::LotSaltSigmaThetaExportScenario scenario;
  scenario.scenario_id = std::move(id);
  scenario.scenario_label = std::move(label);
  scenario.result = make_driver_result();
  return scenario;
}

}  // namespace

TEST_CASE("LotSaltSigmaThetaDiagnosticWriter writes CSV and JSON files",
          "[coupling][sigma_theta][writer]") {
  const auto output_dir = temp_output_dir("basic");

  const auto exported =
      lss::coupling::write_lot_salt_sigma_theta_diagnostics(
          make_options(output_dir), {make_scenario()});

  CHECK(exported.valid);
  CHECK(exported.points_csv == output_dir / "points.csv");
  CHECK(exported.summary_csv == output_dir / "summary.csv");
  CHECK(exported.metadata_json == output_dir / "metadata.json");
  CHECK(std::filesystem::exists(exported.points_csv));
  CHECK(std::filesystem::exists(exported.summary_csv));
  CHECK(std::filesystem::exists(exported.metadata_json));
}

TEST_CASE("LotSaltSigmaThetaDiagnosticWriter points CSV has stable columns",
          "[coupling][sigma_theta][writer]") {
  const auto output_dir = temp_output_dir("points");
  const auto exported =
      lss::coupling::write_lot_salt_sigma_theta_diagnostics(
          make_options(output_dir), {make_scenario()});

  const std::string points = read_file(exported.points_csv);
  CHECK(points.find("case_id,scenario_id,scenario_label,step_index,time_s,"
                    "sample_index,layer_id,gp_id,element_id,local_gp_id,r_m,"
                    "z_m,depth_m,pressure_source,stress_source,"
                    "pressure_map_method,pressure_map_label,"
                    "wall_pressure_Pa,net_pressure_Pa,"
                    "hydrostatic_pressure_Pa,surface_pressure_Pa,"
                    "absolute_wellbore_pressure_Pa,"
                    "sigma_theta_compression_positive_Pa,hoop_state,"
                    "margin_Pa,opened,legacy_algebra_opened,"
                    "tensile_hoop_state,mean_stress_Pa,j2_Pa2,"
                    "von_mises_effective_stress_Pa,caveat") == 0);
  CHECK(line_count(points) == 5);
  CHECK(points.find("\"case_minimal\",\"scenario_a\","
                    "\"Hydrostatic scenario\",0,0,0") != std::string::npos);
  CHECK(points.find("\"case_minimal\",\"scenario_a\","
                    "\"Hydrostatic scenario\",1,10,1") !=
        std::string::npos);
  CHECK(points.find("\"hydrostatic_plus_net_pressure\"") !=
        std::string::npos);
  CHECK(points.find("\"compressive\"") != std::string::npos);
  CHECK(points.find("true,true,false") != std::string::npos);
}

TEST_CASE("LotSaltSigmaThetaDiagnosticWriter summary aggregates scenarios",
          "[coupling][sigma_theta][writer]") {
  const auto output_dir = temp_output_dir("summary");
  const auto exported =
      lss::coupling::write_lot_salt_sigma_theta_diagnostics(
          make_options(output_dir), {make_scenario()});

  const std::string summary = read_file(exported.summary_csv);
  CHECK(summary.find("case_id,scenario_id,scenario_label,n_points,"
                     "n_compressive,n_neutral,n_tensile,"
                     "min_sigma_theta_compression_positive_Pa,"
                     "max_sigma_theta_compression_positive_Pa,min_margin_Pa,"
                     "max_margin_Pa,any_opened,any_legacy_algebra_opened,"
                     "first_open_time_s,first_open_pressure_Pa,"
                     "first_open_layer_id") == 0);
  CHECK(line_count(summary) == 2);
  CHECK(summary.find("\"case_minimal\",\"scenario_a\","
                     "\"Hydrostatic scenario\",4,2,1,1") !=
        std::string::npos);
  CHECK(summary.find("-1000000,3000000,-2000000,1000000,true,true,10,"
                     "5100000,\"salt\"") != std::string::npos);
}

TEST_CASE("LotSaltSigmaThetaDiagnosticWriter metadata records provenance",
          "[coupling][sigma_theta][writer]") {
  const auto output_dir = temp_output_dir("metadata");
  const auto exported =
      lss::coupling::write_lot_salt_sigma_theta_diagnostics(
          make_options(output_dir), {make_scenario()});

  const std::string metadata = read_file(exported.metadata_json);
  CHECK(metadata.find("\"case_id\": \"case_minimal\"") != std::string::npos);
  CHECK(metadata.find("\"generated_by\": \"lot-salt-suite\"") !=
        std::string::npos);
  CHECK(metadata.find("\"phase\": \"10.9B\"") != std::string::npos);
  CHECK(metadata.find("\"input_case\": "
                      "\"cases/validation/lot_pkn_minimal.yaml\"") !=
        std::string::npos);
  CHECK(metadata.find("\"points_csv\": \"points.csv\"") !=
        std::string::npos);
  CHECK(metadata.find("\"summary_csv\": \"summary.csv\"") !=
        std::string::npos);
  CHECK(metadata.find("\"id\": \"scenario_a\"") != std::string::npos);
  CHECK(metadata.find("\"label\": \"Hydrostatic scenario\"") !=
        std::string::npos);
  CHECK(metadata.find("\"n_points\": 4") != std::string::npos);
  CHECK(metadata.find("\"experimental opt-in writer\"") !=
        std::string::npos);
}

TEST_CASE("LotSaltSigmaThetaDiagnosticWriter supports multiple scenarios",
          "[coupling][sigma_theta][writer]") {
  const auto output_dir = temp_output_dir("multi");
  const auto exported =
      lss::coupling::write_lot_salt_sigma_theta_diagnostics(
          make_options(output_dir),
          {make_scenario("no_geostatic", "No geostatic"),
           make_scenario("lithostatic", "Lithostatic")});

  const std::string points = read_file(exported.points_csv);
  const std::string summary = read_file(exported.summary_csv);
  const std::string metadata = read_file(exported.metadata_json);

  CHECK(line_count(points) == 9);
  CHECK(line_count(summary) == 3);
  CHECK(points.find("\"no_geostatic\"") != std::string::npos);
  CHECK(points.find("\"lithostatic\"") != std::string::npos);
  CHECK(metadata.find("\"id\": \"no_geostatic\"") != std::string::npos);
  CHECK(metadata.find("\"id\": \"lithostatic\"") != std::string::npos);
}

TEST_CASE("LotSaltSigmaThetaDiagnosticWriter rejects invalid inputs",
          "[coupling][sigma_theta][writer]") {
  const auto output_dir = temp_output_dir("invalid");

  auto options = make_options(output_dir);
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {}),
                  std::invalid_argument);

  options.case_id.clear();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {make_scenario()}),
                  std::invalid_argument);

  options = make_options(output_dir);
  options.output_dir = std::filesystem::path{};
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {make_scenario()}),
                  std::invalid_argument);

  options = make_options(output_dir);
  auto scenario = make_scenario();
  scenario.scenario_label.clear();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  options = make_options(output_dir);
  scenario = make_scenario();
  scenario.scenario_id.clear();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.valid = false;
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.diagnostic.valid = false;
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.wall_stress.valid = false;
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.pkn_run.result.time_series_s.clear();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.pkn_run.result.net_pressure_series_Pa.clear();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.pkn_run.result.net_pressure_series_Pa.push_back(3.0e6);
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.wall_stress.wall_samples.clear();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);

  scenario = make_scenario();
  scenario.result.diagnostic.points.pop_back();
  CHECK_THROWS_AS(lss::coupling::write_lot_salt_sigma_theta_diagnostics(
                      options, {scenario}),
                  std::invalid_argument);
}
