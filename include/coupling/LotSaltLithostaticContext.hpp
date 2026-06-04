#pragma once

#include <string>

#include "core/types.hpp"
#include "coupling/LotSaltBridgeConfigBuilder.hpp"

namespace lss::coupling {

struct LotSaltLithostaticContext {
  double depth_m = 0.0;
  double rock_density_kg_m3 = 0.0;
  double lithostatic_pressure_Pa = 0.0;
  double geostatic_stress_Pa = 0.0;

  std::string rock_id;
  std::string layer_id;
  std::string source;
};

[[nodiscard]] LotSaltLithostaticContext make_lot_salt_lithostatic_context(
    const lss::core::CaseData& data);

[[nodiscard]] LotSaltBridgeConfigOptions with_lithostatic_geostatic(
    LotSaltBridgeConfigOptions options,
    const lss::core::CaseData& data);

}  // namespace lss::coupling
