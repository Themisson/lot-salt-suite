#include "salt/SaltCreepSaltcreepAdapter.hpp"

#include <algorithm>
#include <cmath>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>

#include "salt/SaltCreepTimeBridge.hpp"

namespace lss::salt {
namespace {

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("SaltCreepSaltcreepAdapter: " + field +
                                " must be finite");
  }
}

void validate_query(const SaltCreepQuery& query) {
  require_finite(query.time_s, "time_s");
  require_finite(query.wall_pressure_Pa, "wall_pressure_Pa");
  require_finite(query.temperature_K, "temperature_K");
  require_finite(query.radial_position_m, "radial_position_m");

  if (query.time_s < 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: time_s must be non-negative");
  }
  if (query.wall_pressure_Pa < 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: wall_pressure_Pa must be non-negative");
  }
  if (query.temperature_K <= 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: temperature_K must be positive");
  }
  if (query.radial_position_m < 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: radial_position_m must be non-negative");
  }
}

bool backend_minimum_supported(const SaltCreepAdapterConfig& config) {
  return config.geometry.axisymmetric && config.geometry.plane_strain &&
         config.mesh.axial_elements == 1 &&
         config.geostatic.use_explicit_gauss_point_vector;
}

SaltCreepTimeBridgeConfig make_bridge_config(
    const SaltCreepAdapterConfig& config) {
  SaltCreepTimeBridgeConfig bridge_config;
  bridge_config.inner_radius_m = config.geometry.inner_radius_m;
  bridge_config.outer_radius_m = config.geometry.outer_radius_m;
  bridge_config.height_m = config.geometry.height_m;
  bridge_config.radial_elements = config.mesh.radial_elements;
  bridge_config.elastic_modulus_Pa = config.material.elastic_modulus_Pa;
  bridge_config.poisson_ratio = config.material.poisson_ratio;
  bridge_config.temperature_K = config.thermal.temperature_K;
  bridge_config.reference_temperature_K =
      config.thermal.reference_temperature_K;
  bridge_config.alpha_thermal_1_K = config.thermal.alpha_thermal_1_K;
  bridge_config.wall_pressure_Pa =
      config.wall_pressure.initial_wall_pressure_Pa;
  bridge_config.geostatic_enabled = config.geostatic.enabled;
  bridge_config.geostatic_radial_stress_Pa =
      config.geostatic.radial_stress_Pa;
  bridge_config.geostatic_hoop_stress_Pa =
      config.geostatic.hoop_stress_Pa;
  bridge_config.geostatic_vertical_stress_Pa =
      config.geostatic.vertical_stress_Pa;
  bridge_config.fix_outer_wall = config.geostatic.enabled;
  return bridge_config;
}

}  // namespace

struct SaltCreepSaltcreepAdapter::BackendCache {
  explicit BackendCache(const SaltCreepAdapterConfig& config)
      : bridge(make_bridge_config(config)) {
    if (config.time.initial_time_s > 0.0) {
      (void)bridge.advance_to(config.time.initial_time_s);
    }
  }

  SaltCreepTimeBridge bridge;
};

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter()
    : SaltCreepSaltcreepAdapter(make_default_salt_creep_adapter_config()) {}

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter(
    SaltCreepAdapterConfig config)
    : config_(std::move(config)) {
  config_.validate();
  state_.initialize(config_.time.initial_time_s,
                    config_.wall_pressure.initial_wall_pressure_Pa);
}

SaltCreepSaltcreepAdapter::~SaltCreepSaltcreepAdapter() = default;

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter(
    SaltCreepSaltcreepAdapter&&) noexcept = default;

SaltCreepSaltcreepAdapter& SaltCreepSaltcreepAdapter::operator=(
    SaltCreepSaltcreepAdapter&&) noexcept = default;

bool SaltCreepSaltcreepAdapter::is_available() const {
  return backend_minimum_supported(config_);
}

const SaltCreepAdapterConfig& SaltCreepSaltcreepAdapter::config() const {
  return config_;
}

const SaltCreepAdapterState& SaltCreepSaltcreepAdapter::state() const {
  return state_;
}

int SaltCreepSaltcreepAdapter::backend_build_count() const {
  return backend_build_count_;
}

SaltCreepSaltcreepAdapter::BackendCache&
SaltCreepSaltcreepAdapter::backend() const {
  if (!backend_cache_) {
    backend_cache_ = std::make_unique<BackendCache>(config_);
    ++backend_build_count_;
  }
  return *backend_cache_;
}

SaltCreepResponse SaltCreepSaltcreepAdapter::evaluate_wall_response(
    const SaltCreepQuery& query) const {
  validate_query(query);
  if (!is_available()) {
    throw std::logic_error(
        "SaltCreepSaltcreepAdapter: time bridge is unavailable for config");
  }
  const auto bridge_result =
      backend().bridge.advance_to(query.time_s, query.wall_pressure_Pa);

  SaltCreepResponse response;
  response.radial_displacement_m = bridge_result.wall_displacement_m;
  response.radial_closure_m =
      radial_closure_from_displacement(response.radial_displacement_m);
  // This is a wall hoop-strain proxy (u/r_i) kept for the minimum backend
  // contract until a future temporal/creep adapter exposes a true du/dr field.
  response.radial_strain =
      response.radial_displacement_m / config_.geometry.inner_radius_m;
  response.effective_closure_pressure_Pa = 0.0;
  response.valid = true;
  state_.record_response(query.time_s, query.wall_pressure_Pa, response);
  return response;
}

double SaltCreepSaltcreepAdapter::radial_closure_from_displacement(
    double radial_displacement_m) {
  require_finite(radial_displacement_m, "radial_displacement_m");
  return std::max(0.0, -radial_displacement_m);
}

}  // namespace lss::salt
