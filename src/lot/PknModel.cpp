#include "lot/PknModel.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>

namespace lss::lot {
namespace {

constexpr double kMinimumWidthM = 1.0e-9;
constexpr double kMinimumTimeS = 1.0e-12;

const char* pressure_model_label(PknPressureModel model) {
  switch (model) {
    case PknPressureModel::PknDirect:
      return "pkn_direct";
    case PknPressureModel::VolumetricBalance:
      return "volumetric_balance";
  }
  throw std::invalid_argument("PknModel: unsupported pressure model");
}

const char* fracture_initiation_label(FractureInitiationCriterion criterion) {
  switch (criterion) {
    case FractureInitiationCriterion::ConstantPressure:
      return "constant_pressure";
    case FractureInitiationCriterion::SigmaThetaStatic:
      return "sigma_theta_static";
  }
  throw std::invalid_argument("PknModel: unsupported fracture initiation criterion");
}

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
  if (!std::isfinite(input.initial_pressure_Pa) || input.initial_pressure_Pa < 0.0) {
    throw std::invalid_argument("PknModel: initial_pressure_Pa must be finite and non-negative");
  }
  for (const auto& phase : input.injection.phases) {
    if (!std::isfinite(phase.duration_s) || phase.duration_s <= 0.0) {
      throw std::invalid_argument("PknModel: injection phase duration_s must be positive");
    }
    if (!std::isfinite(phase.rate_m3_s) || phase.rate_m3_s < 0.0) {
      throw std::invalid_argument("PknModel: injection phase rate_m3_s must be non-negative");
    }
  }
  if (input.initial_width_m < 0.0) {
    throw std::invalid_argument("PknModel: initial_width_m must be non-negative");
  }
  if (input.leakoff.enabled && input.leakoff_coefficient_m_sqrt_s < 0.0) {
    throw std::invalid_argument("PknModel: leakoff coefficient must be non-negative");
  }
  if (input.leakoff.enabled && input.leakoff_constant_rate_m3_s < 0.0) {
    throw std::invalid_argument("PknModel: leakoff constant rate must be non-negative");
  }
  if (input.leakoff.enabled && input.leakoff.coefficient_m_sqrt_s < 0.0) {
    throw std::invalid_argument("PknModel: leakoff.coefficient_m_sqrt_s must be non-negative");
  }
  if (input.leakoff.enabled && input.leakoff.constant_rate_m3_s < 0.0) {
    throw std::invalid_argument("PknModel: leakoff.constant_rate_m3_s must be non-negative");
  }
  if (input.pressure_model == PknPressureModel::VolumetricBalance) {
    if (input.annular_volume_m3 <= 0.0 || !std::isfinite(input.annular_volume_m3)) {
      throw std::invalid_argument(
          "PknModel: volumetric_balance requires positive annular_volume_m3");
    }
    if (input.fluid_compressibility_per_Pa <= 0.0 ||
        !std::isfinite(input.fluid_compressibility_per_Pa)) {
      throw std::invalid_argument(
          "PknModel: volumetric_balance requires positive fluid_compressibility_per_Pa");
    }
  }
  if (input.fracture_initiation ==
      FractureInitiationCriterion::SigmaThetaStatic) {
    const auto& criterion = input.sigma_theta_fracture;
    if (!criterion.enabled) {
      throw std::invalid_argument(
          "PknModel: sigma_theta_static requires enabled criterion");
    }
    if (criterion.layer_id.empty()) {
      throw std::invalid_argument(
          "PknModel: sigma_theta_static requires layer_id");
    }
    if (!std::isfinite(criterion.influence_depth_m) ||
        criterion.influence_depth_m <= 0.0) {
      throw std::invalid_argument(
          "PknModel: sigma_theta_static requires positive influence_depth_m");
    }
    if (!std::isfinite(criterion.sigma_theta_compression_positive_Pa) ||
        criterion.sigma_theta_compression_positive_Pa <= 0.0) {
      throw std::invalid_argument(
          "PknModel: sigma_theta_static requires positive sigma theta");
    }
    if (criterion.pressure_source != "wellbore_pressure_Pa") {
      throw std::invalid_argument(
          "PknModel: sigma_theta_static requires wellbore_pressure_Pa source");
    }
    if (criterion.comparison != "legacy_algebra") {
      throw std::invalid_argument(
          "PknModel: sigma_theta_static requires legacy_algebra comparison");
    }
  }
}

PknResult make_point(const PknInput& input, double elapsed_time_s,
                     double previous_leakoff_m3 = 0.0) {
  const double active_time_s =
      input.injection.active_injection_time_s(elapsed_time_s);
  const double injected_volume_m3 = input.injection.injected_volume_m3(elapsed_time_s);
  const double reference_rate_m3_s =
      std::max(input.injection.reference_rate_m3_s(elapsed_time_s), kMinimumTimeS);

  const double scaling_time_s = std::max(active_time_s, kMinimumTimeS);
  const double scaled_width_m = 2.5 * std::pow(input.fluid_viscosity_Pa_s *
                                                   reference_rate_m3_s *
                                                   reference_rate_m3_s *
                                                   scaling_time_s /
                                                   (input.plane_strain_modulus_Pa *
                                                    input.fracture_height_m),
                                               1.0 / 5.0);
  const double width_m =
      std::max({input.initial_width_m, scaled_width_m, kMinimumWidthM});

  double leakoff_volume_m3 = 0.0;
  if (input.leakoff.enabled && injected_volume_m3 > 0.0) {
    const double previous_elapsed_time_s =
        std::max(0.0, elapsed_time_s - input.injection.dt_s);
    const double previous_injected_volume_m3 =
        input.injection.injected_volume_m3(previous_elapsed_time_s);
    const double previous_fracture_volume_m3 =
        std::max(0.0, previous_injected_volume_m3 - previous_leakoff_m3);
    const double previous_length_m =
        previous_fracture_volume_m3 /
        (std::max(width_m, kMinimumWidthM) * input.fracture_height_m);
    const double leakoff_area_m2 = 2.0 * input.fracture_height_m *
                                   std::max(previous_length_m, kMinimumWidthM);
    LeakoffInput leakoff_input;
    leakoff_input.model = input.leakoff.model;
    leakoff_input.coefficient_m_sqrt_s =
        input.leakoff.coefficient_m_sqrt_s > 0.0
            ? input.leakoff.coefficient_m_sqrt_s
            : input.leakoff_coefficient_m_sqrt_s;
    leakoff_input.constant_rate_m3_s =
        input.leakoff.constant_rate_m3_s > 0.0 ? input.leakoff.constant_rate_m3_s
                                               : input.leakoff_constant_rate_m3_s;
    leakoff_input.area_m2 = leakoff_area_m2;

    const LeakoffState leakoff_state{
        std::max(0.0, elapsed_time_s - input.injection.accommodation_time_s -
                          input.injection.dt_s),
        input.injection.dt_s,
        previous_leakoff_m3,
    };
    const LeakoffStepResult leakoff_step =
        compute_leakoff_step(leakoff_input, leakoff_state);
    leakoff_volume_m3 = std::min(injected_volume_m3,
                                 leakoff_step.cumulative_volume_m3);
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
  result.pressure_model = pressure_model_label(input.pressure_model);
  result.initial_pressure_Pa = input.initial_pressure_Pa;

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
  series.initial_pressure_series_Pa.push_back(point.initial_pressure_Pa);
  series.leakoff_volume_series_m3.push_back(point.leakoff_volume_m3);
  series.fracture_volume_series_m3.push_back(point.fracture_volume_m3);
  series.wellbore_pressure_series_Pa.push_back(point.wellbore_pressure_Pa);
  series.balance_delta_pressure_series_Pa.push_back(point.balance_delta_pressure_Pa);
  series.balance_effective_volume_increment_series_m3.push_back(
      point.balance_effective_volume_increment_m3);
  series.balance_injected_volume_increment_series_m3.push_back(
      point.balance_injected_volume_increment_m3);
  series.balance_fracture_volume_increment_series_m3.push_back(
      point.balance_fracture_volume_increment_m3);
  series.balance_leakoff_volume_increment_series_m3.push_back(
      point.balance_leakoff_volume_increment_m3);
  series.fracture_initiation_pressure_series_Pa.push_back(
      point.fracture_initiation_pressure_Pa);
  series.fracture_initiation_sigma_theta_series_Pa.push_back(
      point.fracture_initiation_sigma_theta_Pa);
  series.fracture_initiation_margin_series_Pa.push_back(
      point.fracture_initiation_margin_Pa);
  series.fracture_initiated_series.push_back(point.fracture_initiated ? 1 : 0);
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
  target.pressure_model = point.pressure_model;
  target.initial_pressure_Pa = point.initial_pressure_Pa;
  target.wellbore_pressure_Pa = point.wellbore_pressure_Pa;
  target.fluid_compressibility_per_Pa = point.fluid_compressibility_per_Pa;
  target.balance_delta_pressure_Pa = point.balance_delta_pressure_Pa;
  target.balance_effective_volume_increment_m3 =
      point.balance_effective_volume_increment_m3;
  target.balance_injected_volume_increment_m3 =
      point.balance_injected_volume_increment_m3;
  target.balance_fracture_volume_increment_m3 =
      point.balance_fracture_volume_increment_m3;
  target.balance_leakoff_volume_increment_m3 =
      point.balance_leakoff_volume_increment_m3;
  target.fracture_initiated = point.fracture_initiated;
  target.fracture_initiation_time_s = point.fracture_initiation_time_s;
  target.fracture_initiation_pressure_Pa =
      point.fracture_initiation_pressure_Pa;
  target.fracture_initiation_sigma_theta_Pa =
      point.fracture_initiation_sigma_theta_Pa;
  target.fracture_initiation_margin_Pa = point.fracture_initiation_margin_Pa;
  target.fracture_initiation_type = point.fracture_initiation_type;
  target.fracture_initiation_layer_id = point.fracture_initiation_layer_id;
  target.fracture_initiation_depth_m = point.fracture_initiation_depth_m;
  target.fracture_initiation_source = point.fracture_initiation_source;
}

void apply_volumetric_balance(const PknInput& input, PknResult& series) {
  double previous_injected_m3 = 0.0;
  double previous_fracture_m3 = 0.0;
  double previous_leakoff_m3 = 0.0;
  double pressure_Pa = input.initial_pressure_Pa;
  bool fracture_opened = false;
  double initiation_pressure_Pa = 0.0;
  double initiation_sigma_theta_Pa = 0.0;
  double initiation_margin_Pa = 0.0;
  double initiation_time_s = 0.0;

  for (std::size_t i = 0; i < series.time_series_s.size(); ++i) {
    const double injected_increment_m3 =
        series.injected_volume_series_m3[i] - previous_injected_m3;
    double fracture_increment_m3 = 0.0;
    double leakoff_increment_m3 = 0.0;

    const double trial_delta_pressure_Pa =
        injected_increment_m3 /
        (input.fluid_compressibility_per_Pa * input.annular_volume_m3);
    const double trial_pressure_Pa =
        std::max(0.0, pressure_Pa + trial_delta_pressure_Pa);

    if (!fracture_opened) {
      if (input.fracture_initiation ==
          FractureInitiationCriterion::SigmaThetaStatic) {
        const double sigma_theta_Pa =
            input.sigma_theta_fracture.sigma_theta_compression_positive_Pa;
        const double margin_Pa = trial_pressure_Pa - sigma_theta_Pa;
        if (margin_Pa > 0.0) {
          fracture_opened = true;
          initiation_pressure_Pa = trial_pressure_Pa;
          initiation_sigma_theta_Pa = sigma_theta_Pa;
          initiation_margin_Pa = margin_Pa;
          initiation_time_s = series.time_series_s[i];
        }
      } else if (input.breakdown.pressure_Pa > 0.0 &&
                 trial_pressure_Pa - input.initial_pressure_Pa >=
                     input.breakdown.pressure_Pa) {
        fracture_opened = true;
        initiation_pressure_Pa = trial_pressure_Pa;
        initiation_margin_Pa =
            trial_pressure_Pa - input.initial_pressure_Pa -
            input.breakdown.pressure_Pa;
        initiation_time_s = series.time_series_s[i];
      }
    }

    if (fracture_opened) {
      fracture_increment_m3 =
          std::max(0.0, series.fracture_volume_series_m3[i] - previous_fracture_m3);
      leakoff_increment_m3 = series.leakoff_volume_series_m3[i] - previous_leakoff_m3;
    }

    const double effective_increment_m3 =
        injected_increment_m3 - fracture_increment_m3 - leakoff_increment_m3;
    const double delta_pressure_Pa =
        effective_increment_m3 /
        (input.fluid_compressibility_per_Pa * input.annular_volume_m3);
    pressure_Pa = std::max(0.0, pressure_Pa + delta_pressure_Pa);

    series.wellbore_pressure_series_Pa[i] = pressure_Pa;
    series.balance_delta_pressure_series_Pa[i] = delta_pressure_Pa;
    series.balance_effective_volume_increment_series_m3[i] = effective_increment_m3;
    series.balance_injected_volume_increment_series_m3[i] = injected_increment_m3;
    series.balance_fracture_volume_increment_series_m3[i] = fracture_increment_m3;
    series.balance_leakoff_volume_increment_series_m3[i] = leakoff_increment_m3;
    series.fracture_initiated_series[i] = fracture_opened ? 1 : 0;
    series.fracture_initiation_pressure_series_Pa[i] = initiation_pressure_Pa;
    series.fracture_initiation_sigma_theta_series_Pa[i] =
        initiation_sigma_theta_Pa;
    series.fracture_initiation_margin_series_Pa[i] = initiation_margin_Pa;

    previous_injected_m3 = series.injected_volume_series_m3[i];
    previous_fracture_m3 = series.fracture_volume_series_m3[i];
    previous_leakoff_m3 = series.leakoff_volume_series_m3[i];
  }

  series.pressure_model = pressure_model_label(input.pressure_model);
  series.fracture_initiation_type =
      fracture_initiation_label(input.fracture_initiation);
  series.fracture_initiation_layer_id = input.sigma_theta_fracture.layer_id;
  series.fracture_initiation_depth_m =
      input.sigma_theta_fracture.influence_depth_m;
  series.fracture_initiation_source = input.sigma_theta_fracture.source;
  series.fluid_compressibility_per_Pa = input.fluid_compressibility_per_Pa;
  if (!series.time_series_s.empty()) {
    series.wellbore_pressure_Pa = series.wellbore_pressure_series_Pa.back();
    series.balance_delta_pressure_Pa = series.balance_delta_pressure_series_Pa.back();
    series.balance_effective_volume_increment_m3 =
        series.balance_effective_volume_increment_series_m3.back();
    series.balance_injected_volume_increment_m3 =
        series.balance_injected_volume_increment_series_m3.back();
    series.balance_fracture_volume_increment_m3 =
        series.balance_fracture_volume_increment_series_m3.back();
    series.balance_leakoff_volume_increment_m3 =
        series.balance_leakoff_volume_increment_series_m3.back();
    series.fracture_initiated = fracture_opened;
    series.fracture_initiation_time_s = initiation_time_s;
    series.fracture_initiation_pressure_Pa = initiation_pressure_Pa;
    series.fracture_initiation_sigma_theta_Pa = initiation_sigma_theta_Pa;
    series.fracture_initiation_margin_Pa = initiation_margin_Pa;
  }
}

}  // namespace

PknResult PknModel::evaluate(const PknInput& input, double elapsed_time_s) const {
  if (elapsed_time_s < 0.0) {
    throw std::invalid_argument("PknModel: elapsed_time_s must be non-negative");
  }
  validate_input(input);
  PknResult point = make_point(input, elapsed_time_s);
  point.pressure_model = pressure_model_label(input.pressure_model);
  point.fluid_compressibility_per_Pa = input.fluid_compressibility_per_Pa;
  return point;
}

PknResult PknModel::simulate(const PknInput& input) const {
  validate_input(input);

  PknResult series;
  double previous_leakoff_m3 = 0.0;
  const double total_time_s = input.injection.scheduled_total_time_s();
  const auto step_count =
      static_cast<std::size_t>(std::floor(total_time_s /
                                          input.injection.dt_s));
  for (std::size_t step = 0; step <= step_count; ++step) {
    const double time_s =
        std::min(total_time_s,
                 static_cast<double>(step) * input.injection.dt_s);
    const PknResult point = make_point(input, time_s, previous_leakoff_m3);
    append_point(series, point);
    previous_leakoff_m3 = point.leakoff_volume_m3;
    copy_scalar_result(series, point);
  }

  if (series.time_series_s.empty() ||
      series.time_series_s.back() < total_time_s) {
    const PknResult point =
        make_point(input, total_time_s, previous_leakoff_m3);
    append_point(series, point);
    copy_scalar_result(series, point);
  }
  if (input.pressure_model == PknPressureModel::VolumetricBalance) {
    apply_volumetric_balance(input, series);
  } else {
    series.pressure_model = pressure_model_label(input.pressure_model);
  }
  return series;
}

}  // namespace lss::lot
