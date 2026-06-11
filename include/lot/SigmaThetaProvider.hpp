#pragma once

#include <string>

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

class SigmaThetaProvider {
 public:
  virtual ~SigmaThetaProvider() = default;

  [[nodiscard]] virtual SigmaThetaRuntimePoint sample(
      double time_s, double wellbore_pressure_trial_Pa) const = 0;
};

}  // namespace lss::lot
