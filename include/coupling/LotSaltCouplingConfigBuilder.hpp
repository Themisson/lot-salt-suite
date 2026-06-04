#pragma once

#include "core/types.hpp"
#include "coupling/LotSaltCouplingStep.hpp"
#include "coupling/LotSaltHydrostaticContext.hpp"
#include "coupling/LotSaltPressureMap.hpp"

namespace lss::coupling {

struct LotSaltCouplingConfigOptions {
  double radial_position_m = 0.1556;
  double temperature_K = 350.0;
  double surface_pressure_Pa = 0.0;

  LotSaltPressureMapMethod method =
      LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
};

[[nodiscard]] LotSaltCouplingConfig
make_lot_salt_coupling_config_from_hydrostatic_context(
    const LotSaltHydrostaticContext& context,
    const LotSaltCouplingConfigOptions& options = {});

[[nodiscard]] LotSaltCouplingConfig make_hydrostatic_lot_salt_coupling_config(
    const lss::core::CaseData& data,
    const LotSaltCouplingConfigOptions& options = {});

}  // namespace lss::coupling
