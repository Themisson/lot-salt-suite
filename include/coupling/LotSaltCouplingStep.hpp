#pragma once

#include <cstddef>

#include "lot/PknResult.hpp"
#include "salt/SaltCreepInterface.hpp"
#include "salt/SaltCreepTypes.hpp"

namespace lss::coupling {

struct LotSaltCouplingConfig {
  double radial_position_m = 0.1556;
  double temperature_K = 350.0;
};

struct LotSaltCouplingStepResult {
  lss::salt::SaltCreepQuery query;
  lss::salt::SaltCreepResponse response;
};

// Experimental injection point: builds a SaltCreepQuery from one step of a
// PknResult time series and calls salt.evaluate_wall_response().
//
// wall_pressure_Pa is set to net_pressure_series_Pa[step_index] as a
// demonstration signal only. net_pressure_series_Pa is NOT the physical
// annular wall pressure seen by the salt formation; the correct physical
// mapping (annular pressure -> salt boundary condition) is pending for a
// future coupling phase.
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
