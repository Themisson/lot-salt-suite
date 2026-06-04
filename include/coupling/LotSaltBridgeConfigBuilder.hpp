#pragma once

#include "core/types.hpp"
#include "salt/SaltCreepTimeBridge.hpp"

namespace lss::coupling {

struct LotSaltBridgeConfigOptions {
  double inner_radius_m = 0.1556;
  double outer_radius_m = 1.556;
  int radial_elements = 40;

  bool use_lot_fracture_height = true;
  bool geostatic_enabled = false;
  double geostatic_radial_stress_Pa = 0.0;
  double geostatic_hoop_stress_Pa = 0.0;
  double geostatic_vertical_stress_Pa = 0.0;

  double temperature_K = 350.0;
};

[[nodiscard]] lss::salt::SaltCreepTimeBridgeConfig make_lot_salt_bridge_config(
    const lss::core::CaseData& data,
    const LotSaltBridgeConfigOptions& options = {});

}  // namespace lss::coupling
