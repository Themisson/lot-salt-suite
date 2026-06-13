#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace lss::io {

struct ApbLotOutputConfiguration {
  std::string output_format = "json";
  std::string leakoff_coupling_mode = "volume_balance";
  std::string salt_displacement_mode = "pre_iterative";
  double axisymmetric_angle_rad = 1.0;
};

struct ApbLotOutputSample {
  double time_s = 0.0;
  double pressure_Pa = 0.0;
  double delta_pressure_Pa = 0.0;
  double dV_m3 = 0.0;
  double dV_leakoff_m3 = 0.0;
  double salt_displacement_m = 0.0;
  int iteration_count = 0;
  bool converged = true;
};

struct ApbLotOutputSummary {
  std::optional<double> max_pressure_Pa;
  std::optional<double> max_delta_pressure_Pa;
  std::optional<double> total_leakoff_volume_m3;
  std::optional<double> final_time_s;
};

struct ApbLotOutputDocument {
  std::string case_id;
  std::filesystem::path input_file;
  std::filesystem::path output_file;
  bool legacy_dat_available = true;
  ApbLotOutputConfiguration configuration;
  std::vector<ApbLotOutputSample> time_series;
  std::vector<std::string> layers;
  std::vector<std::string> annulars;
  ApbLotOutputSummary summary;
  std::vector<std::string> caveats;
};

[[nodiscard]] std::filesystem::path derive_apb_lot_output_json_path(
    const std::filesystem::path& input_path);

[[nodiscard]] std::filesystem::path resolve_apb_lot_output_json_path(
    const std::filesystem::path& input_path,
    const std::optional<std::filesystem::path>& explicit_output_path);

void write_apb_lot_output_json(const ApbLotOutputDocument& document);

}  // namespace lss::io
