#pragma once

#include <filesystem>
#include <string>
#include <vector>

#include "coupling/LotSaltSigmaThetaDriver.hpp"

namespace lss::coupling {

struct LotSaltSigmaThetaExportScenario {
  std::string scenario_id;
  std::string scenario_label;
  LotSaltSigmaThetaDriverResult result;
};

struct LotSaltSigmaThetaExportOptions {
  std::string case_id;
  std::string input_case;
  std::filesystem::path output_dir;
  std::vector<std::string> caveats;
};

struct LotSaltSigmaThetaExportResult {
  std::filesystem::path points_csv;
  std::filesystem::path summary_csv;
  std::filesystem::path metadata_json;
  bool valid = false;
};

// Experimental opt-in writer for sigma-theta diagnostics. It is intentionally
// independent from lot-sim runtime output and is not a ResultWriter extension.
[[nodiscard]] LotSaltSigmaThetaExportResult
write_lot_salt_sigma_theta_diagnostics(
    const LotSaltSigmaThetaExportOptions& options,
    const std::vector<LotSaltSigmaThetaExportScenario>& scenarios);

}  // namespace lss::coupling
