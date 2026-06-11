#include "lot/SigmaThetaProvider.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace lss::lot {
namespace {

void validate_point(const SigmaThetaTimeSeriesPoint& point,
                    const char* context) {
  if (!std::isfinite(point.time_s) || point.time_s < 0.0) {
    throw std::invalid_argument(std::string(context) +
                                ": time_s must be finite and non-negative");
  }
  if (!std::isfinite(point.sigma_theta_compression_positive_Pa) ||
      point.sigma_theta_compression_positive_Pa <= 0.0) {
    throw std::invalid_argument(
        std::string(context) +
        ": sigma_theta_compression_positive_Pa must be finite and positive");
  }
  if (!std::isfinite(point.influence_depth_m) ||
      point.influence_depth_m < 0.0) {
    throw std::invalid_argument(std::string(context) +
                                ": influence_depth_m must be finite and non-negative");
  }
}

}  // namespace

SigmaThetaTimeSeriesProvider::SigmaThetaTimeSeriesProvider(
    std::vector<SigmaThetaTimeSeriesPoint> points, std::string source,
    std::string mapping_status)
    : points_(std::move(points)),
      source_(std::move(source)),
      mapping_status_(std::move(mapping_status)) {
  if (points_.size() < 2) {
    throw std::invalid_argument(
        "SigmaThetaTimeSeriesProvider: at least two points are required");
  }
  if (source_.empty()) {
    throw std::invalid_argument("SigmaThetaTimeSeriesProvider: source is required");
  }
  if (mapping_status_.empty()) {
    throw std::invalid_argument(
        "SigmaThetaTimeSeriesProvider: mapping_status is required");
  }
  for (std::size_t i = 0; i < points_.size(); ++i) {
    validate_point(points_[i], "SigmaThetaTimeSeriesProvider");
    if (i > 0 && points_[i].time_s <= points_[i - 1].time_s) {
      throw std::invalid_argument(
          "SigmaThetaTimeSeriesProvider: times must be strictly increasing");
    }
  }
}

SigmaThetaRuntimePoint SigmaThetaTimeSeriesProvider::sample(
    double time_s, double wellbore_pressure_trial_Pa) const {
  if (!std::isfinite(time_s) || time_s < 0.0) {
    throw std::invalid_argument(
        "SigmaThetaTimeSeriesProvider: sample time_s must be finite and non-negative");
  }
  if (!std::isfinite(wellbore_pressure_trial_Pa) ||
      wellbore_pressure_trial_Pa < 0.0) {
    throw std::invalid_argument(
        "SigmaThetaTimeSeriesProvider: trial pressure must be finite and non-negative");
  }

  SigmaThetaRuntimePoint result;
  result.time_s = time_s;
  result.valid = true;
  result.source = source_;
  result.mapping_status = mapping_status_;

  if (time_s <= points_.front().time_s) {
    result.sigma_theta_compression_positive_Pa =
        points_.front().sigma_theta_compression_positive_Pa;
    result.layer_id = points_.front().layer_id;
    result.influence_depth_m = points_.front().influence_depth_m;
    return result;
  }
  if (time_s >= points_.back().time_s) {
    result.sigma_theta_compression_positive_Pa =
        points_.back().sigma_theta_compression_positive_Pa;
    result.layer_id = points_.back().layer_id;
    result.influence_depth_m = points_.back().influence_depth_m;
    return result;
  }

  const auto upper = std::upper_bound(
      points_.begin(), points_.end(), time_s,
      [](double value, const SigmaThetaTimeSeriesPoint& point) {
        return value < point.time_s;
      });
  const auto lower = upper - 1;
  const double span_s = upper->time_s - lower->time_s;
  const double fraction = (time_s - lower->time_s) / span_s;
  result.sigma_theta_compression_positive_Pa =
      lower->sigma_theta_compression_positive_Pa +
      fraction * (upper->sigma_theta_compression_positive_Pa -
                  lower->sigma_theta_compression_positive_Pa);
  result.layer_id = lower->layer_id.empty() ? upper->layer_id : lower->layer_id;
  result.influence_depth_m = lower->influence_depth_m > 0.0
                                 ? lower->influence_depth_m
                                 : upper->influence_depth_m;
  return result;
}

}  // namespace lss::lot
