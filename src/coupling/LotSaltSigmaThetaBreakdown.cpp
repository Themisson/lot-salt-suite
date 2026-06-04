#include "coupling/LotSaltSigmaThetaBreakdown.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::coupling {
namespace {

void require_non_negative_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltSigmaThetaBreakdown: " + field +
                                " must be finite");
  }
  if (value < 0.0) {
    throw std::invalid_argument("LotSaltSigmaThetaBreakdown: " + field +
                                " must be non-negative");
  }
}

void validate_layer(const SigmaThetaInfluenceLayer& layer) {
  if (layer.layer_id.empty()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaBreakdown: layer_id must not be empty");
  }
  require_non_negative_finite(layer.influence_depth_m, "influence_depth_m");
  require_non_negative_finite(layer.sigma_theta_compression_positive_Pa,
                              "sigma_theta_compression_positive_Pa");
}

}  // namespace

SigmaThetaBreakdownPoint evaluate_sigma_theta_breakdown_point(
    const SigmaThetaInfluenceLayer& layer,
    double time_s,
    double pressure_Pa) {
  validate_layer(layer);
  require_non_negative_finite(time_s, "time_s");
  require_non_negative_finite(pressure_Pa, "pressure_Pa");

  SigmaThetaBreakdownPoint point;
  point.layer_id = layer.layer_id;
  point.influence_depth_m = layer.influence_depth_m;
  point.time_s = time_s;
  point.pressure_Pa = pressure_Pa;
  point.sigma_theta_compression_positive_Pa =
      layer.sigma_theta_compression_positive_Pa;
  point.margin_Pa =
      pressure_Pa - layer.sigma_theta_compression_positive_Pa;
  point.opened = point.margin_Pa > 0.0;
  return point;
}

SigmaThetaBreakdownSeriesResult evaluate_sigma_theta_breakdown_series(
    const std::vector<SigmaThetaInfluenceLayer>& layers,
    const std::vector<double>& time_series_s,
    const std::vector<double>& pressure_series_Pa) {
  if (layers.empty()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaBreakdown: layers must not be empty");
  }
  if (time_series_s.empty()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaBreakdown: time_series_s must not be empty");
  }
  if (time_series_s.size() != pressure_series_Pa.size()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaBreakdown: time and pressure series sizes differ");
  }

  SigmaThetaBreakdownSeriesResult result;
  result.points.reserve(time_series_s.size() * layers.size());

  for (std::size_t time_index = 0; time_index < time_series_s.size();
       ++time_index) {
    for (const auto& layer : layers) {
      auto point = evaluate_sigma_theta_breakdown_point(
          layer, time_series_s[time_index], pressure_series_Pa[time_index]);
      result.any_opened = result.any_opened || point.opened;
      result.points.push_back(std::move(point));
    }
  }

  return result;
}

}  // namespace lss::coupling
