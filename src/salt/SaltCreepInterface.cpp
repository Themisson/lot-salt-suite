#include "salt/SaltCreepInterface.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::salt {
namespace {

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("SaltCreepInterface: " + field + " must be finite");
  }
}

void validate_query(const SaltCreepQuery& query) {
  require_finite(query.time_s, "time_s");
  require_finite(query.wall_pressure_Pa, "wall_pressure_Pa");
  require_finite(query.temperature_K, "temperature_K");
  require_finite(query.radial_position_m, "radial_position_m");

  if (query.time_s < 0.0) {
    throw std::invalid_argument("SaltCreepInterface: time_s must be non-negative");
  }
  if (query.wall_pressure_Pa < 0.0) {
    throw std::invalid_argument(
        "SaltCreepInterface: wall_pressure_Pa must be non-negative");
  }
  if (query.temperature_K <= 0.0) {
    throw std::invalid_argument("SaltCreepInterface: temperature_K must be positive");
  }
  if (query.radial_position_m < 0.0) {
    throw std::invalid_argument(
        "SaltCreepInterface: radial_position_m must be non-negative");
  }
}

}  // namespace

bool NullSaltCreepInterface::is_available() const { return false; }

SaltCreepResponse NullSaltCreepInterface::evaluate_wall_response(
    const SaltCreepQuery& query) const {
  validate_query(query);

  SaltCreepResponse response;
  response.radial_displacement_m = 0.0;
  response.radial_closure_m = 0.0;
  response.radial_strain = 0.0;
  response.effective_closure_pressure_Pa = 0.0;
  response.valid = true;
  return response;
}

}  // namespace lss::salt
