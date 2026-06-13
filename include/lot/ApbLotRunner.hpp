#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include "core/types.hpp"

namespace lss::lot {

struct ApbLotRunnerInput {
  std::string case_id;
  std::filesystem::path input_file;
  std::filesystem::path output_directory;
  std::optional<std::filesystem::path> explicit_output_file;
  std::string output_format = "json";
  std::string leakoff_coupling_mode = "volume_balance";
  std::string salt_displacement_mode = "pre_iterative";
  int layer_count = 0;
  int annular_count = 0;
  double initial_pressure_Pa = 0.0;
  double dt_s = 0.0;
  double injected_volume_m3 = 0.0;
  std::vector<std::string> layers;
  std::vector<std::string> annulars;
};

struct ApbLotRunnerResult {
  std::string run_status;
  bool executed = false;
  bool json_output_generated = false;
  bool volume_balance_exercised = false;
  bool pre_iterative_exercised = false;
  bool legacy_modes_preserved = false;
  bool pkn_behavior_changed = false;
  bool buz29_penny_executed = false;
  std::filesystem::path output_file;
  std::vector<std::string> caveats;
};

[[nodiscard]] ApbLotRunnerInput make_apb_lot_runner_input(
    const lss::core::CaseData& data,
    const std::filesystem::path& input_file,
    const std::filesystem::path& output_directory);

[[nodiscard]] ApbLotRunnerResult run_apb_lot_case(
    const ApbLotRunnerInput& input);

}  // namespace lss::lot
