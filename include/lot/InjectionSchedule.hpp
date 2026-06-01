#pragma once

namespace lss::lot {

struct InjectionSchedule {
  double rate_m3_s = 0.0;
  double total_time_s = 0.0;
  double dt_s = 0.0;
  double accommodation_time_s = 0.0;

  [[nodiscard]] bool has_active_injection() const {
    return rate_m3_s > 0.0 && total_time_s > accommodation_time_s;
  }
};

}  // namespace lss::lot
