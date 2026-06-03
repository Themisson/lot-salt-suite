#include "salt/SaltCreepAdapterConfig.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::salt {
namespace {

void require_finite(double value, const char* field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument(std::string(field) + " must be finite");
  }
}

void require_positive(double value, const char* field) {
  require_finite(value, field);
  if (value <= 0.0) {
    throw std::invalid_argument(std::string(field) + " must be > 0");
  }
}

void require_nonnegative(double value, const char* field) {
  require_finite(value, field);
  if (value < 0.0) {
    throw std::invalid_argument(std::string(field) + " must be >= 0");
  }
}

}  // namespace

void SaltCreepAdapterConfig::validate() const {
  validate_salt_creep_adapter_config(*this);
}

void validate_salt_creep_adapter_config(const SaltCreepAdapterConfig& config) {
  require_positive(config.geometry.inner_radius_m, "geometry.inner_radius_m");
  require_positive(config.geometry.outer_radius_m, "geometry.outer_radius_m");
  require_positive(config.geometry.height_m, "geometry.height_m");
  if (config.geometry.outer_radius_m <= config.geometry.inner_radius_m) {
    throw std::invalid_argument(
        "geometry.outer_radius_m must be greater than geometry.inner_radius_m");
  }

  if (config.mesh.radial_elements <= 0) {
    throw std::invalid_argument("mesh.radial_elements must be > 0");
  }
  if (config.mesh.axial_elements <= 0) {
    throw std::invalid_argument("mesh.axial_elements must be > 0");
  }

  require_positive(config.material.elastic_modulus_Pa,
                   "material.elastic_modulus_Pa");
  require_positive(config.material.density_kg_m3, "material.density_kg_m3");
  require_finite(config.material.poisson_ratio, "material.poisson_ratio");
  if (config.material.poisson_ratio <= -1.0 ||
      config.material.poisson_ratio >= 0.5) {
    throw std::invalid_argument(
        "material.poisson_ratio must be in the open interval (-1, 0.5)");
  }

  require_positive(config.thermal.temperature_K, "thermal.temperature_K");
  require_positive(config.thermal.reference_temperature_K,
                   "thermal.reference_temperature_K");
  require_finite(config.thermal.alpha_thermal_1_K,
                 "thermal.alpha_thermal_1_K");

  require_finite(config.geostatic.radial_stress_Pa,
                 "geostatic.radial_stress_Pa");
  require_finite(config.geostatic.hoop_stress_Pa,
                 "geostatic.hoop_stress_Pa");
  require_finite(config.geostatic.vertical_stress_Pa,
                 "geostatic.vertical_stress_Pa");

  require_nonnegative(config.time.initial_time_s, "time.initial_time_s");
  require_positive(config.time.dt_s, "time.dt_s");
  require_nonnegative(config.time.total_time_s, "time.total_time_s");
  if (config.time.total_time_s < config.time.initial_time_s) {
    throw std::invalid_argument(
        "time.total_time_s must be >= time.initial_time_s");
  }
  if (config.time.max_steps <= 0) {
    throw std::invalid_argument("time.max_steps must be > 0");
  }

  require_nonnegative(config.wall_pressure.initial_wall_pressure_Pa,
                      "wall_pressure.initial_wall_pressure_Pa");
}

SaltCreepAdapterConfig make_default_salt_creep_adapter_config() {
  SaltCreepAdapterConfig config;
  config.validate();
  return config;
}

}  // namespace lss::salt
