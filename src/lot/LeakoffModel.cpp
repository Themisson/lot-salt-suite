#include "lot/LeakoffModel.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::lot {
namespace {

void require_finite_non_negative(double value, const std::string& field) {
  if (!std::isfinite(value) || value < 0.0) {
    throw std::invalid_argument("LeakoffModel: " + field +
                                " must be finite and non-negative");
  }
}

void validate_state(const LeakoffState& state) {
  require_finite_non_negative(state.time_s, "time_s");
  require_finite_non_negative(state.previous_cumulative_volume_m3,
                              "previous_cumulative_volume_m3");
  if (!std::isfinite(state.dt_s) || state.dt_s <= 0.0) {
    throw std::invalid_argument("LeakoffModel: dt_s must be finite and positive");
  }
}

LeakoffStepResult make_result(double incremental_volume_m3,
                              double previous_cumulative_volume_m3) {
  require_finite_non_negative(incremental_volume_m3, "incremental_volume_m3");
  const double cumulative_volume_m3 =
      previous_cumulative_volume_m3 + incremental_volume_m3;
  require_finite_non_negative(cumulative_volume_m3, "cumulative_volume_m3");
  return {incremental_volume_m3, cumulative_volume_m3};
}

}  // namespace

LeakoffStepResult compute_leakoff_step(const LeakoffInput& input,
                                       const LeakoffState& state) {
  validate_state(state);

  switch (input.model) {
    case LeakoffModel::None:
      return {0.0, state.previous_cumulative_volume_m3};

    case LeakoffModel::ConstantRate:
      require_finite_non_negative(input.constant_rate_m3_s,
                                  "constant_rate_m3_s");
      return make_result(input.constant_rate_m3_s * state.dt_s,
                         state.previous_cumulative_volume_m3);

    case LeakoffModel::Carter: {
      require_finite_non_negative(input.coefficient_m_sqrt_s,
                                  "coefficient_m_sqrt_s");
      require_finite_non_negative(input.area_m2, "area_m2");
      const double t0 = state.time_s;
      const double t1 = state.time_s + state.dt_s;
      const double incremental_volume_m3 =
          2.0 * input.coefficient_m_sqrt_s * input.area_m2 *
          std::max(0.0, std::sqrt(t1) - std::sqrt(t0));
      return make_result(incremental_volume_m3,
                         state.previous_cumulative_volume_m3);
    }

    case LeakoffModel::SyntheticConstant: {
      require_finite_non_negative(input.coefficient_m_sqrt_s,
                                  "coefficient_m_sqrt_s");
      require_finite_non_negative(input.area_m2, "area_m2");
      const double incremental_volume_m3 =
          input.coefficient_m_sqrt_s * input.area_m2 * std::sqrt(state.dt_s);
      return make_result(incremental_volume_m3,
                         state.previous_cumulative_volume_m3);
    }
  }

  throw std::invalid_argument("LeakoffModel: unsupported leakoff model");
}

}  // namespace lss::lot
