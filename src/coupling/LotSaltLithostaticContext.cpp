#include "coupling/LotSaltLithostaticContext.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

#include "units/units.hpp"

namespace lss::coupling {
namespace {

void require_positive_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltLithostaticContext: " + field +
                                " must be finite");
  }
  if (value <= 0.0) {
    throw std::invalid_argument("LotSaltLithostaticContext: " + field +
                                " must be positive");
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
            "LotSaltLithostaticContext: multiple layers contain "
            "lot.shoe_depth_m");
      }
      selected_layer = &layer;
    }
  }

  if (selected_layer == nullptr) {
    throw std::invalid_argument(
        "LotSaltLithostaticContext: no layer contains lot.shoe_depth_m");
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
      "LotSaltLithostaticContext: layer rock_id not found in CaseData");
}

}  // namespace

LotSaltLithostaticContext make_lot_salt_lithostatic_context(
    const lss::core::CaseData& data) {
  const auto& layer = layer_at_shoe(data);
  const auto& rock = rock_by_id(data, layer.rock_id);
  require_positive_finite(rock.density_kg_m3, "rock.density_kg_m3");

  LotSaltLithostaticContext context;
  context.depth_m = data.lot.shoe_depth_m;
  context.rock_density_kg_m3 = rock.density_kg_m3;
  context.lithostatic_pressure_Pa =
      units::hydrostatic_pressure_Pa(rock.density_kg_m3, context.depth_m);
  context.geostatic_stress_Pa = -context.lithostatic_pressure_Pa;
  context.rock_id = rock.id;
  context.layer_id = layer.id;
  context.source =
      "lot.shoe_depth_m + layer.rock_id + rock.density_kg_m3";
  return context;
}

LotSaltBridgeConfigOptions with_lithostatic_geostatic(
    LotSaltBridgeConfigOptions options,
    const lss::core::CaseData& data) {
  const auto context = make_lot_salt_lithostatic_context(data);
  options.geostatic_enabled = true;
  options.geostatic_radial_stress_Pa = context.geostatic_stress_Pa;
  options.geostatic_hoop_stress_Pa = context.geostatic_stress_Pa;
  options.geostatic_vertical_stress_Pa = context.geostatic_stress_Pa;
  return options;
}

}  // namespace lss::coupling
