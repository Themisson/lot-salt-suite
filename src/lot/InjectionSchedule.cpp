#include "lot/InjectionSchedule.hpp"

#include <algorithm>

namespace lss::lot {

double InjectionSchedule::scheduled_total_time_s() const {
  if (phases.empty()) {
    return total_time_s;
  }
  double total_s = accommodation_time_s;
  for (const auto& phase : phases) {
    total_s += std::max(0.0, phase.duration_s);
  }
  return total_s;
}

double InjectionSchedule::injected_volume_m3(double elapsed_time_s) const {
  const double t_s = std::max(0.0, elapsed_time_s - accommodation_time_s);
  if (phases.empty()) {
    return rate_m3_s * t_s;
  }

  double remaining_s = t_s;
  double volume_m3 = 0.0;
  for (const auto& phase : phases) {
    const double duration_s = std::max(0.0, phase.duration_s);
    const double used_s = std::min(remaining_s, duration_s);
    if (used_s > 0.0) {
      volume_m3 += std::max(0.0, phase.rate_m3_s) * used_s;
      remaining_s -= used_s;
    }
    if (remaining_s <= 0.0) {
      break;
    }
  }
  return volume_m3;
}

double InjectionSchedule::active_injection_time_s(double elapsed_time_s) const {
  const double t_s = std::max(0.0, elapsed_time_s - accommodation_time_s);
  if (phases.empty()) {
    return t_s;
  }

  double remaining_s = t_s;
  double active_s = 0.0;
  for (const auto& phase : phases) {
    const double duration_s = std::max(0.0, phase.duration_s);
    const double used_s = std::min(remaining_s, duration_s);
    if (used_s > 0.0 && phase.rate_m3_s > 0.0) {
      active_s += used_s;
    }
    remaining_s -= used_s;
    if (remaining_s <= 0.0) {
      break;
    }
  }
  return active_s;
}

double InjectionSchedule::rate_at_m3_s(double elapsed_time_s) const {
  const double t_s = std::max(0.0, elapsed_time_s - accommodation_time_s);
  if (phases.empty()) {
    return rate_m3_s;
  }

  double remaining_s = t_s;
  for (const auto& phase : phases) {
    const double duration_s = std::max(0.0, phase.duration_s);
    if (remaining_s <= duration_s) {
      return std::max(0.0, phase.rate_m3_s);
    }
    remaining_s -= duration_s;
  }
  return phases.empty() ? rate_m3_s : std::max(0.0, phases.back().rate_m3_s);
}

double InjectionSchedule::reference_rate_m3_s(double elapsed_time_s) const {
  if (phases.empty()) {
    return rate_m3_s;
  }
  const double current = rate_at_m3_s(elapsed_time_s);
  if (current > 0.0) {
    return current;
  }
  for (const auto& phase : phases) {
    if (phase.rate_m3_s > 0.0) {
      return phase.rate_m3_s;
    }
  }
  return rate_m3_s;
}

}  // namespace lss::lot
