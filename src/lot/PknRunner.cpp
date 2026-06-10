#include "lot/PknRunner.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

#include "lot/PknModel.hpp"
#include "wellbore/AnnularVolume.hpp"

namespace lss::lot {
namespace {

struct AnnularVolumeContext {
  bool available = false;
  double per_radian_m3 = 0.0;
  double total_m3 = 0.0;
  double outer_radius_m = 0.0;
  double inner_radius_m = 0.0;
  double length_m = 0.0;
  std::string convention = "NOT_AVAILABLE";
  std::string source = "no casing available for annular volume";
};

const lss::core::LayerData& layer_at_shoe(const lss::core::CaseData& data) {
  for (const auto& layer : data.layers) {
    if (data.lot.shoe_depth_m >= layer.top_m && data.lot.shoe_depth_m <= layer.base_m) {
      return layer;
    }
  }
  throw std::runtime_error("PknRunner: no layer contains lot.shoe_depth_m");
}

const lss::core::CasingData* casing_for_annular_outer_radius(
    const lss::core::CaseData& data) {
  const lss::core::CasingData* candidate = nullptr;
  for (const auto& casing : data.casings) {
    if (data.lot.shoe_depth_m >= casing.top_m &&
        data.lot.shoe_depth_m <= casing.base_m) {
      if (candidate == nullptr || casing.di_m < candidate->di_m) {
        candidate = &casing;
      }
    }
  }
  if (candidate != nullptr) {
    return candidate;
  }

  for (const auto& casing : data.casings) {
    if (casing.base_m <= data.lot.shoe_depth_m &&
        (candidate == nullptr || casing.base_m > candidate->base_m)) {
      candidate = &casing;
    }
  }
  return candidate;
}

const lss::core::RockData& rock_by_id(const lss::core::CaseData& data,
                                      const std::string& id) {
  for (const auto& rock : data.rocks) {
    if (rock.id == id) {
      return rock;
    }
  }
  throw std::runtime_error("PknRunner: layer rock_id not found in rocks");
}

const lss::core::FluidData& fluid_by_id(const lss::core::CaseData& data,
                                        const std::string& id) {
  for (const auto& fluid : data.fluids) {
    if (fluid.id == id) {
      return fluid;
    }
  }
  throw std::runtime_error("PknRunner: annular fluid_id not found in fluids");
}

const lss::core::AnnularData& annular_at_shoe(const lss::core::CaseData& data) {
  const lss::core::AnnularData* match = nullptr;
  for (const auto& annular : data.annulars) {
    if (data.lot.shoe_depth_m >= annular.top_m &&
        data.lot.shoe_depth_m <= annular.base_m) {
      if (match != nullptr) {
        throw std::runtime_error("PknRunner: more than one annular contains lot.shoe_depth_m");
      }
      match = &annular;
    }
  }
  if (match == nullptr) {
    throw std::runtime_error("PknRunner: no annular contains lot.shoe_depth_m");
  }
  return *match;
}

LeakoffModel parse_leakoff_model(const std::string& model) {
  if (model.empty() || model == "none") {
    return LeakoffModel::None;
  }
  if (model == "synthetic_constant") {
    return LeakoffModel::SyntheticConstant;
  }
  if (model == "constant_rate") {
    return LeakoffModel::ConstantRate;
  }
  if (model == "carter") {
    return LeakoffModel::Carter;
  }
  throw std::runtime_error("PknRunner: unsupported leakoff model: " + model);
}

BreakdownMethod parse_breakdown_method(const std::string& method) {
  if (method.empty() || method == "pressure_threshold") {
    return BreakdownMethod::PressureThreshold;
  }
  if (method == "derivative_drop") {
    return BreakdownMethod::DerivativeDrop;
  }
  throw std::runtime_error("PknRunner: unsupported breakdown method: " + method);
}

PknPressureModel parse_pressure_model(const std::string& model) {
  if (model.empty() || model == "pkn_direct") {
    return PknPressureModel::PknDirect;
  }
  if (model == "volumetric_balance") {
    return PknPressureModel::VolumetricBalance;
  }
  throw std::runtime_error("PknRunner: unsupported pressure model: " + model);
}

FractureInitiationCriterion parse_fracture_initiation(
    const lss::core::SigmaThetaFractureCriterionData& criterion) {
  if (!criterion.enabled) {
    return FractureInitiationCriterion::ConstantPressure;
  }
  if (criterion.type == "sigma_theta_static") {
    return FractureInitiationCriterion::SigmaThetaStatic;
  }
  throw std::runtime_error("PknRunner: unsupported fracture initiation type: " +
                           criterion.type);
}

double plane_strain_modulus(const lss::core::RockData& rock) {
  const double denominator = 1.0 - rock.nu * rock.nu;
  if (rock.E_Pa <= 0.0 || denominator <= 0.0 || !std::isfinite(denominator)) {
    throw std::runtime_error("PknRunner: invalid rock elastic properties");
  }
  return rock.E_Pa / denominator;
}

void validate_pkn_contract(const lss::core::CaseData& data) {
  if (data.mode != "lot-pkn") {
    throw std::runtime_error("PknRunner: case mode must be lot-pkn");
  }
  if (!data.lot.enabled || data.lot.model != "pkn" ||
      data.lot.fracture_geometry != "pkn") {
    throw std::runtime_error("PknRunner: LOT PKN model/geometry must be enabled");
  }
}

AnnularVolumeContext make_annular_volume_context(const lss::core::CaseData& data) {
  AnnularVolumeContext context;
  const auto& layer = layer_at_shoe(data);
  const auto* casing = casing_for_annular_outer_radius(data);
  if (casing == nullptr) {
    return context;
  }

  const double length_m = layer.base_m - layer.top_m;
  const double outer_radius_m = 0.5 * casing->di_m;
  double inner_radius_m = 0.0;
  std::string source = "layer_at_shoe + casing.di_m";

  if (data.wellbore.drill_pipe.present &&
      data.wellbore.drill_pipe.depth_m >= data.lot.shoe_depth_m) {
    inner_radius_m = 0.5 * data.wellbore.drill_pipe.outer_diameter_m;
    source += " + wellbore.drill_pipe.outer_diameter";
  }

  context.available = true;
  context.outer_radius_m = outer_radius_m;
  context.inner_radius_m = inner_radius_m;
  context.length_m = length_m;
  context.per_radian_m3 =
      lss::wellbore::annular_volume_per_radian_m3(outer_radius_m,
                                                  inner_radius_m, length_m);
  context.total_m3 =
      lss::wellbore::annular_total_volume_m3(outer_radius_m, inner_radius_m, length_m);
  context.convention = "PER_RADIAN_INTERNAL_TOTAL_EXPORTED";
  context.source = source;
  return context;
}

void attach_initial_annular_volume(const AnnularVolumeContext& context,
                                   PknResult& result) {
  result.annular_outer_radius_m = context.outer_radius_m;
  result.annular_inner_radius_m = context.inner_radius_m;
  result.annular_length_m = context.length_m;
  result.initial_annular_volume_per_radian_m3 = context.per_radian_m3;
  result.initial_annular_volume_m3 = context.total_m3;
  result.annular_volume_convention = context.convention;
  result.annular_volume_source = context.source;
}

}  // namespace

PknInput make_pkn_input(const lss::core::CaseData& data) {
  validate_pkn_contract(data);

  const auto& layer = layer_at_shoe(data);
  const auto& rock = rock_by_id(data, layer.rock_id);

  PknInput input;
  input.injection.rate_m3_s = data.lot.injection_rate_m3_s;
  input.injection.total_time_s = data.lot.injection_total_time_s;
  input.injection.dt_s = data.lot.injection_dt_s;
  input.injection.accommodation_time_s = data.lot.injection_accommodation_time_s;
  for (const auto& phase : data.lot.injection_phases) {
    input.injection.phases.push_back({phase.name, phase.duration_s, phase.rate_m3_s});
  }
  input.leakoff.enabled = data.lot.leakoff_enabled;
  input.leakoff.model = parse_leakoff_model(data.lot.leakoff_model);
  input.leakoff.coefficient_m_sqrt_s = data.lot.leakoff_coefficient_m_sqrt_s;
  input.leakoff.constant_rate_m3_s = data.lot.leakoff_constant_rate_m3_s;
  input.breakdown.method = parse_breakdown_method(data.lot.breakdown_method);
  input.breakdown.pressure_Pa = data.lot.breakdown_pressure_Pa;
  input.fracture_height_m = data.lot.fracture_height_m;
  input.initial_width_m = data.lot.fracture_initial_width_m;
  input.net_pressure_Pa = data.lot.breakdown_pressure_Pa;
  input.plane_strain_modulus_Pa = plane_strain_modulus(rock);
  input.fluid_viscosity_Pa_s = data.lot.fracture_fluid_viscosity_Pa_s;
  input.leakoff_coefficient_m_sqrt_s = data.lot.leakoff_coefficient_m_sqrt_s;
  input.leakoff_constant_rate_m3_s = data.lot.leakoff_constant_rate_m3_s;
  input.pressure_model = parse_pressure_model(data.lot.pressure_model);
  input.initial_pressure_Pa = data.lot.initial_pressure_Pa;
  input.volumetric_compliance.enabled =
      data.lot.volumetric_compliance.enabled;
  input.volumetric_compliance.model = data.lot.volumetric_compliance.model;
  input.volumetric_compliance.geometric_compressibility_per_Pa =
      data.lot.volumetric_compliance.geometric_compressibility_per_Pa;
  input.volumetric_compliance.total_compressibility_per_Pa =
      data.lot.volumetric_compliance.total_compressibility_per_Pa;
  input.volumetric_compliance.inner_radius_m =
      data.lot.volumetric_compliance.inner_radius_m;
  input.volumetric_compliance.outer_radius_m =
      data.lot.volumetric_compliance.outer_radius_m;
  input.volumetric_compliance.inner_wall_thickness_m =
      data.lot.volumetric_compliance.inner_wall_thickness_m;
  input.volumetric_compliance.inner_young_modulus_Pa =
      data.lot.volumetric_compliance.inner_young_modulus_Pa;
  input.volumetric_compliance.inner_poisson_ratio =
      data.lot.volumetric_compliance.inner_poisson_ratio;
  input.volumetric_compliance.formation_young_modulus_Pa =
      data.lot.volumetric_compliance.formation_young_modulus_Pa;
  input.volumetric_compliance.formation_poisson_ratio =
      data.lot.volumetric_compliance.formation_poisson_ratio;
  input.volumetric_compliance.mechanical_compliance_status =
      data.lot.volumetric_compliance.mechanical_compliance_status;
  input.volumetric_compliance.source = data.lot.volumetric_compliance.source;
  input.volumetric_compliance.caveat = data.lot.volumetric_compliance.caveat;
  input.fracture_initiation =
      parse_fracture_initiation(data.lot.sigma_theta_fracture);
  input.sigma_theta_fracture.enabled = data.lot.sigma_theta_fracture.enabled;
  input.sigma_theta_fracture.layer_id = data.lot.sigma_theta_fracture.layer_id;
  input.sigma_theta_fracture.influence_depth_m =
      data.lot.sigma_theta_fracture.influence_depth_m;
  input.sigma_theta_fracture.sigma_theta_compression_positive_Pa =
      data.lot.sigma_theta_fracture.sigma_theta_compression_positive_Pa;
  input.sigma_theta_fracture.source = data.lot.sigma_theta_fracture.source;
  input.sigma_theta_fracture.pressure_source =
      data.lot.sigma_theta_fracture.pressure_source;
  input.sigma_theta_fracture.comparison =
      data.lot.sigma_theta_fracture.comparison;
  input.sigma_theta_fracture.mapping_status =
      data.lot.sigma_theta_fracture.mapping_status;
  if (input.pressure_model == PknPressureModel::VolumetricBalance) {
    const auto annular_context = make_annular_volume_context(data);
    if (!annular_context.available || annular_context.total_m3 <= 0.0) {
      throw std::runtime_error(
          "PknRunner: volumetric_balance requires available annular volume");
    }
    const auto& fluid = fluid_by_id(data, annular_at_shoe(data).fluid_id);
    if (fluid.compressibility_per_Pa <= 0.0 ||
        !std::isfinite(fluid.compressibility_per_Pa)) {
      throw std::runtime_error(
          "PknRunner: volumetric_balance requires positive fluid compressibility");
    }
    input.annular_volume_m3 = annular_context.total_m3;
    input.fluid_compressibility_per_Pa = fluid.compressibility_per_Pa;
  }
  return input;
}

PknRun run_pkn_case(const lss::core::CaseData& data) {
  PknRun run;
  run.input = make_pkn_input(data);
  run.result = PknModel{}.simulate(run.input);
  attach_initial_annular_volume(make_annular_volume_context(data), run.result);
  return run;
}

}  // namespace lss::lot
