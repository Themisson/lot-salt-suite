#include "coupling/LotSaltHydrostaticContext.hpp"

#include <cmath>
#include <cstddef>
#include <stdexcept>

#include "units/units.hpp"

namespace lss::coupling {
namespace {

const lss::core::FluidData& fluid_by_id(const lss::core::CaseData& data,
                                        const std::string& fluid_id) {
  for (const auto& fluid : data.fluids) {
    if (fluid.id == fluid_id) {
      return fluid;
    }
  }
  throw std::invalid_argument(
      "LotSaltHydrostaticContext: annular fluid_id not found in CaseData");
}

}  // namespace

LotSaltHydrostaticContext make_lot_salt_hydrostatic_context(
    const lss::core::CaseData& data) {
  const double shoe_depth_m = data.lot.shoe_depth_m;
  if (!std::isfinite(shoe_depth_m) || shoe_depth_m <= 0.0) {
    throw std::invalid_argument(
        "LotSaltHydrostaticContext: lot.shoe_depth_m must be finite and "
        "positive");
  }

  bool found_annular = false;
  std::size_t selected_annular_index = 0;
  for (std::size_t index = 0; index < data.annulars.size(); ++index) {
    const auto& annular = data.annulars[index];
    if (annular.top_m <= shoe_depth_m && shoe_depth_m <= annular.base_m) {
      if (found_annular) {
        throw std::invalid_argument(
            "LotSaltHydrostaticContext: multiple annulars contain "
            "lot.shoe_depth_m");
      }
      found_annular = true;
      selected_annular_index = index;
    }
  }

  if (!found_annular) {
    throw std::invalid_argument(
        "LotSaltHydrostaticContext: no annular contains lot.shoe_depth_m");
  }

  const auto& selected_annular = data.annulars[selected_annular_index];
  const auto& fluid = fluid_by_id(data, selected_annular.fluid_id);

  LotSaltHydrostaticContext context;
  context.depth_m = shoe_depth_m;
  context.density_kg_m3 = fluid.density_kg_m3;
  context.hydrostatic_pressure_Pa =
      units::hydrostatic_pressure_Pa(fluid.density_kg_m3, shoe_depth_m);
  context.annular_index = selected_annular_index;
  context.fluid_id = fluid.id;
  context.source =
      "lot.shoe_depth_m + annular.fluid_id + fluid.density_kg_m3";
  return context;
}

}  // namespace lss::coupling
