#include <filesystem>
#include <fstream>
#include <sstream>
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
                 "fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa") == 0);
  CHECK(json.find("\"validation_status\": \"synthetic_modern_no_legacy_regression\"") !=
        std::string::npos);
  CHECK(json.find("No numerical regression against legacy was performed.") !=
        std::string::npos);
  CHECK(json.find("R09 remains blocker for legacy comparison.") != std::string::npos);

  std::filesystem::remove_all(output_dir);
}
