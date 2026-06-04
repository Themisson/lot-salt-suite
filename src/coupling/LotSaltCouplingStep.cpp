#include "coupling/LotSaltCouplingStep.hpp"

#include <stdexcept>

namespace lss::coupling {

LotSaltCouplingStepResult evaluate_lot_salt_step(
    const lss::lot::PknResult& pkn_result,
    std::size_t step_index,
    const LotSaltCouplingConfig& config,
    lss::salt::SaltCreepInterface& salt) {
  if (step_index >= pkn_result.time_series_s.size()) {
    throw std::out_of_range(
        "evaluate_lot_salt_step: step_index out of range for PknResult "
        "time series");
  }
  if (pkn_result.net_pressure_series_Pa.size() !=
      pkn_result.time_series_s.size()) {
    throw std::invalid_argument(
        "evaluate_lot_salt_step: net_pressure_series_Pa size mismatch with "
        "time_series_s");
  }
  if (config.temperature_K <= 0.0) {
    throw std::invalid_argument(
        "evaluate_lot_salt_step: temperature_K must be positive");
  }
  if (config.radial_position_m < 0.0) {
    throw std::invalid_argument(
        "evaluate_lot_salt_step: radial_position_m must be non-negative");
  }

  LotSaltPressureMapInput pressure_input;
  pressure_input.net_pressure_Pa =
      pkn_result.net_pressure_series_Pa[step_index];
  pressure_input.absolute_wellbore_pressure_Pa =
      config.absolute_wellbore_pressure_Pa;
  pressure_input.hydrostatic_pressure_Pa = config.hydrostatic_pressure_Pa;
  pressure_input.surface_pressure_Pa = config.surface_pressure_Pa;
  pressure_input.depth_m = config.depth_m;
  pressure_input.method = config.pressure_map_method;

  const LotSaltPressureMapResult pressure_map =
      map_lot_pkn_to_salt_wall_pressure(pressure_input);

  lss::salt::SaltCreepQuery query;
  query.time_s = pkn_result.time_series_s[step_index];
  query.wall_pressure_Pa = pressure_map.wall_pressure_Pa;
  query.temperature_K = config.temperature_K;
  query.radial_position_m = config.radial_position_m;

  LotSaltCouplingStepResult result;
  result.query = query;
  result.pressure_map = pressure_map;
  result.response = salt.evaluate_wall_response(query);
  return result;
}

}  // namespace lss::coupling
