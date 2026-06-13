#include <filesystem>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "io/ApbLotJsonOutputWriter.hpp"

namespace {

std::string read_file(const std::filesystem::path& path) {
  std::ifstream in(path);
  std::ostringstream buffer;
  buffer << in.rdbuf();
  return buffer.str();
}

lss::io::ApbLotOutputDocument document(const std::filesystem::path& output) {
  lss::io::ApbLotOutputDocument doc;
  doc.case_id = "case_apb";
  doc.input_file = "cases/case_apb.yaml";
  doc.output_file = output;
  doc.configuration.leakoff_coupling_mode = "volume_balance";
  doc.configuration.salt_displacement_mode = "pre_iterative";
  doc.time_series.push_back({0.0, 10.0, 1.0, 0.2, 0.01, -0.001, 3, true});
  doc.layers = {"salt_layer"};
  doc.annulars = {"A1"};
  doc.summary.max_pressure_Pa = 10.0;
  doc.summary.max_delta_pressure_Pa = 1.0;
  doc.summary.total_leakoff_volume_m3 = 0.01;
  doc.summary.final_time_s = 0.0;
  doc.caveats = {"diagnostic APB/LOT output contract"};
  return doc;
}

}  // namespace

TEST_CASE("APB LOT JSON output path is derived from input stem") {
  CHECK(lss::io::derive_apb_lot_output_json_path("case.json").string() ==
        "case_out.json");
  CHECK(lss::io::derive_apb_lot_output_json_path("case.yaml").string() ==
        "case_out.json");
  CHECK(lss::io::derive_apb_lot_output_json_path("case.dat").string() ==
        "case_out.json");
}

TEST_CASE("APB LOT JSON output path preserves directory") {
  const auto path =
      lss::io::derive_apb_lot_output_json_path("cases/validation/case_apb.yaml");
  CHECK(path.parent_path().string() == std::filesystem::path("cases/validation").string());
  CHECK(path.filename().string() == "case_apb_out.json");
}

TEST_CASE("APB LOT explicit output path overrides derived output") {
  const auto output = lss::io::resolve_apb_lot_output_json_path(
      "cases/case_apb.yaml", std::filesystem::path("out/custom.json"));
  CHECK(output == std::filesystem::path("out/custom.json"));
}

TEST_CASE("APB LOT JSON writer emits parseable contract sections") {
  const auto output_dir =
      std::filesystem::temp_directory_path() / "lss_apb_lot_json_writer";
  std::filesystem::remove_all(output_dir);
  const auto output = output_dir / "case_apb_out.json";

  lss::io::write_apb_lot_output_json(document(output));

  REQUIRE(std::filesystem::exists(output));
  const std::string json = read_file(output);
  CHECK(json.find("\"metadata\"") != std::string::npos);
  CHECK(json.find("\"schema_version\": \"apb_lot_output_v1\"") !=
        std::string::npos);
  CHECK(json.find("\"configuration\"") != std::string::npos);
  CHECK(json.find("\"time_series\"") != std::string::npos);
  CHECK(json.find("\"leakoff_coupling_mode\": \"volume_balance\"") !=
        std::string::npos);
  CHECK(json.find("\"salt_displacement_mode\": \"pre_iterative\"") !=
        std::string::npos);
  CHECK(json.find("\"summary\"") != std::string::npos);
  CHECK(json.find("\"caveats\"") != std::string::npos);

  std::filesystem::remove_all(output_dir);
}

TEST_CASE("APB LOT JSON writer accepts metadata-only streaming-style document") {
  const auto output_dir =
      std::filesystem::temp_directory_path() / "lss_apb_lot_json_writer_empty";
  std::filesystem::remove_all(output_dir);
  auto doc = document(output_dir / "case_apb_out.json");
  doc.time_series.clear();
  doc.summary = {};

  lss::io::write_apb_lot_output_json(doc);

  const std::string json = read_file(doc.output_file);
  CHECK(json.find("\"time_series\": [") != std::string::npos);
  CHECK(json.find("\"max_pressure_Pa\": null") != std::string::npos);

  std::filesystem::remove_all(output_dir);
}

TEST_CASE("APB LOT JSON writer rejects non-finite values") {
  auto doc = document(std::filesystem::temp_directory_path() /
                      "lss_apb_lot_json_writer_bad" / "case_apb_out.json");
  doc.time_series.front().pressure_Pa =
      std::numeric_limits<double>::quiet_NaN();

  CHECK_THROWS_AS(lss::io::write_apb_lot_output_json(doc), std::runtime_error);
}
