#include "lot/PknRunner.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

#include "lot/PknModel.hpp"

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
  if (model == "carter") {
    throw std::runtime_error("PknRunner: carter leakoff is not implemented in Fase 6.5");
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
  input.breakdown.method = parse_breakdown_method(data.lot.breakdown_method);
  input.breakdown.pressure_Pa = data.lot.breakdown_pressure_Pa;
  input.fracture_height_m = data.lot.fracture_height_m;
  input.initial_width_m = data.lot.fracture_initial_width_m;
  input.net_pressure_Pa = data.lot.breakdown_pressure_Pa;
  input.plane_strain_modulus_Pa = plane_strain_modulus(rock);
  input.fluid_viscosity_Pa_s = data.lot.fracture_fluid_viscosity_Pa_s;
  input.leakoff_coefficient_m_sqrt_s = data.lot.leakoff_coefficient_m_sqrt_s;
  return input;
}

PknRun run_pkn_case(const lss::core::CaseData& data) {
  PknRun run;
  run.input = make_pkn_input(data);
  run.result = PknModel{}.simulate(run.input);
  return run;
}

}  // namespace lss::lot
