#include "lot/PknRunner.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

#include "lot/PknModel.hpp"
#include "wellbore/AnnularVolume.hpp"

namespace lss::lot {
namespace {

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

void attach_initial_annular_volume(const lss::core::CaseData& data,
                                   PknResult& result) {
  const auto& layer = layer_at_shoe(data);
  const auto* casing = casing_for_annular_outer_radius(data);
  if (casing == nullptr) {
    result.annular_volume_convention = "NOT_AVAILABLE";
    result.annular_volume_source = "no casing available for annular volume";
    return;
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

  result.annular_outer_radius_m = outer_radius_m;
  result.annular_inner_radius_m = inner_radius_m;
  result.annular_length_m = length_m;
  result.initial_annular_volume_per_radian_m3 =
      lss::wellbore::annular_volume_per_radian_m3(outer_radius_m,
                                                  inner_radius_m, length_m);
  result.initial_annular_volume_m3 = lss::wellbore::annular_total_volume_m3(
      outer_radius_m, inner_radius_m, length_m);
  result.annular_volume_convention = "PER_RADIAN_INTERNAL_TOTAL_EXPORTED";
  result.annular_volume_source = source;
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
  return input;
}

PknRun run_pkn_case(const lss::core::CaseData& data) {
  PknRun run;
  run.input = make_pkn_input(data);
  run.result = PknModel{}.simulate(run.input);
  attach_initial_annular_volume(data, run.result);
  return run;
}

}  // namespace lss::lot
