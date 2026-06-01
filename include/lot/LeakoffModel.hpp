#pragma once

#include "lot/LotTypes.hpp"

namespace lss::lot {

struct LeakoffConfig {
  bool enabled = false;
  LeakoffModel model = LeakoffModel::None;
  double coefficient_m_sqrt_s = 0.0;
  double constant_rate_m3_s = 0.0;
};

struct LeakoffInput {
  LeakoffModel model = LeakoffModel::None;
  double coefficient_m_sqrt_s = 0.0;
  double constant_rate_m3_s = 0.0;
  double area_m2 = 0.0;
};

struct LeakoffState {
  double time_s = 0.0;
  double dt_s = 0.0;
  double previous_cumulative_volume_m3 = 0.0;
};

struct LeakoffStepResult {
  double incremental_volume_m3 = 0.0;
  double cumulative_volume_m3 = 0.0;
};

LeakoffStepResult compute_leakoff_step(const LeakoffInput& input,
                                       const LeakoffState& state);

}  // namespace lss::lot
