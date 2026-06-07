#include "wellbore/AnnularVolume.hpp"

#include <cmath>
#include <numbers>
#include <stdexcept>
#include <string>

namespace lss::wellbore {
namespace {

void require_finite(double value, const char* field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument(std::string("AnnularVolume: ") + field +
                                " must be finite");
  }
}

}  // namespace

double annular_volume_per_radian_m3(double outer_radius_m,
                                    double inner_radius_m,
                                    double length_m) {
  require_finite(outer_radius_m, "outer_radius_m");
  require_finite(inner_radius_m, "inner_radius_m");
  require_finite(length_m, "length_m");
  if (outer_radius_m <= 0.0) {
    throw std::invalid_argument("AnnularVolume: outer_radius_m must be positive");
  }
  if (inner_radius_m < 0.0) {
    throw std::invalid_argument("AnnularVolume: inner_radius_m must be non-negative");
  }
  if (outer_radius_m <= inner_radius_m) {
    throw std::invalid_argument(
        "AnnularVolume: outer_radius_m must be greater than inner_radius_m");
  }
  if (length_m < 0.0) {
    throw std::invalid_argument("AnnularVolume: length_m must be non-negative");
  }
  return 0.5 * (outer_radius_m * outer_radius_m -
                inner_radius_m * inner_radius_m) *
         length_m;
}

double annular_total_volume_m3(double outer_radius_m, double inner_radius_m,
                               double length_m) {
  return 2.0 * std::numbers::pi *
         annular_volume_per_radian_m3(outer_radius_m, inner_radius_m, length_m);
}

}  // namespace lss::wellbore
