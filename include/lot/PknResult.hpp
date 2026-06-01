#pragma once

#include <vector>

namespace lss::lot {

struct PknResult {
  double time_s = 0.0;
  double injected_volume_m3 = 0.0;
  double width_m = 0.0;
  double length_m = 0.0;
  double fracture_volume_m3 = 0.0;
  double leakoff_volume_m3 = 0.0;
  double net_pressure_Pa = 0.0;

  // Backward-compatible aliases for early Fase 6.2 tests.
  double fracture_width_m = 0.0;
  double fracture_length_m = 0.0;
  double volume_m3 = 0.0;

  std::vector<double> time_series_s;
  std::vector<double> injected_volume_series_m3;
  std::vector<double> fracture_length_series_m;
  std::vector<double> fracture_width_series_m;
  std::vector<double> net_pressure_series_Pa;
  std::vector<double> leakoff_volume_series_m3;
  std::vector<double> fracture_volume_series_m3;
};

}  // namespace lss::lot
