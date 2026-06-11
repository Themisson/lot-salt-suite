#include <filesystem>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "io/ResultWriter.hpp"
#include "lot/PknRunner.hpp"

namespace {

std::string read_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  std::ostringstream buffer;
  buffer << in.rdbuf();
  return buffer.str();
}

}  // namespace

TEST_CASE("ResultWriter creates PKN CSV and JSON outputs") {
  const auto data = lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");
  const auto run = lss::lot::run_pkn_case(data);
  const auto output_dir = std::filesystem::temp_directory_path() / "lss_result_writer_pkn";
  std::filesystem::remove_all(output_dir);

  lss::io::write_pkn_result(output_dir, data.name, run.result);

  const auto csv_path = output_dir / "timeseries.csv";
  const auto json_path = output_dir / "result.json";
  REQUIRE(std::filesystem::exists(csv_path));
  REQUIRE(std::filesystem::exists(json_path));

  const std::string csv = read_file(csv_path);
  const std::string json = read_file(json_path);
  CHECK(csv.find("time_s,injected_volume_m3,fracture_length_m,fracture_width_m,"
                 "fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa,"
                 "initial_pressure_Pa,wellbore_pressure_Pa,balance_delta_pressure_Pa") == 0);
  CHECK(json.find("\"validation_status\": \"synthetic_modern_no_legacy_regression\"") !=
        std::string::npos);
  CHECK(json.find("No numerical regression against legacy was performed.") !=
        std::string::npos);
  CHECK(json.find("R09 remains blocker for legacy comparison.") != std::string::npos);
  CHECK(json.find("\"initial_annular_volume_per_radian_m3\"") !=
        std::string::npos);
  CHECK(json.find("\"initial_annular_volume_m3\"") != std::string::npos);
  CHECK(json.find("\"annular_volume_convention\"") != std::string::npos);
  CHECK(json.find("\"pressure_model\": \"pkn_direct\"") != std::string::npos);
  CHECK(json.find("\"initial_pressure_Pa\"") != std::string::npos);
  CHECK(json.find("\"final_wellbore_pressure_Pa\"") != std::string::npos);
  CHECK(json.find("\"geometric_compressibility_per_Pa\"") != std::string::npos);
  CHECK(json.find("\"effective_compressibility_per_Pa\"") != std::string::npos);
  CHECK(json.find("\"compliance_model\": \"none\"") != std::string::npos);
  CHECK(json.find("\"mechanical_compliance_status\": \"none\"") !=
        std::string::npos);
  CHECK(json.find("\"final_balance_effective_volume_increment_m3\"") !=
        std::string::npos);
  CHECK(csv.find("fracture_initiated,fracture_initiation_pressure_Pa,"
                 "fracture_initiation_sigma_theta_Pa,"
                 "fracture_initiation_margin_Pa,"
                 "sigma_theta_provider_type,"
                 "sigma_theta_source,"
                 "sigma_theta_lookup_time_s,"
                 "sigma_theta_layer_id,"
                 "sigma_theta_mapping_status,"
                 "fluid_compressibility_1_Pa,"
                 "geometric_compressibility_1_Pa,"
                 "effective_compressibility_1_Pa,"
                 "mechanical_compliance_status") != std::string::npos);
  CHECK(json.find("\"fracture_initiation_type\": \"constant_pressure\"") !=
        std::string::npos);
  CHECK(json.find("\"fracture_initiation_pressure_Pa\"") != std::string::npos);
  CHECK(json.find("\"sigma_theta_provider_type\": \"none\"") !=
        std::string::npos);
  CHECK(json.find("\"sigma_theta_lookup_time_s\"") != std::string::npos);

  std::filesystem::remove_all(output_dir);
}

TEST_CASE("ResultWriter rejects non-finite PKN values") {
  const auto data = lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");
  auto run = lss::lot::run_pkn_case(data);
  run.result.net_pressure_series_Pa.front() =
      std::numeric_limits<double>::quiet_NaN();
  const auto output_dir =
      std::filesystem::temp_directory_path() / "lss_result_writer_nonfinite";
  std::filesystem::remove_all(output_dir);

  CHECK_THROWS_AS(lss::io::write_pkn_result(output_dir, data.name, run.result),
                  std::runtime_error);

  std::filesystem::remove_all(output_dir);
}
