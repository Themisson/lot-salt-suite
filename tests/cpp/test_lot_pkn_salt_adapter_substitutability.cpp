#include <cstddef>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"
#include "io/ResultWriter.hpp"
#include "lot/PknRunner.hpp"
#include "salt/SaltCreepInterface.hpp"
#include "salt/SaltCreepSaltcreepAdapter.hpp"

namespace {

constexpr const char* kPknMinimalCasePath = "cases/validation/lot_pkn_minimal.yaml";
constexpr const char* kPknLeakoffCasePath = "cases/validation/lot_pkn_with_leakoff.yaml";

class SpySaltCreepInterface final : public lss::salt::SaltCreepInterface {
 public:
  [[nodiscard]] bool is_available() const override { return true; }

  [[nodiscard]] lss::salt::SaltCreepResponse evaluate_wall_response(
      const lss::salt::SaltCreepQuery& query) const override {
    (void)query;
    ++call_count_;
    return {};
  }

  [[nodiscard]] int call_count() const { return call_count_; }

 private:
  mutable int call_count_ = 0;
};

struct PknArtifacts {
  lss::lot::PknRun run;
  std::string result_json;
  std::string timeseries_csv;
};

std::string read_text_file(const std::filesystem::path& path) {
  std::ifstream in(path, std::ios::binary);
  REQUIRE(in);
  return {std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>()};
}

void compare_vector_exact(const std::vector<double>& lhs,
                          const std::vector<double>& rhs) {
  REQUIRE(lhs.size() == rhs.size());
  for (std::size_t i = 0; i < lhs.size(); ++i) {
    CHECK(lhs[i] == rhs[i]);
  }
}

void compare_pkn_result_exact(const lss::lot::PknResult& lhs,
                              const lss::lot::PknResult& rhs) {
  CHECK(lhs.time_s == rhs.time_s);
  CHECK(lhs.injected_volume_m3 == rhs.injected_volume_m3);
  CHECK(lhs.length_m == rhs.length_m);
  CHECK(lhs.width_m == rhs.width_m);
  CHECK(lhs.fracture_volume_m3 == rhs.fracture_volume_m3);
  CHECK(lhs.leakoff_volume_m3 == rhs.leakoff_volume_m3);
  CHECK(lhs.net_pressure_Pa == rhs.net_pressure_Pa);

  compare_vector_exact(lhs.time_series_s, rhs.time_series_s);
  compare_vector_exact(lhs.injected_volume_series_m3,
                       rhs.injected_volume_series_m3);
  compare_vector_exact(lhs.fracture_length_series_m, rhs.fracture_length_series_m);
  compare_vector_exact(lhs.fracture_width_series_m, rhs.fracture_width_series_m);
  compare_vector_exact(lhs.fracture_volume_series_m3,
                       rhs.fracture_volume_series_m3);
  compare_vector_exact(lhs.leakoff_volume_series_m3, rhs.leakoff_volume_series_m3);
  compare_vector_exact(lhs.net_pressure_series_Pa, rhs.net_pressure_series_Pa);
}

PknArtifacts run_and_write(const lss::core::CaseData& data,
                           const std::filesystem::path& output_dir) {
  std::filesystem::remove_all(output_dir);

  PknArtifacts artifacts;
  artifacts.run = lss::lot::run_pkn_case(data);
  lss::io::write_pkn_result(output_dir, data.name, artifacts.run.result);
  artifacts.result_json = read_text_file(output_dir / "result.json");
  artifacts.timeseries_csv = read_text_file(output_dir / "timeseries.csv");
  return artifacts;
}

void check_substitutability_for_case(const char* case_path) {
  const auto data = lss::io::parse_yaml(case_path);
  REQUIRE(data.mode == "lot-pkn");

  const lss::salt::NullSaltCreepInterface null_salt;
  const SpySaltCreepInterface spy_salt;
  const lss::salt::SaltCreepSaltcreepAdapter saltcreep_adapter;

  REQUIRE_FALSE(null_salt.is_available());
  REQUIRE(spy_salt.is_available());
  REQUIRE(saltcreep_adapter.is_available());
  REQUIRE(saltcreep_adapter.backend_build_count() == 0);
  REQUIRE(saltcreep_adapter.state().step_count() == 0);

  const auto root = std::filesystem::temp_directory_path() /
                    "lss_lot_pkn_salt_adapter_substitutability";
  const auto reference_dir = root / "null_salt_reference";
  const auto adapter_dir = root / "adapter_available_not_called";

  const auto reference = run_and_write(data, reference_dir);
  const auto with_adapter_present = run_and_write(data, adapter_dir);

  compare_pkn_result_exact(reference.run.result, with_adapter_present.run.result);

  CHECK(reference.result_json == with_adapter_present.result_json);
  CHECK(reference.timeseries_csv == with_adapter_present.timeseries_csv);

  CHECK(spy_salt.call_count() == 0);
  CHECK(saltcreep_adapter.backend_build_count() == 0);
  CHECK(saltcreep_adapter.state().step_count() == 0);

  std::filesystem::remove_all(root);
}

}  // namespace

TEST_CASE("LOT PKN result is identical with null salt or idle saltcreep adapter") {
  check_substitutability_for_case(kPknMinimalCasePath);
}

TEST_CASE("LOT PKN leakoff result is identical with null salt or idle saltcreep adapter") {
  check_substitutability_for_case(kPknLeakoffCasePath);
}
