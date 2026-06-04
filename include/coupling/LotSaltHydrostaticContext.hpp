#pragma once

#include <cstddef>
#include <string>

#include "core/types.hpp"

namespace lss::coupling {

struct LotSaltHydrostaticContext {
  double depth_m = 0.0;
  double density_kg_m3 = 0.0;
  double hydrostatic_pressure_Pa = 0.0;

  std::size_t annular_index = 0;
  std::string fluid_id;
  std::string source;
};

[[nodiscard]] LotSaltHydrostaticContext make_lot_salt_hydrostatic_context(
    const lss::core::CaseData& data);

}  // namespace lss::coupling
