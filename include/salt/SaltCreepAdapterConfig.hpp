#pragma once

namespace lss::salt {

struct SaltCreepAdapterGeometryConfig {
  double inner_radius_m = 0.1556;
  double outer_radius_m = 1.556;
  double height_m = 1.0;
  bool axisymmetric = true;
  bool plane_strain = true;
};

struct SaltCreepAdapterMeshConfig {
  int radial_elements = 40;
  int axial_elements = 1;
};

struct SaltCreepAdapterMaterialConfig {
  double elastic_modulus_Pa = 25.0e9;
  double poisson_ratio = 0.30;
  double density_kg_m3 = 2160.0;
};

struct SaltCreepAdapterThermalConfig {
  double temperature_K = 350.0;
  double reference_temperature_K = 350.0;
  double alpha_thermal_1_K = 0.0;
};

struct SaltCreepAdapterGeostaticConfig {
  bool enabled = false;
  // Signed stresses for the future backend vector; compression is negative there.
  double radial_stress_Pa = 0.0;
  double hoop_stress_Pa = 0.0;
  double vertical_stress_Pa = 0.0;
  bool use_explicit_gauss_point_vector = true;
};

struct SaltCreepAdapterTimeConfig {
  double initial_time_s = 0.0;
  double dt_s = 60.0;
  double total_time_s = 60.0;
  int max_steps = 1;
};

struct SaltCreepAdapterWallPressureConfig {
  // Wall pressure follows the lot-salt-suite contract: nonnegative compression.
  double initial_wall_pressure_Pa = 0.0;
};

struct SaltCreepAdapterConfig {
  SaltCreepAdapterGeometryConfig geometry;
  SaltCreepAdapterMeshConfig mesh;
  SaltCreepAdapterMaterialConfig material;
  SaltCreepAdapterThermalConfig thermal;
  SaltCreepAdapterGeostaticConfig geostatic;
  SaltCreepAdapterTimeConfig time;
  SaltCreepAdapterWallPressureConfig wall_pressure;

  void validate() const;
};

void validate_salt_creep_adapter_config(const SaltCreepAdapterConfig& config);

SaltCreepAdapterConfig make_default_salt_creep_adapter_config();

}  // namespace lss::salt
