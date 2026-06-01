#include "lot/PknModel.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>

namespace lss::lot {
namespace {

constexpr double kMinimumWidthM = 1.0e-9;
constexpr double kMinimumTimeS = 1.0e-12;

void validate_input(const PknInput& input) {
  if (input.fracture_height_m <= 0.0) {
    throw std::invalid_argument("PknModel: fracture_height_m must be positive");
  }
  if (input.plane_strain_modulus_Pa <= 0.0) {
    throw std::invalid_argument("PknModel: plane_strain_modulus_Pa must be positive");
  }
  if (input.fluid_viscosity_Pa_s <= 0.0) {
    throw std::invalid_argument("PknModel: fluid_viscosity_Pa_s must be positive");
  }
  if (input.injection.rate_m3_s <= 0.0) {
    throw std::invalid_argument("PknModel: injection rate must be positive");
  }
  if (input.injection.dt_s <= 0.0) {
    throw std::invalid_argument("PknModel: dt_s must be positive");
  }
  if (input.injection.total_time_s <= 0.0) {
    throw std::invalid_argument("PknModel: total_time_s must be positive");
  }
  if (input.injection.dt_s > input.injection.total_time_s) {
    throw std::invalid_argument("PknModel: dt_s must not exceed total_time_s");
  }
  if (input.injection.accommodation_time_s < 0.0) {
    throw std::invalid_argument("PknModel: accommodation_time_s must be non-negative");
  }
  if (input.initial_width_m < 0.0) {
    throw std::invalid_argument("PknModel: initial_width_m must be non-negative");
  }
  if (input.leakoff.enabled && input.leakoff_coefficient_m_sqrt_s < 0.0) {
    throw std::invalid_argument("PknModel: leakoff coefficient must be non-negative");
  }
}

PknResult make_point(const PknInput& input, double elapsed_time_s,
                     double previous_leakoff_m3 = 0.0) {
  const double active_time_s =
      std::max(0.0, elapsed_time_s - input.injection.accommodation_time_s);
  const double injected_volume_m3 = input.injection.rate_m3_s * active_time_s;

  const double scaling_time_s = std::max(active_time_s, kMinimumTimeS);
  const double scaled_width_m = 2.5 * std::pow(input.fluid_viscosity_Pa_s *
                                                   input.injection.rate_m3_s *
                                                   input.injection.rate_m3_s *
                                                   scaling_time_s /
                                                   (input.plane_strain_modulus_Pa *
                                                    input.fracture_height_m),
                                               1.0 / 5.0);
  const double width_m =
      std::max({input.initial_width_m, scaled_width_m, kMinimumWidthM});

  double leakoff_volume_m3 = 0.0;
  if (input.leakoff.enabled && injected_volume_m3 > 0.0) {
    const double previous_fracture_volume_m3 =
        std::max(0.0, input.injection.rate_m3_s *
                          std::max(0.0, elapsed_time_s - input.injection.dt_s -
                                            input.injection.accommodation_time_s) -
                          previous_leakoff_m3);
    const double previous_length_m =
        previous_fracture_volume_m3 /
        (std::max(width_m, kMinimumWidthM) * input.fracture_height_m);
    const double leakoff_area_m2 = 2.0 * input.fracture_height_m *
                                   std::max(previous_length_m, kMinimumWidthM);
    const double incremental_leakoff_m3 =
        input.leakoff_coefficient_m_sqrt_s * leakoff_area_m2 *
        std::sqrt(input.injection.dt_s);
    leakoff_volume_m3 =
        std::min(injected_volume_m3, previous_leakoff_m3 + incremental_leakoff_m3);
  }

  const double fracture_volume_m3 =
      std::max(0.0, injected_volume_m3 - leakoff_volume_m3);
  const double length_m =
      fracture_volume_m3 /
      (std::max(width_m, kMinimumWidthM) * input.fracture_height_m);
  const double net_pressure_Pa =
      std::max(0.0, input.plane_strain_modulus_Pa * width_m /
                        input.fracture_height_m);

  PknResult result;
  result.time_s = elapsed_time_s;
  result.injected_volume_m3 = injected_volume_m3;
  result.width_m = width_m;
  result.fracture_width_m = width_m;
  result.length_m = length_m;
  result.fracture_length_m = length_m;
  result.fracture_volume_m3 = fracture_volume_m3;
  result.volume_m3 = fracture_volume_m3;
  result.leakoff_volume_m3 = leakoff_volume_m3;
  result.net_pressure_Pa = net_pressure_Pa;

  if (!std::isfinite(result.time_s) || !std::isfinite(result.injected_volume_m3) ||
      !std::isfinite(result.width_m) || !std::isfinite(result.length_m) ||
      !std::isfinite(result.fracture_volume_m3) ||
      !std::isfinite(result.leakoff_volume_m3) ||
      !std::isfinite(result.net_pressure_Pa)) {
    throw std::runtime_error("PknModel: non-finite SI result");
  }
  return result;
}

void append_point(PknResult& series, const PknResult& point) {
  series.time_series_s.push_back(point.time_s);
  series.injected_volume_series_m3.push_back(point.injected_volume_m3);
  series.fracture_length_series_m.push_back(point.length_m);
  series.fracture_width_series_m.push_back(point.width_m);
  series.net_pressure_series_Pa.push_back(point.net_pressure_Pa);
  series.leakoff_volume_series_m3.push_back(point.leakoff_volume_m3);
  series.fracture_volume_series_m3.push_back(point.fracture_volume_m3);
}

void copy_scalar_result(PknResult& target, const PknResult& point) {
  target.time_s = point.time_s;
  target.injected_volume_m3 = point.injected_volume_m3;
  target.width_m = point.width_m;
  target.fracture_width_m = point.fracture_width_m;
  target.length_m = point.length_m;
  target.fracture_length_m = point.fracture_length_m;
  target.fracture_volume_m3 = point.fracture_volume_m3;
  target.volume_m3 = point.volume_m3;
  target.leakoff_volume_m3 = point.leakoff_volume_m3;
  target.net_pressure_Pa = point.net_pressure_Pa;
}

}  // namespace

PknResult PknModel::evaluate(const PknInput& input, double elapsed_time_s) const {
  if (elapsed_time_s < 0.0) {
    throw std::invalid_argument("PknModel: elapsed_time_s must be non-negative");
  }
  validate_input(input);
  return make_point(input, elapsed_time_s);
}

PknResult PknModel::simulate(const PknInput& input) const {
  validate_input(input);

  PknResult series;
  double previous_leakoff_m3 = 0.0;
  const auto step_count =
      static_cast<std::size_t>(std::floor(input.injection.total_time_s /
                                          input.injection.dt_s));
  for (std::size_t step = 0; step <= step_count; ++step) {
    const double time_s =
        std::min(input.injection.total_time_s,
                 static_cast<double>(step) * input.injection.dt_s);
    const PknResult point = make_point(input, time_s, previous_leakoff_m3);
    append_point(series, point);
    previous_leakoff_m3 = point.leakoff_volume_m3;
    copy_scalar_result(series, point);
  }

  if (series.time_series_s.empty() ||
      series.time_series_s.back() < input.injection.total_time_s) {
    const PknResult point =
        make_point(input, input.injection.total_time_s, previous_leakoff_m3);
    append_point(series, point);
    copy_scalar_result(series, point);
  }
  return series;
}

}  // namespace lss::lot
