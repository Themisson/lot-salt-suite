#pragma once

namespace lss::salt {

struct WallPressureSample {
  double time_s = 0.0;
  double pressure_Pa = 0.0;
};

struct SaltCreepQuery {
  double time_s = 0.0;
  double wall_pressure_Pa = 0.0;
  double temperature_K = 0.0;
  double radial_position_m = 0.0;
};

struct SaltCreepResponse {
  double radial_displacement_m = 0.0;
  double radial_strain = 0.0;
  double effective_closure_pressure_Pa = 0.0;
  bool valid = false;
};

}  // namespace lss::salt
