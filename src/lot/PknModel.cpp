#include "lot/PknModel.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace lss::lot {

PknResult PknModel::evaluate(const PknInput& input, double elapsed_time_s) const {
  if (elapsed_time_s < 0.0) {
    throw std::invalid_argument("PknModel: elapsed_time_s must be non-negative");
  }
  if (input.fracture_height_m <= 0.0) {
    throw std::invalid_argument("PknModel: fracture_height_m must be positive");
  }
  if (input.injection.rate_m3_s < 0.0) {
    throw std::invalid_argument("PknModel: injection rate must be non-negative");
  }

  const double active_time_s =
      std::max(0.0, elapsed_time_s - input.injection.accommodation_time_s);
  const double injected_volume_m3 = input.injection.rate_m3_s * active_time_s;
  const double width_m = std::max(input.initial_width_m,
                                  std::cbrt(std::max(0.0, injected_volume_m3)) * 0.01);
  const double area_m2 = std::max(width_m * input.fracture_height_m, 1.0e-18);
  const double length_m = injected_volume_m3 / area_m2;

  PknResult result;
  result.width_m = width_m;
  result.length_m = length_m;
  result.volume_m3 = std::max(0.0, width_m * input.fracture_height_m * length_m);
  result.net_pressure_Pa = std::max(0.0, input.net_pressure_Pa);
  if (!std::isfinite(result.width_m) || !std::isfinite(result.length_m) ||
      !std::isfinite(result.volume_m3) || !std::isfinite(result.net_pressure_Pa)) {
    throw std::runtime_error("PknModel: non-finite synthetic result");
  }
  return result;
}

}  // namespace lss::lot
