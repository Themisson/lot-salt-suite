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

  lss::salt::SaltCreepQuery query;
  query.time_s = pkn_result.time_series_s[step_index];
  query.wall_pressure_Pa = pkn_result.net_pressure_series_Pa[step_index];
  query.temperature_K = config.temperature_K;
  query.radial_position_m = config.radial_position_m;

  LotSaltCouplingStepResult result;
  result.query = query;
  result.response = salt.evaluate_wall_response(query);
  return result;
}

}  // namespace lss::coupling
