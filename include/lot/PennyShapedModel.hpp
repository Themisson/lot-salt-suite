#pragma once

namespace lss::lot {

struct PennyShapedInput {
  double young_modulus_Pa = 0.0;
  double poisson_ratio = 0.0;
  double viscosity_Pa_min = 0.0;
  double flow_rate_m3_min = 0.0;
  double elapsed_since_opening_min = 0.0;
  double wellbore_pressure_Pa = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  double volume_multiplier = 10.0;
};

struct PennyShapedResult {
  double plane_strain_modulus_Pa = 0.0;
  double opening_m = 0.0;
  double radius_m = 0.0;
  double pressure_factor = 0.0;
  double fracture_volume_proxy_m3 = 0.0;
};

[[nodiscard]] double penny_shaped_plane_strain_modulus_Pa(
    double young_modulus_Pa,
    double poisson_ratio);

[[nodiscard]] PennyShapedResult evaluate_penny_shaped_model(
    const PennyShapedInput& input);

}  // namespace lss::lot
