#pragma once

#include <string>
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
  std::string pressure_model = "pkn_direct";
  double initial_pressure_Pa = 0.0;
  double wellbore_pressure_Pa = 0.0;
  double fluid_compressibility_per_Pa = 0.0;
  double balance_delta_pressure_Pa = 0.0;
  double balance_effective_volume_increment_m3 = 0.0;
  double balance_injected_volume_increment_m3 = 0.0;
  double balance_fracture_volume_increment_m3 = 0.0;
  double balance_leakoff_volume_increment_m3 = 0.0;
  double initial_annular_volume_per_radian_m3 = 0.0;
  double initial_annular_volume_m3 = 0.0;
  double annular_outer_radius_m = 0.0;
  double annular_inner_radius_m = 0.0;
  double annular_length_m = 0.0;
  std::string annular_volume_convention;
  std::string annular_volume_source;

  // Backward-compatible aliases for early Fase 6.2 tests.
  double fracture_width_m = 0.0;
  double fracture_length_m = 0.0;
  double volume_m3 = 0.0;

  std::vector<double> time_series_s;
  std::vector<double> injected_volume_series_m3;
  std::vector<double> fracture_length_series_m;
  std::vector<double> fracture_width_series_m;
  std::vector<double> net_pressure_series_Pa;
  std::vector<double> initial_pressure_series_Pa;
  std::vector<double> leakoff_volume_series_m3;
  std::vector<double> fracture_volume_series_m3;
  std::vector<double> wellbore_pressure_series_Pa;
  std::vector<double> balance_delta_pressure_series_Pa;
  std::vector<double> balance_effective_volume_increment_series_m3;
  std::vector<double> balance_injected_volume_increment_series_m3;
  std::vector<double> balance_fracture_volume_increment_series_m3;
  std::vector<double> balance_leakoff_volume_increment_series_m3;
};

}  // namespace lss::lot
