#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace lss::coupling {

enum class SigmaThetaHoopState {
  Compressive,
  Neutral,
  Tensile
};

struct SigmaThetaInfluenceLayer {
  std::string layer_id;
  double influence_depth_m = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
};

struct SigmaThetaBreakdownPoint {
  std::string layer_id;
  double influence_depth_m = 0.0;
  double time_s = 0.0;
  double pressure_Pa = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  double margin_Pa = 0.0;
  SigmaThetaHoopState hoop_state = SigmaThetaHoopState::Neutral;
  bool tensile_hoop_state = false;
  bool legacy_algebra_opened = false;
  bool opened = false;
  std::string caveat;
};

struct SigmaThetaBreakdownSeriesResult {
  std::vector<SigmaThetaBreakdownPoint> points;
  bool any_opened = false;
};

[[nodiscard]] const char* to_string(SigmaThetaHoopState state);

[[nodiscard]] SigmaThetaHoopState classify_sigma_theta_hoop_state(
    double sigma_theta_compression_positive_Pa);

[[nodiscard]] SigmaThetaBreakdownPoint evaluate_sigma_theta_breakdown_point(
    const SigmaThetaInfluenceLayer& layer,
    double time_s,
    double pressure_Pa);

[[nodiscard]] SigmaThetaBreakdownSeriesResult
evaluate_sigma_theta_breakdown_series(
    const std::vector<SigmaThetaInfluenceLayer>& layers,
    const std::vector<double>& time_series_s,
    const std::vector<double>& pressure_series_Pa);

}  // namespace lss::coupling
