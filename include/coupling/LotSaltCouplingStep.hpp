#pragma once

#include <cstddef>

#include "coupling/LotSaltPressureMap.hpp"
#include "lot/PknResult.hpp"
#include "salt/SaltCreepInterface.hpp"
#include "salt/SaltCreepTypes.hpp"

namespace lss::coupling {

struct LotSaltCouplingConfig {
  double radial_position_m = 0.1556;
  double temperature_K = 350.0;
  LotSaltPressureMapMethod pressure_map_method =
      LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
  double absolute_wellbore_pressure_Pa = 0.0;
  double hydrostatic_pressure_Pa = 0.0;
  double surface_pressure_Pa = 0.0;
  double depth_m = 0.0;
};

struct LotSaltCouplingStepResult {
  lss::salt::SaltCreepQuery query;
  lss::salt::SaltCreepResponse response;
  LotSaltPressureMapResult pressure_map;
};

// Experimental injection point: builds a SaltCreepQuery from one step of a
// PknResult time series and calls salt.evaluate_wall_response().
//
// wall_pressure_Pa is produced by LotSaltPressureMap. The default mapping is
// ExperimentalNetPressureProxy, preserving the Fase 9.0 demonstration signal:
// wall_pressure_Pa = net_pressure_series_Pa[step_index]. This default is not a
// physical annular wall pressure; physically absolute mappings must be selected
// explicitly.
//
// Does not modify pkn_result. Does not affect PknRunner or lot-sim.
// Throws std::out_of_range  if step_index >= pkn_result.time_series_s.size().
// Throws std::invalid_argument if the PknResult vectors are inconsistent or
// config fields are out of valid range.
[[nodiscard]] LotSaltCouplingStepResult evaluate_lot_salt_step(
    const lss::lot::PknResult& pkn_result,
    std::size_t step_index,
    const LotSaltCouplingConfig& config,
    lss::salt::SaltCreepInterface& salt);

}  // namespace lss::coupling
