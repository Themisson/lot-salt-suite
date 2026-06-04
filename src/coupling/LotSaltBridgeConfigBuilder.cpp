#include "coupling/LotSaltBridgeConfigBuilder.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

#include "coupling/LotSaltHydrostaticContext.hpp"

namespace lss::coupling {
namespace {

void require_positive_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltBridgeConfigBuilder: " + field +
                                " must be finite");
  }
  if (value <= 0.0) {
    throw std::invalid_argument("LotSaltBridgeConfigBuilder: " + field +
                                " must be positive");
  }
}

void validate_options(const LotSaltBridgeConfigOptions& options) {
  require_positive_finite(options.inner_radius_m, "inner_radius_m");
  require_positive_finite(options.outer_radius_m, "outer_radius_m");
  if (options.outer_radius_m <= options.inner_radius_m) {
    throw std::invalid_argument(
        "LotSaltBridgeConfigBuilder: outer_radius_m must be greater than "
        "inner_radius_m");
  }
  if (options.radial_elements <= 0) {
    throw std::invalid_argument(
        "LotSaltBridgeConfigBuilder: radial_elements must be positive");
  }
  require_positive_finite(options.temperature_K, "temperature_K");
  if (!options.use_lot_fracture_height) {
    throw std::invalid_argument(
        "LotSaltBridgeConfigBuilder: use_lot_fracture_height=false is not "
        "supported until an explicit salt domain height is provided");
  }
  if (options.geostatic_enabled) {
    throw std::invalid_argument(
        "LotSaltBridgeConfigBuilder: geostatic_enabled=true is not supported "
        "until explicit geostatic stresses are provided");
  }
}

const lss::core::LayerData& layer_at_shoe(const lss::core::CaseData& data) {
  const double shoe_depth_m = data.lot.shoe_depth_m;
  require_positive_finite(shoe_depth_m, "lot.shoe_depth_m");

  const lss::core::LayerData* selected_layer = nullptr;
  for (const auto& layer : data.layers) {
    if (layer.top_m <= shoe_depth_m && shoe_depth_m <= layer.base_m) {
      if (selected_layer != nullptr) {
        throw std::invalid_argument(
            "LotSaltBridgeConfigBuilder: multiple layers contain "
            "lot.shoe_depth_m");
      }
      selected_layer = &layer;
    }
  }

  if (selected_layer == nullptr) {
    throw std::invalid_argument(
        "LotSaltBridgeConfigBuilder: no layer contains lot.shoe_depth_m");
  }
  return *selected_layer;
}

const lss::core::RockData& rock_by_id(const lss::core::CaseData& data,
                                      const std::string& rock_id) {
  for (const auto& rock : data.rocks) {
    if (rock.id == rock_id) {
      return rock;
    }
  }
  throw std::invalid_argument(
      "LotSaltBridgeConfigBuilder: layer rock_id not found in CaseData");
}

}  // namespace

lss::salt::SaltCreepTimeBridgeConfig make_lot_salt_bridge_config(
    const lss::core::CaseData& data,
    const LotSaltBridgeConfigOptions& options) {
  validate_options(options);

  const auto& layer = layer_at_shoe(data);
  const auto& rock = rock_by_id(data, layer.rock_id);
  require_positive_finite(rock.E_Pa, "rock.E_Pa");
  require_positive_finite(rock.nu, "rock.nu");
  if (rock.nu >= 0.5) {
    throw std::invalid_argument(
        "LotSaltBridgeConfigBuilder: rock.nu must be less than 0.5");
  }

  require_positive_finite(data.lot.fracture_height_m,
                          "lot.fracture_height_m");

  const auto hydrostatic_context =
      make_lot_salt_hydrostatic_context(data);

  lss::salt::SaltCreepTimeBridgeConfig config;
  config.inner_radius_m = options.inner_radius_m;
  config.outer_radius_m = options.outer_radius_m;
  config.height_m = data.lot.fracture_height_m;
  config.radial_elements = options.radial_elements;
  config.elastic_modulus_Pa = rock.E_Pa;
  config.poisson_ratio = rock.nu;
  config.temperature_K = options.temperature_K;
  config.reference_temperature_K = options.temperature_K;
  config.alpha_thermal_1_K = 0.0;
  config.wall_pressure_Pa = hydrostatic_context.hydrostatic_pressure_Pa;
  config.geostatic_enabled = false;
  config.geostatic_radial_stress_Pa = 0.0;
  config.geostatic_hoop_stress_Pa = 0.0;
  config.geostatic_vertical_stress_Pa = 0.0;
  config.fix_outer_wall = false;
  return config;
}

}  // namespace lss::coupling
