#include "lot/PknModel.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>

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

const char* sink_timing_label(FractureSinkTiming timing) {
  switch (timing) {
    case FractureSinkTiming::SameStep:
      return "same_step";
    case FractureSinkTiming::NextStep:
      return "next_step";
  }
  throw std::invalid_argument("PknModel: unsupported fracture sink timing");
}

const char* fracture_initiation_label(FractureInitiationCriterion criterion) {
  switch (criterion) {
    case FractureInitiationCriterion::ConstantPressure:
      return "constant_pressure";
    case FractureInitiationCriterion::SigmaThetaStatic:
      return "sigma_theta_static";
    case FractureInitiationCriterion::SigmaThetaProviderRuntime:
      return "sigma_theta_provider_runtime";
  }
  throw std::invalid_argument("PknModel: unsupported fracture initiation criterion");
}

void validate_sigma_theta_point(const SigmaThetaRuntimePoint& point) {
  if (!point.valid) {
    throw std::invalid_argument("PknModel: sigma theta provider returned invalid point");
  }
  if (!std::isfinite(point.time_s) || point.time_s < 0.0) {
    throw std::invalid_argument(
        "PknModel: sigma theta provider returned invalid time_s");
  }
  if (!std::isfinite(point.sigma_theta_compression_positive_Pa) ||
      point.sigma_theta_compression_positive_Pa <= 0.0) {
    throw std::invalid_argument(
        "PknModel: sigma theta provider returned non-positive sigma theta");
  }
  if (!std::isfinite(point.influence_depth_m) ||
      point.influence_depth_m < 0.0) {
    throw std::invalid_argument(
        "PknModel: sigma theta provider returned invalid influence_depth_m");
  }
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
    const auto& compliance = input.volumetric_compliance;
    if (compliance.enabled) {
      if (compliance.model != "constant_geometric" &&
          compliance.model != "elastic_annular_simple") {
        throw std::invalid_argument(
            "PknModel: unsupported volumetric compliance model");
      }
      if (compliance.total_compressibility_per_Pa != 0.0) {
        throw std::invalid_argument(
            "PknModel: total_compressibility_per_Pa is not supported");
      }
      if (compliance.model == "constant_geometric") {
        if (!std::isfinite(compliance.geometric_compressibility_per_Pa) ||
            compliance.geometric_compressibility_per_Pa < 0.0) {
          throw std::invalid_argument(
              "PknModel: geometric_compressibility_per_Pa must be finite and non-negative");
        }
      } else {
        (void)elasticAnnularGeometricCompressibility(
            compliance.inner_radius_m, compliance.outer_radius_m,
            compliance.inner_wall_thickness_m,
            compliance.inner_young_modulus_Pa, compliance.inner_poisson_ratio,
            compliance.formation_young_modulus_Pa,
            compliance.formation_poisson_ratio);
      }
    }
  }
  if (input.pressure_model == PknPressureModel::VolumetricBalance &&
      input.fracture_initiation ==
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
  if (input.pressure_model == PknPressureModel::VolumetricBalance &&
      input.fracture_initiation ==
          FractureInitiationCriterion::SigmaThetaProviderRuntime &&
      input.sigma_theta_provider == nullptr) {
    throw std::invalid_argument(
        "PknModel: sigma_theta_provider_runtime requires provider");
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
  series.sink_deferred_this_step_series.push_back(
      point.sink_deferred_this_step ? 1 : 0);
  series.sink_active_this_step_series.push_back(
      point.sink_active_this_step ? 1 : 0);
  series.fracture_initiated_before_step_series.push_back(
      point.fracture_initiated_before_step ? 1 : 0);
  series.fracture_initiated_after_step_series.push_back(
      point.fracture_initiated_after_step ? 1 : 0);
  series.fracture_started_this_step_series.push_back(
      point.fracture_started_this_step ? 1 : 0);
  series.fracture_sink_applied_series_m3.push_back(
      point.fracture_sink_applied_m3);
  series.leakoff_sink_applied_series_m3.push_back(point.leakoff_sink_applied_m3);
  series.fracture_initiation_pressure_series_Pa.push_back(
      point.fracture_initiation_pressure_Pa);
  series.fracture_initiation_sigma_theta_series_Pa.push_back(
      point.fracture_initiation_sigma_theta_Pa);
  series.fracture_initiation_margin_series_Pa.push_back(
      point.fracture_initiation_margin_Pa);
  series.sigma_theta_lookup_time_series_s.push_back(
      point.sigma_theta_lookup_time_s);
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
  target.sink_timing = point.sink_timing;
  target.sink_deferred_this_step = point.sink_deferred_this_step;
  target.sink_active_this_step = point.sink_active_this_step;
  target.fracture_initiated_before_step =
      point.fracture_initiated_before_step;
  target.fracture_initiated_after_step = point.fracture_initiated_after_step;
  target.fracture_started_this_step = point.fracture_started_this_step;
  target.fracture_sink_applied_m3 = point.fracture_sink_applied_m3;
  target.leakoff_sink_applied_m3 = point.leakoff_sink_applied_m3;
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
  target.sigma_theta_provider_type = point.sigma_theta_provider_type;
  target.sigma_theta_source = point.sigma_theta_source;
  target.sigma_theta_lookup_time_s = point.sigma_theta_lookup_time_s;
  target.sigma_theta_layer_id = point.sigma_theta_layer_id;
  target.sigma_theta_mapping_status = point.sigma_theta_mapping_status;
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
  double sigma_theta_lookup_time_s = 0.0;
  std::string sigma_theta_layer_id;
  std::string sigma_theta_source;
  std::string sigma_theta_mapping_status;
  double geometric_compressibility_per_Pa = 0.0;
  std::string mechanical_compliance_status = "none";
  if (input.volumetric_compliance.enabled) {
    if (input.volumetric_compliance.model == "elastic_annular_simple") {
      geometric_compressibility_per_Pa = elasticAnnularGeometricCompressibility(
          input.volumetric_compliance.inner_radius_m,
          input.volumetric_compliance.outer_radius_m,
          input.volumetric_compliance.inner_wall_thickness_m,
          input.volumetric_compliance.inner_young_modulus_Pa,
          input.volumetric_compliance.inner_poisson_ratio,
          input.volumetric_compliance.formation_young_modulus_Pa,
          input.volumetric_compliance.formation_poisson_ratio);
      mechanical_compliance_status = "computed_elastic_annular_simple";
    } else {
      geometric_compressibility_per_Pa =
          input.volumetric_compliance.geometric_compressibility_per_Pa;
      mechanical_compliance_status = "constant_geometric_input";
    }
  }
  const double effective_compressibility_per_Pa =
      effectiveCompressibility(input.fluid_compressibility_per_Pa,
                               geometric_compressibility_per_Pa);

  for (std::size_t i = 0; i < series.time_series_s.size(); ++i) {
    const bool fracture_initiated_before_step = fracture_opened;
    const double injected_increment_m3 =
        series.injected_volume_series_m3[i] - previous_injected_m3;
    double fracture_increment_m3 = 0.0;
    double leakoff_increment_m3 = 0.0;
    bool fracture_started_this_step = false;
    bool sink_deferred_this_step = false;
    bool sink_active_this_step = false;

    const double trial_delta_pressure_Pa =
        volumetricPressureIncrement(injected_increment_m3,
                                    input.annular_volume_m3,
                                    effective_compressibility_per_Pa);
    const double trial_pressure_Pa =
        std::max(0.0, pressure_Pa + trial_delta_pressure_Pa);

    if (!fracture_opened) {
      if (input.fracture_initiation ==
          FractureInitiationCriterion::SigmaThetaStatic) {
        const double sigma_theta_Pa =
            input.sigma_theta_fracture.sigma_theta_compression_positive_Pa;
        const double margin_Pa = trial_pressure_Pa - sigma_theta_Pa;
        sigma_theta_lookup_time_s = series.time_series_s[i];
        sigma_theta_layer_id = input.sigma_theta_fracture.layer_id;
        sigma_theta_source = input.sigma_theta_fracture.source;
        sigma_theta_mapping_status = input.sigma_theta_fracture.mapping_status;
        if (margin_Pa > 0.0) {
          fracture_opened = true;
          fracture_started_this_step = !fracture_initiated_before_step;
          initiation_pressure_Pa = trial_pressure_Pa;
          initiation_sigma_theta_Pa = sigma_theta_Pa;
          initiation_margin_Pa = margin_Pa;
          initiation_time_s = series.time_series_s[i];
        }
      } else if (input.fracture_initiation ==
                 FractureInitiationCriterion::SigmaThetaProviderRuntime) {
        const SigmaThetaRuntimePoint sigma_theta =
            input.sigma_theta_provider->sample(series.time_series_s[i],
                                               trial_pressure_Pa);
        validate_sigma_theta_point(sigma_theta);
        const double margin_Pa =
            trial_pressure_Pa -
            sigma_theta.sigma_theta_compression_positive_Pa;
        sigma_theta_lookup_time_s = sigma_theta.time_s;
        sigma_theta_layer_id = sigma_theta.layer_id;
        sigma_theta_source = sigma_theta.source;
        sigma_theta_mapping_status = sigma_theta.mapping_status;
        if (margin_Pa > 0.0) {
          fracture_opened = true;
          fracture_started_this_step = !fracture_initiated_before_step;
          initiation_pressure_Pa = trial_pressure_Pa;
          initiation_sigma_theta_Pa =
              sigma_theta.sigma_theta_compression_positive_Pa;
          initiation_margin_Pa = margin_Pa;
          initiation_time_s = series.time_series_s[i];
        }
      } else if (input.breakdown.pressure_Pa > 0.0 &&
                 trial_pressure_Pa - input.initial_pressure_Pa >=
                     input.breakdown.pressure_Pa) {
        fracture_opened = true;
        fracture_started_this_step = !fracture_initiated_before_step;
        initiation_pressure_Pa = trial_pressure_Pa;
        initiation_margin_Pa =
            trial_pressure_Pa - input.initial_pressure_Pa -
            input.breakdown.pressure_Pa;
        initiation_time_s = series.time_series_s[i];
      }
    }

    bool apply_sink_this_step = fracture_opened;
    if (input.sink_timing == FractureSinkTiming::NextStep &&
        fracture_started_this_step) {
      apply_sink_this_step = false;
      sink_deferred_this_step = true;
    }

    if (apply_sink_this_step) {
      fracture_increment_m3 =
          std::max(0.0, series.fracture_volume_series_m3[i] - previous_fracture_m3);
      leakoff_increment_m3 = series.leakoff_volume_series_m3[i] - previous_leakoff_m3;
      sink_active_this_step = fracture_opened;
    }

    const double effective_increment_m3 =
        injected_increment_m3 - fracture_increment_m3 - leakoff_increment_m3;
    const double delta_pressure_Pa =
        volumetricPressureIncrement(effective_increment_m3,
                                    input.annular_volume_m3,
                                    effective_compressibility_per_Pa);
    pressure_Pa = std::max(0.0, pressure_Pa + delta_pressure_Pa);

    series.wellbore_pressure_series_Pa[i] = pressure_Pa;
    series.balance_delta_pressure_series_Pa[i] = delta_pressure_Pa;
    series.balance_effective_volume_increment_series_m3[i] = effective_increment_m3;
    series.balance_injected_volume_increment_series_m3[i] = injected_increment_m3;
    series.balance_fracture_volume_increment_series_m3[i] = fracture_increment_m3;
    series.balance_leakoff_volume_increment_series_m3[i] = leakoff_increment_m3;
    series.sink_deferred_this_step_series[i] = sink_deferred_this_step ? 1 : 0;
    series.sink_active_this_step_series[i] = sink_active_this_step ? 1 : 0;
    series.fracture_initiated_before_step_series[i] =
        fracture_initiated_before_step ? 1 : 0;
    series.fracture_initiated_after_step_series[i] = fracture_opened ? 1 : 0;
    series.fracture_started_this_step_series[i] =
        fracture_started_this_step ? 1 : 0;
    series.fracture_sink_applied_series_m3[i] = fracture_increment_m3;
    series.leakoff_sink_applied_series_m3[i] = leakoff_increment_m3;
    series.fracture_initiated_series[i] = fracture_opened ? 1 : 0;
    series.fracture_initiation_pressure_series_Pa[i] = initiation_pressure_Pa;
    series.fracture_initiation_sigma_theta_series_Pa[i] =
        initiation_sigma_theta_Pa;
    series.fracture_initiation_margin_series_Pa[i] = initiation_margin_Pa;
    series.sigma_theta_lookup_time_series_s[i] = sigma_theta_lookup_time_s;

    previous_injected_m3 = series.injected_volume_series_m3[i];
    previous_fracture_m3 = series.fracture_volume_series_m3[i];
    previous_leakoff_m3 = series.leakoff_volume_series_m3[i];
  }

  series.pressure_model = pressure_model_label(input.pressure_model);
  series.sink_timing = sink_timing_label(input.sink_timing);
  series.fracture_initiation_type =
      fracture_initiation_label(input.fracture_initiation);
  series.fracture_initiation_layer_id = input.sigma_theta_fracture.layer_id;
  series.fracture_initiation_depth_m =
      input.sigma_theta_fracture.influence_depth_m;
  series.fracture_initiation_source = input.sigma_theta_fracture.source;
  series.sigma_theta_provider_type =
      input.fracture_initiation ==
              FractureInitiationCriterion::SigmaThetaProviderRuntime
          ? "runtime"
          : (input.fracture_initiation ==
                     FractureInitiationCriterion::SigmaThetaStatic
                 ? "static"
                 : "none");
  series.sigma_theta_source = sigma_theta_source;
  series.sigma_theta_lookup_time_s = sigma_theta_lookup_time_s;
  series.sigma_theta_layer_id = sigma_theta_layer_id;
  series.sigma_theta_mapping_status = sigma_theta_mapping_status;
  series.fluid_compressibility_per_Pa = input.fluid_compressibility_per_Pa;
  series.geometric_compressibility_per_Pa = geometric_compressibility_per_Pa;
  series.effective_compressibility_per_Pa = effective_compressibility_per_Pa;
  series.compliance_model =
      input.volumetric_compliance.enabled ? input.volumetric_compliance.model : "none";
  series.compliance_source = input.volumetric_compliance.source;
  series.mechanical_compliance_status = mechanical_compliance_status;
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
    series.sink_deferred_this_step =
        series.sink_deferred_this_step_series.back() != 0;
    series.sink_active_this_step =
        series.sink_active_this_step_series.back() != 0;
    series.fracture_initiated_before_step =
        series.fracture_initiated_before_step_series.back() != 0;
    series.fracture_initiated_after_step =
        series.fracture_initiated_after_step_series.back() != 0;
    series.fracture_started_this_step =
        series.fracture_started_this_step_series.back() != 0;
    series.fracture_sink_applied_m3 =
        series.fracture_sink_applied_series_m3.back();
    series.leakoff_sink_applied_m3 =
        series.leakoff_sink_applied_series_m3.back();
    series.fracture_initiated = fracture_opened;
    series.fracture_initiation_time_s = initiation_time_s;
    series.fracture_initiation_pressure_Pa = initiation_pressure_Pa;
    series.fracture_initiation_sigma_theta_Pa = initiation_sigma_theta_Pa;
    series.fracture_initiation_margin_Pa = initiation_margin_Pa;
    series.sigma_theta_lookup_time_s = sigma_theta_lookup_time_s;
  }
}

}  // namespace

double effectiveCompressibility(double fluid_compressibility,
                                double geometric_compressibility) {
  if (!std::isfinite(fluid_compressibility) || fluid_compressibility <= 0.0) {
    throw std::invalid_argument(
        "PknModel: fluid_compressibility must be finite and positive");
  }
  if (!std::isfinite(geometric_compressibility) ||
      geometric_compressibility < 0.0) {
    throw std::invalid_argument(
        "PknModel: geometric_compressibility must be finite and non-negative");
  }
  const double effective = fluid_compressibility + geometric_compressibility;
  if (!std::isfinite(effective) || effective <= 0.0) {
    throw std::invalid_argument(
        "PknModel: effective compressibility must be finite and positive");
  }
  return effective;
}

double elasticAnnularGeometricCompressibility(
    double inner_radius_m, double outer_radius_m,
    double inner_wall_thickness_m, double inner_young_modulus_Pa,
    double inner_poisson_ratio, double formation_young_modulus_Pa,
    double formation_poisson_ratio) {
  if (!std::isfinite(inner_radius_m) || inner_radius_m <= 0.0 ||
      !std::isfinite(outer_radius_m) || outer_radius_m <= inner_radius_m) {
    throw std::invalid_argument(
        "PknModel: elastic_annular_simple requires outer_radius > inner_radius > 0");
  }
  if (!std::isfinite(inner_wall_thickness_m) ||
      inner_wall_thickness_m <= 0.0) {
    throw std::invalid_argument(
        "PknModel: elastic_annular_simple requires positive inner_wall_thickness");
  }
  if (!std::isfinite(inner_young_modulus_Pa) ||
      inner_young_modulus_Pa <= 0.0 ||
      !std::isfinite(formation_young_modulus_Pa) ||
      formation_young_modulus_Pa <= 0.0) {
    throw std::invalid_argument(
        "PknModel: elastic_annular_simple requires positive Young moduli");
  }
  if (!std::isfinite(inner_poisson_ratio) || inner_poisson_ratio < 0.0 ||
      inner_poisson_ratio >= 0.5 || !std::isfinite(formation_poisson_ratio) ||
      formation_poisson_ratio < 0.0 || formation_poisson_ratio >= 0.5) {
    throw std::invalid_argument(
        "PknModel: elastic_annular_simple requires Poisson ratios in [0, 0.5)");
  }

  const double inner_radial_compliance_m_per_Pa =
      (inner_radius_m * inner_radius_m) /
      (inner_young_modulus_Pa * inner_wall_thickness_m);
  const double formation_radial_compliance_m_per_Pa =
      ((1.0 + formation_poisson_ratio) * outer_radius_m) /
      formation_young_modulus_Pa;
  const double annular_area_factor =
      outer_radius_m * outer_radius_m - inner_radius_m * inner_radius_m;
  const double geometric_compressibility =
      2.0 *
      (inner_radius_m * inner_radial_compliance_m_per_Pa +
       outer_radius_m * formation_radial_compliance_m_per_Pa) /
      annular_area_factor;
  if (!std::isfinite(geometric_compressibility) ||
      geometric_compressibility < 0.0) {
    throw std::invalid_argument(
        "PknModel: elastic_annular_simple produced invalid compliance");
  }
  return geometric_compressibility;
}

double volumetricPressureIncrement(double dV_effective, double annular_volume,
                                   double effective_compressibility) {
  if (!std::isfinite(dV_effective)) {
    throw std::invalid_argument("PknModel: dV_effective must be finite");
  }
  if (!std::isfinite(annular_volume) || annular_volume <= 0.0) {
    throw std::invalid_argument(
        "PknModel: annular_volume must be finite and positive");
  }
  if (!std::isfinite(effective_compressibility) ||
      effective_compressibility <= 0.0) {
    throw std::invalid_argument(
        "PknModel: effective_compressibility must be finite and positive");
  }
  return dV_effective / (effective_compressibility * annular_volume);
}

PknResult PknModel::evaluate(const PknInput& input, double elapsed_time_s) const {
  if (elapsed_time_s < 0.0) {
    throw std::invalid_argument("PknModel: elapsed_time_s must be non-negative");
  }
  validate_input(input);
  PknResult point = make_point(input, elapsed_time_s);
  const bool uses_volumetric_compliance =
      input.pressure_model == PknPressureModel::VolumetricBalance &&
      input.volumetric_compliance.enabled;
  double geometric_compressibility_per_Pa = 0.0;
  std::string mechanical_compliance_status = "none";
  if (uses_volumetric_compliance) {
    if (input.volumetric_compliance.model == "elastic_annular_simple") {
      geometric_compressibility_per_Pa = elasticAnnularGeometricCompressibility(
          input.volumetric_compliance.inner_radius_m,
          input.volumetric_compliance.outer_radius_m,
          input.volumetric_compliance.inner_wall_thickness_m,
          input.volumetric_compliance.inner_young_modulus_Pa,
          input.volumetric_compliance.inner_poisson_ratio,
          input.volumetric_compliance.formation_young_modulus_Pa,
          input.volumetric_compliance.formation_poisson_ratio);
      mechanical_compliance_status = "computed_elastic_annular_simple";
    } else {
      geometric_compressibility_per_Pa =
          input.volumetric_compliance.geometric_compressibility_per_Pa;
      mechanical_compliance_status = "constant_geometric_input";
    }
  }
  point.pressure_model = pressure_model_label(input.pressure_model);
  point.sink_timing = sink_timing_label(input.sink_timing);
  point.fluid_compressibility_per_Pa = input.fluid_compressibility_per_Pa;
  point.geometric_compressibility_per_Pa = geometric_compressibility_per_Pa;
  point.effective_compressibility_per_Pa =
      input.pressure_model == PknPressureModel::VolumetricBalance
          ? effectiveCompressibility(input.fluid_compressibility_per_Pa,
                                     point.geometric_compressibility_per_Pa)
          : 0.0;
  point.compliance_model =
      uses_volumetric_compliance ? input.volumetric_compliance.model : "none";
  point.compliance_source =
      uses_volumetric_compliance ? input.volumetric_compliance.source : "";
  point.mechanical_compliance_status = mechanical_compliance_status;
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
