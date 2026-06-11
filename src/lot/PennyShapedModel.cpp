#include "lot/PennyShapedModel.hpp"

#include <cmath>
#include <numbers>
#include <stdexcept>
#include <string>

namespace lss::lot {
namespace {

void require_finite_positive(double value, const std::string& field) {
  if (!std::isfinite(value) || value <= 0.0) {
    throw std::invalid_argument("PennyShapedModel: " + field +
                                " must be finite and positive");
  }
}

void require_finite_non_negative(double value, const std::string& field) {
  if (!std::isfinite(value) || value < 0.0) {
    throw std::invalid_argument("PennyShapedModel: " + field +
                                " must be finite and non-negative");
  }
}

void validate_poisson_ratio(double poisson_ratio) {
  if (!std::isfinite(poisson_ratio) || poisson_ratio < 0.0 ||
      poisson_ratio >= 0.5) {
    throw std::invalid_argument(
        "PennyShapedModel: poisson_ratio must be finite in [0, 0.5)");
  }
}

void validate_input(const PennyShapedInput& input) {
  require_finite_positive(input.young_modulus_Pa, "young_modulus_Pa");
  validate_poisson_ratio(input.poisson_ratio);
  require_finite_positive(input.viscosity_Pa_min, "viscosity_Pa_min");
  require_finite_non_negative(input.flow_rate_m3_min, "flow_rate_m3_min");
  require_finite_non_negative(input.elapsed_since_opening_min,
                              "elapsed_since_opening_min");
  require_finite_non_negative(input.wellbore_pressure_Pa,
                              "wellbore_pressure_Pa");
  require_finite_positive(input.sigma_theta_compression_positive_Pa,
                          "sigma_theta_compression_positive_Pa");
  require_finite_non_negative(input.volume_multiplier, "volume_multiplier");
}

}  // namespace

double penny_shaped_plane_strain_modulus_Pa(double young_modulus_Pa,
                                            double poisson_ratio) {
  require_finite_positive(young_modulus_Pa, "young_modulus_Pa");
  validate_poisson_ratio(poisson_ratio);
  return young_modulus_Pa / (1.0 - poisson_ratio * poisson_ratio);
}

PennyShapedResult evaluate_penny_shaped_model(const PennyShapedInput& input) {
  validate_input(input);

  PennyShapedResult result;
  result.plane_strain_modulus_Pa = penny_shaped_plane_strain_modulus_Pa(
      input.young_modulus_Pa, input.poisson_ratio);
  result.pressure_factor =
      input.wellbore_pressure_Pa /
      input.sigma_theta_compression_positive_Pa;

  if (input.flow_rate_m3_min == 0.0 ||
      input.elapsed_since_opening_min == 0.0) {
    return result;
  }

  const double mu = input.viscosity_Pa_min;
  const double q = input.flow_rate_m3_min;
  const double epd = result.plane_strain_modulus_Pa;
  const double time = input.elapsed_since_opening_min;

  result.opening_m =
      3.65 * std::pow((mu * mu * q * q * q) / (epd * epd), 1.0 / 9.0) *
      std::pow(time, 1.0 / 9.0);
  result.radius_m =
      0.572 * std::pow((epd * q * q * q) / mu, 1.0 / 9.0) *
      std::pow(time, 4.0 / 9.0);
  result.fracture_volume_proxy_m3 =
      input.volume_multiplier * std::pow(result.opening_m / 2.0, 2.0) *
      result.radius_m * std::numbers::pi * result.pressure_factor;

  return result;
}

}  // namespace lss::lot
