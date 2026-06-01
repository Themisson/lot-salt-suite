#include "lot/BreakdownDetector.hpp"

#include <cmath>
#include <stdexcept>

namespace lss::lot {

BreakdownDetector::BreakdownDetector(BreakdownDetectionConfig config)
    : config_(config) {}

BreakdownDetectionResult BreakdownDetector::detect_derivative_drop(
    const std::vector<double>& time_s, const std::vector<double>& volume_m3,
    const std::vector<double>& pressure_Pa) const {
  if (time_s.size() != volume_m3.size() || time_s.size() != pressure_Pa.size()) {
    throw std::invalid_argument("BreakdownDetector: input vectors must have equal sizes");
  }
  if (time_s.size() < config_.minimum_points) {
    throw std::invalid_argument("BreakdownDetector: not enough points for derivative_drop");
  }
  if (config_.slope_drop_fraction <= 0.0 || config_.slope_drop_fraction >= 1.0) {
    throw std::invalid_argument("BreakdownDetector: slope_drop_fraction must be in (0, 1)");
  }

  double reference_slope = 0.0;
  std::size_t reference_count = 0;
  for (std::size_t i = 1; i + 1 < pressure_Pa.size(); ++i) {
    const double dV = volume_m3[i] - volume_m3[i - 1];
    const double dP = pressure_Pa[i] - pressure_Pa[i - 1];
    if (dV <= 0.0) {
      continue;
    }
    const double slope = dP / dV;
    if (slope <= 0.0 || !std::isfinite(slope)) {
      continue;
    }

    if (reference_count == 0) {
      reference_slope = slope;
      reference_count = 1;
      continue;
    }

    const double threshold = reference_slope * config_.slope_drop_fraction;
    if (slope < threshold) {
      BreakdownDetectionResult result;
      result.found = true;
      result.breakdown_index = i;
      result.breakdown_time_s = time_s[i];
      result.breakdown_volume_m3 = volume_m3[i];
      result.breakdown_pressure_Pa = pressure_Pa[i];
      result.confidence = 1.0 - (slope / reference_slope);
      return result;
    }

    reference_slope =
        (reference_slope * static_cast<double>(reference_count) + slope) /
        static_cast<double>(reference_count + 1);
    ++reference_count;
  }

  return {};
}

}  // namespace lss::lot
