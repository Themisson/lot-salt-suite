#pragma once

#include <string>
#include <vector>

namespace lss::lot {

struct SigmaThetaRuntimePoint {
  double time_s = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  std::string layer_id;
  double influence_depth_m = 0.0;
  bool valid = false;
  std::string source;
  std::string mapping_status;
};

struct SigmaThetaTimeSeriesPoint {
  double time_s = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  std::string layer_id;
  double influence_depth_m = 0.0;
};

class SigmaThetaProvider {
 public:
  virtual ~SigmaThetaProvider() = default;

  [[nodiscard]] virtual SigmaThetaRuntimePoint sample(
      double time_s, double wellbore_pressure_trial_Pa) const = 0;
};

class SigmaThetaTimeSeriesProvider final : public SigmaThetaProvider {
 public:
  SigmaThetaTimeSeriesProvider(
      std::vector<SigmaThetaTimeSeriesPoint> points, std::string source,
      std::string mapping_status);

  [[nodiscard]] SigmaThetaRuntimePoint sample(
      double time_s, double wellbore_pressure_trial_Pa) const override;

 private:
  std::vector<SigmaThetaTimeSeriesPoint> points_;
  std::string source_;
  std::string mapping_status_;
};

}  // namespace lss::lot
