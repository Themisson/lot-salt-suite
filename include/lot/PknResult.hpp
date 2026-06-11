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
  double geometric_compressibility_per_Pa = 0.0;
  double effective_compressibility_per_Pa = 0.0;
  std::string compliance_model = "none";
  std::string compliance_source;
  std::string mechanical_compliance_status = "none";
  double balance_delta_pressure_Pa = 0.0;
  double balance_effective_volume_increment_m3 = 0.0;
  double balance_injected_volume_increment_m3 = 0.0;
  double balance_fracture_volume_increment_m3 = 0.0;
  double balance_leakoff_volume_increment_m3 = 0.0;
  std::string sink_timing = "same_step";
  bool sink_deferred_this_step = false;
  bool sink_active_this_step = false;
  bool fracture_initiated_before_step = false;
  bool fracture_initiated_after_step = false;
  bool fracture_started_this_step = false;
  double fracture_sink_applied_m3 = 0.0;
  double leakoff_sink_applied_m3 = 0.0;
  bool fracture_initiated = false;
  double fracture_initiation_time_s = 0.0;
  double fracture_initiation_pressure_Pa = 0.0;
  double fracture_initiation_sigma_theta_Pa = 0.0;
  double fracture_initiation_margin_Pa = 0.0;
  std::string fracture_initiation_type = "constant_pressure";
  std::string fracture_initiation_layer_id;
  double fracture_initiation_depth_m = 0.0;
  std::string fracture_initiation_source;
  std::string sigma_theta_provider_type = "none";
  std::string sigma_theta_source;
  double sigma_theta_lookup_time_s = 0.0;
  std::string sigma_theta_layer_id;
  std::string sigma_theta_mapping_status;
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
  std::vector<int> sink_deferred_this_step_series;
  std::vector<int> sink_active_this_step_series;
  std::vector<int> fracture_initiated_before_step_series;
  std::vector<int> fracture_initiated_after_step_series;
  std::vector<int> fracture_started_this_step_series;
  std::vector<double> fracture_sink_applied_series_m3;
  std::vector<double> leakoff_sink_applied_series_m3;
  std::vector<double> fracture_initiation_pressure_series_Pa;
  std::vector<double> fracture_initiation_sigma_theta_series_Pa;
  std::vector<double> fracture_initiation_margin_series_Pa;
  std::vector<double> sigma_theta_lookup_time_series_s;
  std::vector<int> fracture_initiated_series;
};

}  // namespace lss::lot
