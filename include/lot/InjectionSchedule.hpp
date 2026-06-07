#pragma once

#include <string>
#include <vector>

namespace lss::lot {

struct InjectionPhase {
  std::string name = "injection";
  double duration_s = 0.0;
  double rate_m3_s = 0.0;
};

struct InjectionSchedule {
  double rate_m3_s = 0.0;
  double total_time_s = 0.0;
  double dt_s = 0.0;
  double accommodation_time_s = 0.0;
  std::vector<InjectionPhase> phases;

  [[nodiscard]] bool has_active_injection() const {
    if (phases.empty()) {
      return rate_m3_s > 0.0 && total_time_s > accommodation_time_s;
    }
    for (const auto& phase : phases) {
      if (phase.rate_m3_s > 0.0 && phase.duration_s > 0.0) {
        return true;
      }
    }
    return false;
  }

  [[nodiscard]] double scheduled_total_time_s() const;
  [[nodiscard]] double injected_volume_m3(double elapsed_time_s) const;
  [[nodiscard]] double active_injection_time_s(double elapsed_time_s) const;
  [[nodiscard]] double reference_rate_m3_s(double elapsed_time_s) const;
  [[nodiscard]] double rate_at_m3_s(double elapsed_time_s) const;
};

}  // namespace lss::lot
