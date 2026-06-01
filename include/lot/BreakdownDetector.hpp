#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace lss::lot {

struct BreakdownDetectionConfig {
  std::size_t minimum_points = 4;
  double slope_drop_fraction = 0.35;
};

struct BreakdownDetectionResult {
  bool found = false;
  std::size_t breakdown_index = 0;
  double breakdown_time_s = 0.0;
  double breakdown_volume_m3 = 0.0;
  double breakdown_pressure_Pa = 0.0;
  std::string method = "derivative_drop";
  double confidence = 0.0;
};

class BreakdownDetector {
 public:
  explicit BreakdownDetector(BreakdownDetectionConfig config = {});

  [[nodiscard]] BreakdownDetectionResult detect_derivative_drop(
      const std::vector<double>& time_s, const std::vector<double>& volume_m3,
      const std::vector<double>& pressure_Pa) const;

 private:
  BreakdownDetectionConfig config_;
};

}  // namespace lss::lot
