#pragma once

#include <vector>

namespace lss::salt {

struct SaltWallStressSample {
  int gp_id = -1;
  int element_id = -1;
  int local_gp_id = -1;

  double r_m = 0.0;
  double z_m = 0.0;
  double depth_m = 0.0;

  double sigma_rr_Pa = 0.0;
  double sigma_theta_Pa = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  double sigma_zz_Pa = 0.0;
  double sigma_rz_Pa = 0.0;

  double mean_stress_Pa = 0.0;
  double j2_Pa2 = 0.0;
  double von_mises_effective_stress_Pa = 0.0;
};

struct SaltWallStressDiagnostics {
  std::vector<SaltWallStressSample> wall_samples;
  bool valid = false;
};

}  // namespace lss::salt
