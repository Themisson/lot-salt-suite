#pragma once

#include "salt/SaltCreepTypes.hpp"

namespace lss::salt {

class SaltCreepAdapterState {
 public:
  [[nodiscard]] bool initialized() const;
  [[nodiscard]] double current_time_s() const;
  [[nodiscard]] double last_wall_pressure_Pa() const;
  [[nodiscard]] double last_radial_displacement_m() const;
  [[nodiscard]] double last_radial_closure_m() const;
  [[nodiscard]] int step_count() const;

  void initialize(double initial_time_s, double initial_wall_pressure_Pa);
  void record_response(double time_s,
                       double wall_pressure_Pa,
                       const SaltCreepResponse& response);
  void reset();

 private:
  bool initialized_ = false;
  double current_time_s_ = 0.0;
  double last_wall_pressure_Pa_ = 0.0;
  double last_radial_displacement_m_ = 0.0;
  double last_radial_closure_m_ = 0.0;
  int step_count_ = 0;
};

}  // namespace lss::salt
